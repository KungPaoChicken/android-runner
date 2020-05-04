import argparse
import logging
import os.path as op
import sys
import time

import paths
from AndroidRunner.ExperimentFactory import ExperimentFactory
from AndroidRunner.Progress import Progress
from AndroidRunner.util import makedirs


def main():
    args = parse_arguments(sys.argv[1:])
    progress, log_dir = set_progress(args)
    config_file = op.abspath(args['file'])
    setup_paths(config_file, log_dir)
    logger = setup_logger(log_dir)

    try:
        progress_file = progress.get_progress_xml_file()
    except Exception:
        progress_file = ' No progress file created'

    try:
        experiment = ExperimentFactory.from_json(config_file, progress)
        progress_file = experiment.get_progress_xml_file()
        experiment.start()
    except Exception as e:
        logger.error('%s: %s' % (e.__class__.__name__, str(e)))
        logger.error('An error occurred, the experiment has been stopped. '
                     'To continue, add progress file argument to experiment startup: '
                     '--progress {}'.format(progress_file))
    except KeyboardInterrupt:
        logger.error('Experiment stopped by user. '
                     'To continue, add progress file argument to experiment startup: '

                     '--progress {}'.format(progress_file))


def set_progress(args):
    config_file = op.abspath(args['file'])
    if not args.get('progress') is None:
        progress = Progress(progress_file=args['progress'], config_file=config_file, load_progress=True)
        log_dir = progress.get_output_dir()
    else:
        log_dir = op.join(op.dirname(config_file), 'output/%s/' % time.strftime('%Y.%m.%d_%H%M%S'))
        progress = None
    return progress, log_dir


def parse_arguments(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--progress', default=argparse.SUPPRESS)
    return vars(parser.parse_args(args))


def setup_paths(config_file, log_dir):
    paths.CONFIG_DIR = op.dirname(config_file)
    paths.ORIGINAL_CONFIG_DIR = config_file
    makedirs(log_dir)
    paths.OUTPUT_DIR = log_dir
    paths.BASE_OUTPUT_DIR = log_dir
    sys.path.append(op.join(paths.ROOT_DIR, 'AndroidRunner'))


def setup_logger(log_dir):
    log_filename = op.join(log_dir, 'experiment.log')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(set_file_logger(log_filename))
    logger.addHandler(set_stdout_logger())
    return logger


def set_file_logger(log_filename):
    file_logger = logging.FileHandler(log_filename)
    file_logger.setLevel(logging.DEBUG)
    file_logger.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
    return file_logger


def set_stdout_logger():
    stdout_logger = logging.StreamHandler(sys.stdout)
    stdout_logger.setLevel(logging.INFO)
    stdout_logger.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    return stdout_logger


if __name__ == "__main__": \
    main()
