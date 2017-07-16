import argparse
from os.path import expanduser
# from Experiment import Experiment
from WebExperiment import WebExperiment
from ConfigParser import ConfigError
from Adb import ConnectionError, AdbError
import logging
import sys

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
        experiment = WebExperiment(config_file=expanduser(args['file']))
        experiment.start()
    except ConfigError as e:
        print("There are some errors in the config file:")
        print('\n'.join(['- ' + m for m in e.message]))
    except ConnectionError as e:
        print(e.message)
        exit(0)
    except AdbError as e:
        print(e.message)
        exit(0)


if __name__ == "__main__":
    main()
