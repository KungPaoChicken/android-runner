import os.path as op
import os
import time
import csv
import json
import errno
import BatterystatsParser

from collections import OrderedDict
from subprocess import Popen
from Profiler import Profiler


class Batterystats(Profiler):

    def __init__(self, config, paths):
        super(Batterystats, self).__init__(config, paths)
        self.output_dir = ''
        self.paths = paths
        self.profile = False
        self.cleanup = config.get('cleanup')

        # "config" only passes the fields under "profilers", so config.json is loaded again for the fields below
	#FIX
        config_file = self.load_json(op.join(self.paths["CONFIG_DIR"], paths['ORIGINAL_CONFIG_DIR']))
        self.type = config_file['type']
        self.systrace = config_file.get('systrace_path', 'systrace')
        self.powerprofile = config_file['powerprofile_path']
        self.duration = self.is_integer(config_file.get('duration', 0)) / 1000

    def start_profiling(self, device, **kwargs):
        # Reset logs on the device
        device.shell('dumpsys batterystats --reset')
        print('Batterystats cleared')

        # Create output directories
        global app
        global systrace_file
        global logcat_file
        global batterystats_file
        global results_file
        global results_file_name

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
        print(batterystats_file)
        results_file_name = 'results_{}_{}.csv'.format(device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        results_file = op.join(self.output_dir, results_file_name)

        self.profile = True
        self.get_data(device, app)

    def get_data(self, device, app):
        """Runs the systrace method for self.duration seconds in a separate thread"""
        # TODO: Check if 'systrace freq idle' is supported by the device
        global sysproc
        sysproc = Popen('{} freq idle -e {} -a {} -t {} -o {}'.format(self.systrace, device.id, app, int(self.duration + 5), systrace_file), shell=True)
#FIX
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
        batterystats_results = BatterystatsParser.parse_batterystats(app, batterystats_file, self.powerprofile)

        # Estimate total consumption
        # charge is given in mAh
        charge = device.shell('dumpsys batterystats | grep "Computed drain:"').split(',')[1].split(':')[1]
        volt = device.shell('dumpsys batterystats | grep "volt="').split('volt=')[1].split()[0]
        energy_consumed_Wh = float(charge) * float(volt) / 1000000.0
        energy_consumed_J = energy_consumed_Wh * 3600.0

        # Wait for Systrace file finalisation before parsing
        sysproc.wait()
        cores = int(device.shell('cat /proc/cpuinfo | grep processor | wc -l'))
        systrace_results = BatterystatsParser.parse_systrace(app, systrace_file, logcat_file, batterystats_file, self.powerprofile,
                                                 cores)

        with open(results_file, 'w+') as results:
            writer = csv.writer(results, delimiter="\n")
            writer.writerow(
                ['Start Time (Seconds),End Time (Seconds),Duration (Seconds),Component,Energy Consumption (Joule)'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
	#FIX
        with open(op.join(self.output_dir, 'Joule_{}'.format(results_file_name)),'w+') as out:
            out.write('Joule calculated\n{}\n'.format(energy_consumed_J))

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

    def aggregate_subject(self):
        filename = os.path.join(self.output_dir, 'Aggregated.csv')
        current_row = self.aggregate_battery_subject(self.output_dir, False)
        current_row.update(self.aggregate_battery_subject(self.output_dir, True))
        subject_rows = list()
        subject_rows.append(current_row)
        self.write_to_file(filename, subject_rows)

    def aggregate_end(self, data_dir, output_file):
	#FIX
        rows = self.aggregate_final(data_dir)
        self.write_to_file(output_file, rows)

    def write_to_file(self, filename, rows):
        with open(filename, 'w') as f:
            writer = csv.DictWriter(f, rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def aggregate_battery_subject(self, logs_dir, joules):
        def add_row(accum, new):
            row = {k: v + float(new[k]) for k, v in accum.items() if k not in ['Component', 'count']}
            count = accum['count'] + 1
            return dict(row, **{'count': count})
#FIX
        runs = []
	runs_total = dict()
        for run_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
            if ('Joule' in run_file) and joules:
                with open(os.path.join(logs_dir, run_file), 'rb') as run:
                    reader = csv.DictReader(run)
                    init = dict({fn: 0 for fn in reader.fieldnames if fn != 'datetime'}, **{'count': 0})
                    run_total = reduce(add_row, reader, init)
                    runs.append({k: v / run_total['count'] for k, v in run_total.items() if k != 'count'})
        	runs_total = reduce(lambda x, y: {k: v + y[k] for k, v in x.items()},runs)
        return OrderedDict(
            sorted({'batterystats_' + k: v / len(runs) for k, v in runs_total.items()}.items(), key=lambda x: x[0]))

    def aggregate_final(self, data_dir):
        rows = []
        for device in self.list_subdir(data_dir):
            row = OrderedDict({'device': device})
            device_dir = os.path.join(data_dir, device)
            for subject in self.list_subdir(device_dir):
                row.update({'subject': subject})
                subject_dir = os.path.join(device_dir, subject)
                if os.path.isdir(os.path.join(subject_dir, 'batterystats')):
                    row.update(self.aggregate_battery_final(os.path.join(subject_dir, 'batterystats')))
                    rows.append(row.copy())
                else:
                    for browser in self.list_subdir(subject_dir):
                        row.update({'browser': browser})
                        browser_dir = os.path.join(subject_dir, browser)
                        if os.path.isdir(os.path.join(browser_dir, 'batterystats')):
                            row.update(self.aggregate_battery_final(os.path.join(browser_dir, 'batterystats')))
                            rows.append(row.copy())
        return rows

    def aggregate_battery_final(self, logs_dir):
        for aggregated_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
            if aggregated_file == "Aggregated.csv":
                with open(os.path.join(logs_dir, aggregated_file), 'rb') as aggregated:
                    reader = csv.DictReader(aggregated)
                    row_dict = OrderedDict()
                    for row in reader:
                        for f in reader.fieldnames:
                            row_dict.update({f: row[f]})
                    return OrderedDict(row_dict)

    def list_subdir(self, a_dir):
        """List immediate subdirectories of a_dir"""
        # https://stackoverflow.com/a/800201
        return [name for name in os.listdir(a_dir)
                if os.path.isdir(os.path.join(a_dir, name))]

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
