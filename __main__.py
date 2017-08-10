import argparse
import logging
import time
import os.path as op
import sys
from ExperimentRunner.ExperimentFactory import ExperimentFactory
from ExperimentRunner.util import makedirs
from config import ROOT_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = vars(parser.parse_args())

    config_path = op.abspath(args['file'])
    log_path = op.join(op.dirname(config_path), 'log/')
    log_filename = op.join(log_path, '%s.log' % time.strftime('%Y.%m.%d_%H%M%S'))
    makedirs(log_path)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_logger = logging.FileHandler(log_filename)
    file_logger.setLevel(logging.DEBUG)
    file_logger.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
    logger.addHandler(file_logger)

    stdout_logger = logging.StreamHandler(sys.stdout)
    stdout_logger.setLevel(logging.INFO)
    stdout_logger.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    logger.addHandler(stdout_logger)

    sys.path.append(op.join(ROOT_DIR, 'ExperimentRunner'))

    try:
        experiment = ExperimentFactory.from_json(config_path)
        experiment.start()
    except Exception, e:
        logger.error('%s: %s' % (e.__class__.__name__, e.message))
        raise


if __name__ == "__main__":
    main()
