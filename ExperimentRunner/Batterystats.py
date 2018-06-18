import os.path as op
import os
from subprocess import Popen
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
        self.type = config_file['type']
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']
        self.cleanup = config.get('cleanup')

    def start_profiling(self, device, **kwargs):
        ## clear data (moved to before_run)
        #device.shell('dumpsys batterystats --reset')
        #print 'Batterystats cleared'
        #device.shell('logcat -c')
        #print 'Logcat cleared'

        # create output directories
        global app
        global systrace_file
        global logcat_file
        global batterystats_file
        global results_file
        output_dir = op.join(paths.OUTPUT_DIR, 'android/')
        makedirs(output_dir)
        if self.type == 'native':
            app = kwargs.get('app', None)
        elif self.type == 'web':
            app = 'com.android.chrome'

        # Create files
        systrace_file = '{}systrace_{}_{}.html'.format(output_dir, device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        logcat_file = '{}logcat_{}_{}.txt'.format(output_dir, device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        batterystats_file = op.join(output_dir, 'batterystats_history_{}_{}.txt'.format(device.id, time.strftime(
            '%Y.%m.%d_%H%M%S')))
        results_file = op.join(output_dir, 'results_{}_{}.csv'
                               .format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))

        # Run systrace
        Popen('{} freq idle -e {} -a {} -t {} -o {}'.format
              (self.systrace, device.id, app, int(self.duration + 5), systrace_file), shell=True)

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

    def collect_results(self, device, path=None):
        time.sleep(10)
        device.shell('logcat -f /mnt/sdcard/logcat.txt -d')
        device.pull('/mnt/sdcard/logcat.txt', logcat_file)
        device.shell('rm -f /mnt/sdcard/logcat.txt')

        # Get BatteryStats data
        with open(batterystats_file, 'w+') as f:
            f.write(device.shell('dumpsys batterystats --history'))
        batterystats_results = Parser.parse_batterystats(app, batterystats_file, self.powerprofile)

        # Estimate total consumption
        charge = device.shell('dumpsys batterystats | grep "Computed drain:"').split(',')[1].split(':')[1]
        volt = device.shell('dumpsys batterystats | grep "volt="').split('volt=')[1].split()[0]
        energy_consumed = (float(charge) / 1000) * (float(volt) / 1000.0) * 3600.0

        # Get Systrace data
        systrace_results = Parser.parse_systrace(app, systrace_file, logcat_file, batterystats_file, self.powerprofile)

        with open(results_file, 'w+') as results:
            writer = csv.writer(results, delimiter="\n")
            writer.writerow(['Start Time,End Time,Duration (Seconds),Component,Energy Consumption (Joule)'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
            writer.writerow([''])
            writer.writerow([',,,Estimated total consumption:,{}'.format(energy_consumed)])

        if self.cleanup == 'True':
            os.remove(systrace_file)
            os.remove(logcat_file)
            os.remove(batterystats_file)
