import argparse
import logging
import os.path as op
import sys
from ExperimentBuilder import ExperimentBuilder


def main():
    # %(levelname)s: %(name)s: %(message)s
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = vars(parser.parse_args())
    logging_level = logging.DEBUG if args['verbose'] else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=logging_level, format='%(name)s: %(message)s')
    logger = logging.getLogger(__name__)

    try:
        experiment = ExperimentBuilder.from_json(op.expanduser(args['file']))
        experiment.start()
    except Exception, e:
        logger.error('%s: %s' % (e.__class__.__name__, e.message))


if __name__ == "__main__":
    main()
