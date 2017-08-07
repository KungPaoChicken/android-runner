import logging


class Browser(object):
    @staticmethod
    def dependencies():
        return []

    @staticmethod
    def package_name():
        raise NotImplementedError

    @staticmethod
    def main_activity():
        raise NotImplementedError

    def __init__(self, basedir, config):
        self.basedir = basedir
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self, device_id, url=None):
        self.logger.info('%s: Loading configuration' % device_id)

    def unload(self, device_id):
        self.logger.info('%s: Cleanup' % device_id)
