import os.path as op
from subprocess import Popen, PIPE, STDOUT
import time
from util import makedirs, load_json
import csv

from Profiler import Profiler
import paths
import Tests
import Parser


class Batterystats(Profiler):
    def __init__(self, config):
        super(Batterystats, self).__init__(config)
        self.profile = False
        self.duration = int(Tests.is_integer(config.get('duration', 0))) / 1000
        config_file = load_json(op.join(paths.CONFIG_DIR, 'config.json'))
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']
        self.app = config_file['paths']

    def start_profiling(self, device, **kwargs):
        # clear data (moved to before_run)
        ## device.shell('dumpsys batterystats --reset')
        ## device.shell('logcat -c')
        ## print 'batt + logc cleared'

        # create output directories
        global app
        global output_dir
        output_dir = op.join(paths.OUTPUT_DIR, 'android/')
        makedirs(output_dir)
        app = kwargs.get('app', None)

        # Run systrace
        Popen('{} freq idle -e {} -a {} -t {} -o {}systrace.html'.format(self.systrace, device.id, app, self.duration + 5, output_dir),
                        shell=True)
        super(Batterystats, self).start_profiling(device, **kwargs)
        self.profile = True
        self.get_data(device, app)

    def get_data(self, device, app):
        """Runs the profiling methods for self.duration milliseconds in a separate thread"""
        time.sleep(self.duration)

    def stop_profiling(self, device, **kwargs):
        super(Batterystats, self).stop_profiling(device, **kwargs)
        self.profile = False
        # device.shell('dumpsys battery reset')

    def collect_results(self, device, path=None, **kwargs):
        time.sleep(10)
        device.shell('logcat -f /mnt/sdcard/logcat.txt -d')
        device.pull('/mnt/sdcard/logcat.txt', '{}logcat.txt'.format(output_dir))
        device.shell('rm -f /mnt/sdcard/logcat.txt')

        filename = op.join(output_dir, 'batterystats_results_{}_{}.csv'
                           .format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))

        # Get BatteryStats data
        batterystats_file = op.join(output_dir, 'batterystats_history.txt')
        with open(batterystats_file, 'w+') as f:
            f.write(device.shell('dumpsys batterystats --history'))
        batterystats_results = Parser.parse_batterystats(app, batterystats_file, self.powerprofile)

        # Get Systrace data
        systrace_file = '{}systrace.html'.format(output_dir)
        logcat_file = op.join(output_dir, 'logcat.txt')
        systrace_results = Parser.parse_systrace(app, systrace_file, logcat_file, batterystats_file, self.powerprofile)

        with open(filename, 'w') as results_file:
            writer = csv.writer(results_file, delimiter="\n")
            writer.writerow(['Start time,End time,Duration (seconds),Component,Energy Consumption (Joule)'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
