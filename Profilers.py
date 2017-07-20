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
        for p in self.profilers:
            p.load(device.id)

    def start_profiling(self, device):
        for p in self.profilers:
            p.start_profiling(device.id)

    def stop_profiling(self, device):
        for p in self.profilers:
            p.stop_profiling(device.id)

    def unload(self, device):
        for p in self.profilers:
            p.unload(device.id)
