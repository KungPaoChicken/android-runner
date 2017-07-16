import os
import errno
import logging


class Browser(object):
    @staticmethod
    def get_dependencies():
        return []

    def __init__(self, basedir, config):
        self.basedir = basedir
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self, device_id):
        self.logger.info('%s: Loading configuration' % device_id)

    def load_page(self, device_id, url):
        self.logger.info('%s: ' % device_id)

    def stop_measurement(self, device_id):
        self.logger.info('%s: Stop measurement' % device_id)

    def collect_results(self, device_id):
        self.logger.info('%s: Collecting data' % device_id)

    def unload(self, device_id):
        self.logger.info('%s: Cleanup' % device_id)


def makedirs(path):
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
