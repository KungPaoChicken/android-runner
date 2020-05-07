import csv
import errno
import json
import os
import os.path as op
import subprocess
import time
from collections import OrderedDict

from . import BatterystatsParser
from AndroidRunner.BrowserFactory import BrowserFactory
from .Profiler import Profiler
from functools import reduce
from AndroidRunner import Tests
from AndroidRunner import util

class Batterystats(Profiler):

    def __init__(self, config, paths):
        super(Batterystats, self).__init__(config, paths)
        self.output_dir = ''
        self.paths = paths
        self.profile = False
        self.cleanup = config.get('cleanup')
        self.enable_systrace_parsing = config.get('enable_systrace_parsing', True)
        self.python2_path = config.get('python2_path', 'python2')

        # "config" only passes the fields under "profilers", so config.json is loaded again for the fields below
        # FIX
        config_f = util.load_json(op.join(self.paths["CONFIG_DIR"], self.paths['ORIGINAL_CONFIG_DIR']))
        self.type = config_f['type']
        self.systrace = config_f.get('systrace_path', 'systrace')
        self.powerprofile = config_f['powerprofile_path']
        self.duration = Tests.is_integer(config_f.get('duration', 0)) / 1000
        if self.type == 'web':
            self.browsers = [BrowserFactory.get_browser(b)(config_f) for b in config_f.get('browsers', ['chrome'])]

        if os.path.exists(self.systrace): # If it does not exist, then there might be a prefix already added to the path
            self.systrace  = ' '.join([self.python2_path, self.systrace])
        else:
            print("Did not prefix python2 path to systrace path due to the systrace path not existing. " + \
                  "This is fine if you added a prefix path yourself, if not, double check the systrace_path inside of your config and make sure it exists.")

    # noinspection PyGlobalUndefined
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
            app = self.browsers[0].to_string()

        # Create files on system
        systrace_file = op.join(self.output_dir,
                                'systrace_{}_{}.html'.format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))
        logcat_file = op.join(self.output_dir, 'logcat_{}_{}.txt'.format(device.id, time.strftime('%Y.%m.%d_%H%M%S')))
        batterystats_file = op.join(self.output_dir, 'batterystats_history_{}_{}.txt'.format(device.id, time.strftime(
            '%Y.%m.%d_%H%M%S')))
        print(batterystats_file)
        results_file_name = 'results_{}_{}.csv'.format(device.id, time.strftime('%Y.%m.%d_%H%M%S'))
        results_file = op.join(self.output_dir, results_file_name)

        self.profile = True
        self.get_data(device, app)

    # noinspection PyGlobalUndefined
    def get_data(self, device, application):
        """Runs the systrace method for self.duration seconds in a separate thread"""
        # TODO: Check if 'systrace freq idle' is supported by the device
        global sysproc

        sysproc = subprocess.Popen(
            '{} freq idle -e {} -a {} -t {} -o {}'.format(self.systrace, device.id, application, int(self.duration + 5),
                                                          systrace_file), shell=True)

    # FIX

    def stop_profiling(self, device, **kwargs):
        self.profile = False

    # Pull logcat file from device
    @staticmethod
    def pull_logcat(device):
        device.shell('logcat -f /mnt/sdcard/logcat.txt -d')
        device.pull('/mnt/sdcard/logcat.txt', logcat_file)
        device.shell('rm -f /mnt/sdcard/logcat.txt')

    # Get BatteryStats data
    def get_batterystats_results(self, device):
        with open(batterystats_file, 'w+') as f:
            f.write(device.shell('dumpsys batterystats --history'))
        batterystats_results = BatterystatsParser.parse_batterystats(app, batterystats_file, self.powerprofile)
        return batterystats_results

    # Estimate total consumption, charge is given in mAh, volt in mV
    @staticmethod
    def get_consumed_joules(device):
        charge = device.shell('dumpsys batterystats | grep "Computed drain:"').split(',')[1].split(':')[1]
        volt = device.shell('dumpsys batterystats | grep "volt="').split('volt=')[1].split()[0]
        energy_consumed_wh = float(charge) * float(volt) / 1000000.0
        energy_consumed_j = energy_consumed_wh * 3600.0
        return energy_consumed_j

    def get_systrace_results(self, device):
        # Wait for Systrace file finalisation before parsing
        sysproc.wait()
        cores = int(device.shell('cat /proc/cpuinfo | grep processor | wc -l'))

        systrace_results = []
        if self.enable_systrace_parsing: 
            systrace_results = BatterystatsParser.parse_systrace(app, systrace_file, logcat_file, batterystats_file,
                                                                self.powerprofile,
                                                                cores)
        return systrace_results

    def write_results(self, batterystats_results, systrace_results, energy_consumed_j):
        with open(results_file, 'w+') as results:
            writer = csv.writer(results, delimiter="\n")
            writer.writerow(
                ['Start Time (Seconds),End Time (Seconds),Duration (Seconds),Component,Energy Consumption (Joule)'])
            writer.writerow(batterystats_results)
            writer.writerow(systrace_results)
        # FIX
        with open(op.join(self.output_dir, 'Joule_{}'.format(results_file_name)), 'w+') as out:
            out.write('Joule_calculated\n{}\n'.format(energy_consumed_j))

    def cleanup_logs(self):
        if self.cleanup is True:
            # Remove log files
            os.remove(systrace_file)
            os.remove(logcat_file)
            os.remove(batterystats_file)

    def collect_results(self, device, path=None):
        self.pull_logcat(device)
        batterystats_results = self.get_batterystats_results(device)
        energy_consumed_j = self.get_consumed_joules(device)
        systrace_results = self.get_systrace_results(device)

        self.write_results(batterystats_results, systrace_results, energy_consumed_j)
        self.cleanup_logs()

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

        util.write_to_file(filename, subject_rows)

    def aggregate_end(self, data_dir, output_file):
        # FIX
        rows = self.aggregate_final(data_dir)

        util.write_to_file(output_file, rows)

    @staticmethod
    def aggregate_battery_subject(logs_dir, joules):
        def add_row(accum, new):
            row = {k: v + float(new[k]) for k, v in list(accum.items()) if k not in ['Component', 'count']}
            count = accum['count'] + 1
            return dict(row, **{'count': count})

        # FIX
        runs = []
        runs_total = dict()
        for run_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
            if ('Joule' in run_file) and joules:
                with open(os.path.join(logs_dir, run_file), 'r', encoding='utf-8') as run:
                    reader = csv.DictReader(run)
                    init = dict({fn: 0 for fn in reader.fieldnames if fn != 'datetime'}, **{'count': 0})
                    run_total = reduce(add_row, reader, init)
                    runs.append({k: v / run_total['count'] for k, v in list(run_total.items()) if k != 'count'})
                runs_total = reduce(lambda x, y: {k: v + y[k] for k, v in list(x.items())}, runs)
        return OrderedDict(
            sorted(list({'batterystats_' + k: v / len(runs) for k, v in list(runs_total.items())}.items()), key=lambda x: x[0]))

    def aggregate_final(self, data_dir):
        rows = []
        for device in util.list_subdir(data_dir):
            row = OrderedDict({'device': device})
            device_dir = os.path.join(data_dir, device)
            for subject in util.list_subdir(device_dir):
                row.update({'subject': subject})
                subject_dir = os.path.join(device_dir, subject)
                if os.path.isdir(os.path.join(subject_dir, 'batterystats')):
                    row.update(self.aggregate_battery_final(os.path.join(subject_dir, 'batterystats')))
                    rows.append(row.copy())
                else:
                    for browser in util.list_subdir(subject_dir):
                        row.update({'browser': browser})
                        browser_dir = os.path.join(subject_dir, browser)
                        if os.path.isdir(os.path.join(browser_dir, 'batterystats')):
                            row.update(self.aggregate_battery_final(os.path.join(browser_dir, 'batterystats')))
                            rows.append(row.copy())
        return rows

    @staticmethod
    def aggregate_battery_final(logs_dir):
        for aggregated_file in [f for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f))]:
            if aggregated_file == "Aggregated.csv":
                with open(os.path.join(logs_dir, aggregated_file), 'r', encoding='utf-8') as aggregated:
                    reader = csv.DictReader(aggregated)
                    row_dict = OrderedDict()
                    for row in reader:
                        for f in reader.fieldnames:
                            row_dict.update({f: row[f]})
                    return OrderedDict(row_dict)
