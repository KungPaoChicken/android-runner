import logging
import os.path as op

import util
from Experiment import Experiment
from NativeExperiment import NativeExperiment
from WebExperiment import WebExperiment

logger = logging.getLogger('ExperimentBuilder')


class ExperimentFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def from_json(path):
        logger.info(path)
        config = util.load_json(path)
        experiment_type = config['type']
        if experiment_type == 'native':
            return NativeExperiment(config)
        elif experiment_type == 'web':
            return WebExperiment(config)
        else:
            return Experiment(config)
