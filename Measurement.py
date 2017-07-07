import os
import errno


class Measurement(object):
    @staticmethod
    def get_dependencies():
        return []

    def __init__(self, basedir, config):
        self.basedir = basedir

    def load(self, device_id):
        pass

    def start_measurement(self, device_id):
        # print('Measurement started')
        pass

    def stop_measurement(self, device_id):
        # print('Measurement stopped')
        pass

    def get_results(self, device_id):
        pass

    def unload(self, device_id):
        pass


def makedirs(path):
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
