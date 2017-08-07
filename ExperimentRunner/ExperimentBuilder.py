import logging
import os.path as op

import util
from Experiment import Experiment
from NativeExperiment import NativeExperiment
from WebExperiment import WebExperiment

logger = logging.getLogger('ExperimentBuilder')


class ExperimentBuilder(object):
    def __init__(self):
        pass

    @staticmethod
    def from_json(path):
        logger.info(path)
        config = util.load_json(path)
        experiment_type = config['type']
        config['config_dir'] = op.abspath(op.dirname(path))
        if experiment_type == 'native':
            return NativeExperiment(config)
        elif experiment_type == 'web':
            return WebExperiment(config)
        else:
            return Experiment(config)
