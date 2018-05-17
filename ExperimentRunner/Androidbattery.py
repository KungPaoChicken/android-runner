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

class Androidbattery(Profiler):
    def __init__(self, config):
        super(Androidbattery, self).__init__(config)
        self.profile = False
        available_data_points = ['battery']
        self.interval = float(Tests.is_integer(config.get('sample_interval', 0))) / 1000
        self.data_points = config['data_points']
        invalid_data_points = [dp for dp in config['data_points'] if dp not in set(available_data_points)]
        if invalid_data_points:
            self.logger.warning('Invalid data points in config: {}'.format(invalid_data_points))
        self.data_points = [dp for dp in config['data_points'] if dp in set(available_data_points)]
        self.data = [['datetime'] + self.data_points]
        config_file = load_json(op.join(paths.CONFIG_DIR, 'config.json'))
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']

    def get_battery_usage(self, device, app):
        intensity = 5
        voltage = int(device.shell('dumpsys batterystats | grep volt | tail -1').split("volt=")[1].split()[0])
        time_frame = 1
        usage = intensity * voltage * time_frame
        return usage

    def start_profiling(self, device, **kwargs):
        print self.systrace
        #create output directories
        global output_dir
        global raw_dir
        output_dir = op.join(paths.OUTPUT_DIR, 'android/')
        makedirs(output_dir)
        raw_dir = op.join(output_dir, 'raw_data/')
        makedirs(raw_dir)
        super(Androidbattery, self).start_profiling(device, **kwargs)
        self.profile = True
        device.shell('dumpsys batterystats --reset')
        app = kwargs.get('app', None)
        self.get_data(device, app)


    def get_data(self, device, app):
        """Runs the profiling methods every self.interval seconds in a separate thread"""
        start = timeit.default_timer()

        # Get Systrace data
        subprocess.Popen('%s freq idle -t %d -o %s/systrace.html' % (self.systrace, self.interval, raw_dir), shell=True)

        device_time = device.shell('date -u')
        row = [device_time]
        row.append(self.get_battery_usage(device, app))
        self.data.append(row)
        end = timeit.default_timer()
        # timer results could be negative

    def stop_profiling(self, device, **kwargs):
        super(Androidbattery, self).stop_profiling(device, **kwargs)
        self.profile = False
        #device.shell('dumpsys battery reset')

    def collect_results(self, device, path=None):
        super(Androidbattery, self).collect_results(device)

        filename = '{}_{}.csv'.format(device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        with open(op.join(output_dir, filename), 'w+') as f:
            writer = csv.writer(f)
            for row in self.data:
                writer.writerow(row)

        # Parse Power Profile
        Parser.parse_power_profile(self.powerprofile, raw_dir)

        # Get BatteryStats data
        batterystats_file = 'batterystats_raw.txt'
        file = open(op.join(raw_dir, batterystats_file), 'w+')
        file.write(device.shell('dumpsys batterystats --history'))
        file.close()

