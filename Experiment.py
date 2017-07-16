from importlib import import_module
import logging
from time import sleep
from ConfigParser import ConfigParser
from Devices import Devices
from Runner import Runner
import json


class Experiment(object):
    def __init__(self, config_file=None):
        self.basedir = None
        self.type = None
        self.replications = 1
        self.devices = None
        self.paths = []
        self.profilers = {}
        self.scripts = None
        self.time_between_run = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        if config_file:
            config = ConfigParser(config_file).parse()
            # Check pprint docs
            self.logger.debug('Parsed config:\n%s' % json.dumps(config, indent=2))
            self.setup(config)

    def check_dependencies(self, dependencies):
        error = False
        for device in self.devices:
            for name, installed in device.is_installed(dependencies).items():
                if not installed:
                    error = True
                    self.logger.error('Required package %s is not installed' % name)
        if error:
            exit(0)

    def load_profilers(self, profilers):
        for t, c in profilers.items():
            self.profilers[t] = getattr(import_module(t), t)(self.basedir, c)

    def setup(self, config):
        self.basedir = config['basedir']
        self.type = config['type']
        self.replications = config['replications']
        self.devices = Devices(config['devices'])
        self.paths = config['paths']
        self.scripts = Runner(config['scripts'])
        self.time_between_run = config['time_between_run']
        self.paths = config['paths']

        self.check_dependencies(config['dependencies'])
        self.load_profilers(config['profilers'])

    def profilers_run(self, func, device):
        for m in self.profilers.values():
            getattr(m, func)(device.id)

    def before_experiment(self, device):
        self.logger.info('Device: %s' % device)
        self.profilers_run('load', device)
        self.scripts.run(device, 'before_experiment')
        device.unplug()

    def before_first_run(self, device, path):
        pass

    def before_run(self, device, path, run):
        self.logger.info('Run %s of %s' % (run + 1, self.replications))
        self.scripts.run(device, 'before_run')

    def after_run(self, device, path, run):
        self.scripts.run(device, 'after_run')
        self.profilers_run('collect_results', device)
        self.logger.debug('Sleeping for %s milliseconds' % self.time_between_run)
        sleep(self.time_between_run / 1000.0)

    def after_last_run(self, device, path):
        pass

    def after_experiment(self, device):
        self.logger.info('Experiment completed, start cleanup')
        self.scripts.run(device, 'after_experiment')
        device.plug()
        self.profilers_run('unload', device)

    def start(self):
        for device in self.devices:
            self.before_experiment(device)
            for path in self.paths:
                self.before_first_run(device, path)
                for i in range(self.replications):
                    self.before_run(device, path, i)
                    self.profilers_run('start_profiling', device)
                    self.scripts.run(device, 'interaction')
                    self.profilers_run('stop_profiling', device)
                    self.after_run(device, path, i)
                self.after_last_run(device, path)
            self.logger.info('Experiment completed, start cleanup')
            self.after_experiment(device)
