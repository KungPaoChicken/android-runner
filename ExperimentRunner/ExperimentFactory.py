import logging
import os.path as op
import shutil

import paths
import util
from Experiment import Experiment
from NativeExperiment import NativeExperiment
from Progress import Progress
from WebExperiment import WebExperiment

logger = logging.getLogger('ExperimentFactory')


class ExperimentFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def from_json(path, progress):
        """Returns an Experiment object from a JSON configuration"""
        logger.info(path)
        shutil.copy(path, op.join(paths.OUTPUT_DIR, 'config.json'))
        config = util.load_json(path)
        experiment_type = config['type']
        if progress is None:
            progress = Progress(config_file=path, config=config, load_progress=False)
        if experiment_type == 'native':
            return NativeExperiment(config, progress)
        elif experiment_type == 'web':
            return WebExperiment(config, progress)
        else:
            return Experiment(config, progress)
