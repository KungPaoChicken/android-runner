from importlib import import_module
from time import sleep
from ConfigParser import ConfigParser, ConfigError
from Devices import Devices
from Runner import Runner
from Adb import ConnectionError, AdbError
import Adb
import pprint


class Experiment:
    def __init__(self, config_file=None):
        self.type = None
        self.replications = 1
        self.devices = None
        self.measurements = {}
        self.scripts = None
        self.time_between_run = 0
        if config_file:
            try:
                config = ConfigParser(config_file).parse()
                # pprint.PrettyPrinter(indent=2).pprint(config)
                self.setup(config)
            except ConfigError:
                raise

    def setup(self, config):
        try:
            self.type = config['type']
            self.replications = config['replications']
            self.devices = Devices(config['devices'])
            self.scripts = Runner(config['scripts'])
            self.time_between_run = config['time_between_run']
            for device in self.devices:
                for name, installed in device.is_installed(config['dependencies']).items():
                    if not installed:
                        print('%s is not installed' % name)
                        exit(0)
            for t, c in config['measurements'].items():
                self.measurements[t] = getattr(import_module(t), t)(config['basedir'], c)
            if self.type == 'native':
                for device in self.devices:
                    device.install_apps(config['paths'])
        except ConnectionError as e:
            print(e.message)
            exit(0)
        except AdbError as e:
            print(e.message)

    def run_measure(self, func, device):
        for m in self.measurements.values():
            getattr(m, func)(device.id)

    def start(self):
        for device in self.devices:
            self.run_measure('load', device)
            Adb.unplug(device.id)
            self.scripts.run(device, 'setup')
            for i in range(self.replications):
                self.scripts.run(device, 'before_run')
                self.run_measure('start_measurement', device)
                self.scripts.run(device, 'interaction')
                self.run_measure('stop_measurement', device)
                self.scripts.run(device, 'after_run')
                self.run_measure('get_results', device)
                sleep(self.time_between_run / 1000.0)

            self.scripts.run(device, 'teardown')
            Adb.plug(device.id)
            self.run_measure('unload', device)
            if self.type == 'native':
                pass
