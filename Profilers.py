import logging
from importlib import import_module
from itertools import chain


class Profilers(object):
    def __init__(self, config_dir, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.profilers = []
        for name, params in config.items():
            name = name.capitalize()
            self.profilers.append(getattr(import_module(name), name)(config_dir, params))

    def dependencies(self):
        # https://stackoverflow.com/a/953097
        return list(chain.from_iterable([p.dependencies() for p in self.profilers]))

    def load(self, device):
        self.logger.info('Loading')
        for p in self.profilers:
            p.load(device)

    def start_profiling(self, device):
        self.logger.info('Start profiling')
        for p in self.profilers:
            p.start_profiling(device)

    def stop_profiling(self, device):
        self.logger.info('Stop profiling')
        for p in self.profilers:
            p.stop_profiling(device)

    def collect_results(self, device, path=None):
        self.logger.info('Collecting results')
        for p in self.profilers:
            p.collect_results(device, path)

    def unload(self, device):
        self.logger.info('Unloading')
        for p in self.profilers:
            p.unload(device)
