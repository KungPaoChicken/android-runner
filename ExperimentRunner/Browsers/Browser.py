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

    def start(self, device):
        self.logger.info('%s: Start %s' % device.id)
        device.launch_activity(self.package_name(), self.main_activity(), from_scratch=True, force_stop=True,
                               action='android.intent.action.VIEW')

    def load_url(self, device, url):
        self.logger.info('%s: Load URL: %s' % (device.id, url))
        device.launch_activity(self.package_name(), self.main_activity(), data_uri=url,
                               action='android.intent.action.VIEW')

    def stop(self, device, clear_data=False):
        self.logger.info('%s: Stop' % device.id)
        device.force_stop(self.package_name())
        if clear_data:
            device.clear_app_data(self.package_name())
