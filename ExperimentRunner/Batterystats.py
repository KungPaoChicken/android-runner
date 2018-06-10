import os.path as op
import subprocess
import time
from util import makedirs, load_json
import timeit
import threading
import csv

from Profiler import Profiler
import paths
import Tests
import Parser


class Batterystats(Profiler):
    def __init__(self, config):
        super(Batterystats, self).__init__(config)
        self.profile = False
        available_data_points = ['battery']
        self.interval = int(Tests.is_integer(config.get('sample_interval', 0))) / 1000
        self.data_points = config['data_points']
        invalid_data_points = [dp for dp in config['data_points'] if dp not in set(available_data_points)]
        if invalid_data_points:
            self.logger.warning('Invalid data points in config: {}'.format(invalid_data_points))
        self.data_points = [dp for dp in config['data_points'] if dp in set(available_data_points)]
        self.data = [['datetime'] + self.data_points]
        config_file = load_json(op.join(paths.CONFIG_DIR, 'config.json'))
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']
        self.app = config_file['paths']

    def get_battery_usage(self, device, app):
        cpu_intensity = 1


        intensity = 5
        voltage = int(device.shell('dumpsys batterystats | grep volt | tail -1').split("volt=")[1].split()[0])
        timeframe = 1
        usage = intensity * voltage * timeframe
        return usage

    def start_profiling(self, device, **kwargs):
        # clear data
        device.shell('dumpsys batterystats --reset')
        device.shell('logcat -c')
        # create output directories
        global app
        global output_dir
        global raw_dir
        output_dir = op.join(paths.OUTPUT_DIR, 'android/')
        makedirs(output_dir)
        # raw_dir = op.join(output_dir, 'raw_data/')
        # makedirs(raw_dir)
        super(Batterystats, self).start_profiling(device, **kwargs)
        self.profile = True
        app = kwargs.get('app', None)
        self.get_data(device, app)

    def get_data(self, device, app):
        """Runs the profiling methods every self.interval seconds in a separate thread"""
        start = timeit.default_timer()

        # Get Systrace data ## PROBLEM: if t too large, android-runner continues before output created
        subprocess.Popen('{} freq idle -t {} -o {}systrace.html'.format(self.systrace, self.interval, output_dir), shell=True)

        device_time = device.shell('date -u')
        row = [device_time]
        row.append(self.get_battery_usage(device, app))
        self.data.append(row)
        end = timeit.default_timer()
        # timer results could be negative

    def stop_profiling(self, device, **kwargs):
        super(Batterystats, self).stop_profiling(device, **kwargs)
        self.profile = False
        device.shell('logcat -f /mnt/sdcard/logcat.txt -d')
        device.pull('/mnt/sdcard/logcat.txt', '{}logcat.txt'.format(output_dir))
        device.shell('rm -f /mnt/sdcard/logcat.txt')
        #device.shell('dumpsys battery reset')

    def collect_results(self, device, path=None):
        #super(Batterystats, self).collect_results(device)

        filename = op.join(output_dir, 'batterystats_results_{}_{}.csv'
                           .format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['timeframe (duration)', 'component', 'mAh'])

            # Parse Power Profile
            # parsed_profile = Parser.parse_power_profile(self.powerprofile, raw_dir)

            # Get BatteryStats data
            batterystats_file = op.join(output_dir, 'batterystats_history.txt')
            with open(batterystats_file, 'w+') as f:
                f.write(device.shell('dumpsys batterystats --history'))
            Parser.parse_batterystats(app, batterystats_file, self.powerprofile, filename)

            # Parse Systrace
            systrace_file = '{}systrace.html'.format(output_dir)
            Parser.parse_systrace(systrace_file, self.powerprofile, filename)