import os.path as op
import time

import Tests
import paths
from BrowserFactory import BrowserFactory
from Experiment import Experiment
from util import makedirs, slugify_dir


class WebExperiment(Experiment):
    def __init__(self, config, progress):
        super(WebExperiment, self).__init__(config, progress)
        self.browsers = [BrowserFactory.get_browser(b)(config) for b in config.get('browsers', ['chrome'])]
        Tests.check_dependencies(self.devices, [b.package_name for b in self.browsers])
        self.duration = Tests.is_integer(config.get('duration', 0)) / 1000

    def run(self, device, path, run, browser_name):
        browser = None
        for browserItem in self.browsers:
            if browser_name in browserItem.to_string():
                browser = browserItem
        self.before_run(device, path, run, browser)
        self.after_launch(device, path, run, browser)
        self.start_profiling(device, path, run, browser)
        self.interaction(device, path, run, browser)
        self.stop_profiling(device, path, run, browser)
        self.before_close(device, path, run, browser)
        self.after_run(device, path, run, browser)

    def last_run_subject(self, current_run):
        if self.progress.subject_finished(current_run['device'], current_run['path'], current_run['browser']):
            self.after_last_run(self.devices.get_device(current_run['device']), current_run['path'])
            self.aggregate_subject()

    def prepare_output_dir(self, current_run):
        paths.OUTPUT_DIR = op.join(paths.BASE_OUTPUT_DIR, 'data/', current_run['device'],
                                   slugify_dir(current_run['path']),
                                   current_run['browser'])
        makedirs(paths.OUTPUT_DIR)

    def before_run_subject(self, device, path, *args, **kwargs):
        super(WebExperiment, self).before_run_subject(device, path)
        self.logger.info('URL: %s' % path)

    def before_run(self, device, path, run, *args, **kwargs):
        super(WebExperiment, self).before_run(device, path, run)
        browser = args[0]
        browser.start(device)
        time.sleep(5)

    def interaction(self, device, path, run, *args, **kwargs):
        browser = args[0]
        browser.load_url(device, path)
        time.sleep(5)
        super(WebExperiment, self).interaction(device, path, run, *args, **kwargs)

        # TODO: Fix web experiments running longer than self.duration
        time.sleep(self.duration)

    def after_run(self, device, path, run, *args, **kwargs):
        browser = args[0]
        browser.stop(device, clear_data=True)
        time.sleep(3)
        super(WebExperiment, self).after_run(device, path, run)

    def after_last_run(self, device, path, *args, **kwargs):
        super(WebExperiment, self).after_last_run(device, path, *args, **kwargs)
        # https://stackoverflow.com/a/2860193

    def cleanup(self, device):
        super(WebExperiment, self).cleanup(device)
        for browser in self.browsers:
            browser.stop(device, clear_data=True)
