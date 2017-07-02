from ConfigParser import ConfigParser, ConfigError
from Devices import Devices
from Runner import Runner
from Adb import Adb, AdbError


class Experiment:
    def __init__(self, config_file=None):
        if config_file:
            try:
                config = ConfigParser(config_file).parse()
                self.replications = config['replications']
                self.devices = Devices(config['devices'])
                self.scripts = Runner(self.devices, config['scripts'])
                self.devices.check_apps(config['dependencies'])
                self.devices.install_apps(config['paths'])
            except ConfigError:
                raise
            except AdbError as e:
                print(e.message)

    def start(self):
        for dev in self.devices.ids():
            self.scripts.run('setup')
            for i in range(self.replications):
                self.scripts.run('before_run')
                self.scripts.measure()
                self.scripts.run('interaction')
                self.scripts.run('after_run')
            self.scripts.run('teardown')
