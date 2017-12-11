import os.path as op
import time

import Tests
import paths
from Experiment import Experiment
from BrowserFactory import BrowserFactory
from util import makedirs, slugify


class WebExperiment(Experiment):
    def __init__(self, config):
        super(WebExperiment, self).__init__(config)
        self.browsers = [BrowserFactory.get_browser(b)(config) for b in config.get('browsers', ['chrome'])]
        self.browser = 'com.android.chrome'
        self.main_activity = 'com.google.android.apps.chrome.Main'
        Tests.check_dependencies(self.devices, [self.browser])

    def run(self, device, path, run):
        # for browser in self.browsers:
        self.before_run(device, path, run)
        self.start_profiling(device, path, run)
        self.interaction(device, path, run)
        self.stop_profiling(device, path, run)
        self.after_run(device, path, run)

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
