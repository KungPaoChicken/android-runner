import os.path as op
from Experiment import Experiment


class NativeExperiment(Experiment):
    def before_experiment(self, device):
        super(NativeExperiment, self).before_experiment(device)
        for device in self.devices:
            device.install_apks(self.paths)

    def before_first_run(self, device, path):
        super(NativeExperiment, self).before_first_run(device, path)
        self.logger.info('APK: %s' % op.basename(path))

    def after_last_run(self, device, path):
        pass

    def after_experiment(self, device):
        super(NativeExperiment, self).after_experiment(device)
        device.uninstall_apps([op.splitext(op.basename(apk))[0] for apk in self.paths])
