from ConfigParser import ConfigParser, ConfigError
from Devices import Devices
from Runner import Runner
from Adb import ConnectionError, AdbError
import pprint


class Experiment:
    def __init__(self, config_file=None):
        self.replications = 1
        self.devices = None
        self.measurements = None
        self.scripts = None
        if config_file:
            try:
                config = ConfigParser(config_file).parse()
                # pprint.PrettyPrinter(indent=2).pprint(config)
                self.setup(config)
            except ConfigError:
                raise

    def setup(self, config):
        try:
            self.replications = config['replications']
            self.devices = Devices(config['devices'])
            self.measurements = config['measurements']
            self.scripts = Runner(config['scripts'])
            for device in self.devices:
                for name, installed in device.is_installed(config['dependencies']).items():
                    if not installed:
                        print('%s is not installed' % name)
                device.install_apps(config['paths'])
        except ConnectionError as e:
            print(e.message)
            exit(0)
        except AdbError as e:
            print(e.message)

    def start(self):
        for device in self.devices:
            self.scripts.run(device, 'setup')
            for i in range(self.replications):
                self.scripts.run(device, 'before_run')
                # self.scripts.start_measurement()
                self.scripts.run(device, 'interaction')
                # self.scripts.stop_measurement()
                self.scripts.run(device, 'after_run')
            self.scripts.run(device, 'teardown')
