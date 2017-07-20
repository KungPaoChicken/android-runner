from time import sleep
from Experiment import Experiment


class WebExperiment(Experiment):
    def __init__(self, config):
        super(WebExperiment, self).__init__(config)
        # LOAD AND TEST BROWSER DEPENDENCIES
        # https://stackoverflow.com/a/28151563
        self.browser = 'com.android.chrome'
        self.main_activity = 'com.google.android.apps.chrome.Main'
        # self.browser = 'org.mozilla.focus'
        # self.main_activity = 'org.mozilla.focus.activity.MainActivity'

    def before_first_run(self, device, path):
        super(WebExperiment, self).before_first_run(device, path)
        self.logger.info('URL: %s' % path)

    def before_run(self, device, path, run):
        super(WebExperiment, self).before_run(device, path, run)
        device.launch(self.browser, self.main_activity, data_uri=path,
                      action='android.intent.action.VIEW', from_scratch=True)
        sleep(5)

    def after_run(self, device, path, run):
        super(WebExperiment, self).after_run(device, path, run)
        device.force_stop(self.browser)
        sleep(3)
