import time
import os.path as op

from Experiment import Experiment
import Tests
import paths
from util import makedirs, slugify


class WebExperiment(Experiment):
    def __init__(self, config):
        super(WebExperiment, self).__init__(config)
        # https://stackoverflow.com/a/28151563
        self.browser = 'com.android.chrome'
        self.main_activity = 'com.google.android.apps.chrome.Main'
        Tests.check_dependencies(self.devices, [self.browser])

    def before_first_run(self, device, path):
        super(WebExperiment, self).before_first_run(device, path)
        paths.OUTPUT_DIR = op.join(paths.OUTPUT_DIR, slugify(path))
        makedirs(paths.OUTPUT_DIR)
        self.logger.info('URL: %s' % path)

    def before_run(self, device, path, run):
        super(WebExperiment, self).before_run(device, path, run)
        device.launch_activity(self.browser, self.main_activity, data_uri=path,
                               action='android.intent.action.VIEW', from_scratch=True, force_stop=True)
        time.sleep(5)
        self.scripts.run('after_launch', device, device.id, device.current_activity())

    def after_run(self, device, path, run):
        self.scripts.run('before_close', device, device.id, device.current_activity())
        device.force_stop(self.browser)
        time.sleep(3)
        super(WebExperiment, self).after_run(device, path, run)
