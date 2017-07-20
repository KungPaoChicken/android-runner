import argparse
import logging
import os.path as op
import sys
from WebExperiment import WebExperiment
from util import ConfigError
from Adb import ConnectionError, AdbError
from ExperimentBuilder import ExperimentBuilder

# %(levelname)s: %(name)s: %(message)s
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(name)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = vars(parser.parse_args())
    # args['verbose']

    try:
        experiment = ExperimentBuilder.from_json(op.expanduser(args['file']))
        experiment.start()
    except ConfigError as e:
        print(e.message)
    except ConnectionError as e:
        print(e.message)
        exit(0)
    except AdbError as e:
        print(e.message)
        exit(0)


if __name__ == "__main__":
    main()
