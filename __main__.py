import argparse
import logging
import time
import os.path as op
import sys
from ExperimentRunner.Progress import Progress
from ExperimentRunner.ExperimentFactory import ExperimentFactory
from ExperimentRunner.util import makedirs
import paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--progress', default=argparse.SUPPRESS)
    args = vars(parser.parse_args())

    config_file = op.abspath(args['file'])
    paths.CONFIG_DIR = op.dirname(config_file)
    paths.ORIGINAL_CONFIG_DIR = config_file
    if 'progress' in args:
        progress = Progress(progress_file=args['progress'], config_file=config_file, load_progress=True)
        log_dir = progress.get_output_dir()
    else:
        log_dir = op.join(paths.CONFIG_DIR, 'output/%s/' % time.strftime('%Y.%m.%d_%H%M%S'))
        progress = None

    makedirs(log_dir)
    paths.OUTPUT_DIR = log_dir
    paths.BASE_OUTPUT_DIR = log_dir
    log_filename = op.join(log_dir, 'experiment.log')

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

    sys.path.append(op.join(paths.ROOT_DIR, 'ExperimentRunner'))
    progress_file = ' No progress file created'
    try:
        experiment = ExperimentFactory.from_json(config_file, progress)
        progress_file = experiment.get_progress_xml_file()
        experiment.start()
    except Exception, e:
        logger.error('%s: %s' % (e.__class__.__name__, e.message))
        logger.error('An error occurred, the experiment has been stopped. '
                     'To continue, add progress file argument to experiment startup: '
                     '--progress {}'.format(progress_file))
    except KeyboardInterrupt:
        logger.error('Experiment stopped by user. '
                     'To continue, add progress file argument to experiment startup: '
                     '--progress {}'.format(progress_file))


if __name__ == "__main__":
    main()
