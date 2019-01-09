import os.path as op
import os
import time
import csv
import json
import errno
import Parser

from collections import OrderedDict
from subprocess import Popen
from Profiler import Profiler


class Batterystats(Profiler):
    def __init__(self, config, paths):
        self.output_dir = ''
        self.paths = paths
        self.profile = False
        self.cleanup = config.get('cleanup')

        # "config" only passes the fields under "profilers", so config.json is loaded again for the fields below
        config_file = self.load_json(op.join(self.paths.CONFIG_DIR, 'config.json'))
        self.type = config_file['type']
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']
        self.duration = self.is_integer(config_file.get('duration', 0)) / 1000

    def start_profiling(self, device, **kwargs):
        # Reset logs on the device
        device.shell('dumpsys batterystats --reset')
        device.shell('logcat -c')
        print('Batterystats cleared')
        print('Logcat cleared')

        # Create output directories
        global app
        global systrace_file
        global logcat_file
        global batterystats_file
        global results_file

        if self.type == 'native':
            app = kwargs.get('app', None)
        # TODO: add support for other browsers, required form: app = 'package.name'
        elif self.type == 'web':
            app = 'com.android.chrome'

        # Create files on system
        systrace_file = '{}systrace_{}_{}.html'.format(self.output_dir, device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        logcat_file = '{}logcat_{}_{}.txt'.format(self.output_dir, device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        batterystats_file = op.join(self.output_dir, 'batterystats_history_{}_{}.txt'.format(device.id, time.strftime(
            '%Y.%m.%d_%H%M%S')))
        results_file = op.join(self.output_dir, 'results_{}_{}.csv'
                               .format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))

        self.profile = True
        self.get_data(device, app)

    def get_data(self, device, app):
        """Runs the systrace method for self.duration seconds in a separate thread"""
        # TODO: Check if 'systrace freq idle' is supported by the device
        global sysproc
        sysproc = Popen('{} freq idle -e {} -a {} -t {} -b 50000 -o {}'.format
                        (self.systrace, device.id, app, int(self.duration + 5), systrace_file), shell=True)

    def stop_profiling(self, device, **kwargs):
        self.profile = False

    def collect_results(self, device, path=None):
        # Pull logcat file from device
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

        # Wait for Systrace file finalisation before parsing
        sysproc.wait()
        cores = int(device.shell('cat /proc/cpuinfo | grep processor | wc -l'))
        systrace_results = Parser.parse_systrace(app, systrace_file, logcat_file, batterystats_file, self.powerprofile,
                                                 cores)

        with open(results_file, 'w+') as results:
            writer = csv.writer(results, delimiter="\n")
            writer.writerow(
                ['Start Time (Seconds),End Time (Seconds),Duration (Seconds),Component,Energy Consumption (Joule)'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
            writer.writerow([''])
            writer.writerow(['Android Internal Estimation:,{}'.format(energy_consumed)])

        # Remove log files
        if self.cleanup is True:
            os.remove(systrace_file)
            os.remove(logcat_file)
            os.remove(batterystats_file)

    def set_output(self, output_dir):
        self.output_dir = output_dir

    def dependencies(self):
        return []

    def load(self, device):
        return

    def unload(self, device):
        return

    def is_integer(self, number, minimum=0):
        if not isinstance(number, (int, long)):
            raise ConfigError('%s is not an integer' % number)
        if number < minimum:
            raise ConfigError('%s should be equal or larger than %i' % (number, minimum))
        return number

    def load_json(self, path):
        """Load a JSON file from path, and returns an ordered dictionary or throws exceptions on formatting errors"""
        try:
            with open(path, 'r') as f:
                try:
                    return json.loads(f.read(), object_pairs_hook=OrderedDict)
                except ValueError:
                    raise FileFormatError(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                raise FileNotFoundError(path)
            else:
                raise e


class FileNotFoundError(Exception):
    def __init__(self, filename):
        Exception.__init__(self, '[Errno %s] %s: \'%s\'' % (errno.ENOENT, os.strerror(errno.ENOENT), filename))


class FileFormatError(Exception):
    pass


class ConfigError(Exception):
    pass


