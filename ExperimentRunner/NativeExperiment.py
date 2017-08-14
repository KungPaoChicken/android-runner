import os.path as op
from Experiment import Experiment
from util import ConfigError, makedirs, slugify
import paths


class NativeExperiment(Experiment):
    def __init__(self, config):
        super(NativeExperiment, self).__init__(config)
        for apk in config.get('paths', []):
            if not op.isfile(apk):
                raise ConfigError('File %s not found' % apk)

    def prepare(self, device):
        super(NativeExperiment, self).prepare(device)
        device.install_apks(self.paths)

    def cleanup(self, device):
        super(NativeExperiment, self).cleanup(device)
        device.uninstall_apps([op.splitext(op.basename(apk))[0] for apk in self.paths])

    def before_experiment(self, device):
        super(NativeExperiment, self).before_experiment(device)

    def before_first_run(self, device, path):
        super(NativeExperiment, self).before_first_run(device, path)
        filename = op.basename(path)
        paths.OUTPUT_DIR = op.join(paths.OUTPUT_DIR, slugify(filename))
        makedirs(paths.OUTPUT_DIR)
        self.logger.info('APK: %s' % filename)

    def before_run(self, device, path, run):
        super(NativeExperiment, self).before_run(device, path, run)
        device.launch('coolcherrytrees.games.reactor4', '.GameActivity')

    def after_run(self, device, path, run):
        super(NativeExperiment, self).after_run(device, path, run)
        device.force_stop('coolcherrytrees.games.reactor4')

    def after_experiment(self, device):
        super(NativeExperiment, self).after_experiment(device)
