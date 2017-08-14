import os
import errno
import logging


class Profiler(object):
    @staticmethod
    def dependencies():
        return []

    def __init__(self, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Initialized')

    def load(self, device):
        self.logger.debug('%s: Loading configuration' % device)

    def start_profiling(self, device):
        self.logger.debug('%s: Start profiling' % device)

    def stop_profiling(self, device):
        self.logger.debug('%s: Stop profilers' % device)

    def collect_results(self, device, path=None):
        self.logger.debug('%s: Collecting data' % device)

    def unload(self, device):
        self.logger.debug('%s: Cleanup' % device)
