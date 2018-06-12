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

    def start_profiling(self, device, **kwargs):
        # clear data
        device.shell('dumpsys batterystats --reset')
        device.shell('logcat -c')
        # create output directories
        global app
        global output_dir
        output_dir = op.join(paths.OUTPUT_DIR, 'android/')
        makedirs(output_dir)
        super(Batterystats, self).start_profiling(device, **kwargs)
        self.profile = True
        app = kwargs.get('app', None)
        self.get_data(device, app)

    def get_data(self, device, app):
        """Runs the profiling methods for self.interval seconds in a separate thread"""
        # start = timeit.default_timer()
        # Get Systrace data
        subprocess.Popen('{} freq idle -t {} -o {}systrace.html'.format(self.systrace, self.interval, output_dir), shell=True)
        # end = timeit.default_timer()
        # timer results could be negative

    def stop_profiling(self, device, **kwargs):
        if self.interval > 5:
            time.sleep(self.interval / 2.0)
        super(Batterystats, self).stop_profiling(device, **kwargs)
        self.profile = False
        device.shell('logcat -f /mnt/sdcard/logcat.txt -d')
        device.pull('/mnt/sdcard/logcat.txt', '{}logcat.txt'.format(output_dir))
        device.shell('rm -f /mnt/sdcard/logcat.txt')
        #device.shell('dumpsys battery reset')

    def collect_results(self, device, path=None):
        filename = op.join(output_dir, 'batterystats_results_{}_{}.csv'
                           .format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))

        # Get BatteryStats data
        batterystats_file = op.join(output_dir, 'batterystats_history.txt')
        with open(batterystats_file, 'w+') as f2:
            f2.write(device.shell('dumpsys batterystats --history'))
        batterystats_results = Parser.parse_batterystats(app, batterystats_file, self.powerprofile)

        # Get Systrace data
        systrace_file = '{}systrace.html'.format(output_dir)
        logcat_file = op.join(output_dir, 'logcat.txt')
        systrace_results = Parser.parse_systrace(app, systrace_file, logcat_file, batterystats_file, self.powerprofile)

        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter="\n")
            writer.writerow(['timeframe (duration), component, Joule'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
