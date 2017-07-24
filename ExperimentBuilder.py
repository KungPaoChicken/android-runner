import logging
import os.path as op
from util import load_json
from Experiment import Experiment
from WebExperiment import WebExperiment
from NativeExperiment import NativeExperiment

logger = logging.getLogger('ExperimentBuilder')


class ExperimentBuilder(object):
    def __init__(self):
        pass

    @staticmethod
    def from_json(path):
        logger.info(path)
        config = load_json(path)
        experiment_type = config['type']
        config['config_dir'] = op.abspath(op.dirname(path))
        if experiment_type == 'native':
            return NativeExperiment(config)
        elif experiment_type == 'web':
            return WebExperiment(config)
        else:
            return Experiment(config)
