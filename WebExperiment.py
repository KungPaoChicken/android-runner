from time import sleep
from Experiment import Experiment


class WebExperiment(Experiment):
    def setup(self, config):
        super(WebExperiment, self).setup(config)

    def before_first_run(self, device, path):
        super(WebExperiment, self).before_first_run(device, path)
        self.logger.info('URL: %s' % path)

    def before_run(self, device, path, run):
        super(WebExperiment, self).before_run(device, path, run)
        device.launch('com.android.chrome',
                      'com.google.android.apps.chrome.Main',
                      action='android.intent.action.VIEW',
                      data=path
                      )
        sleep(10)

    def after_run(self, device, path, run):
        super(WebExperiment, self).after_run(device, path, run)
        device.force_stop('com.android.chrome')
        # device.clear_app_data('com.android.chrome')
        sleep(5)
