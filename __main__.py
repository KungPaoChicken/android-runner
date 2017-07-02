import argparse
from os.path import expanduser
from Experiment import Experiment
from ConfigParser import ConfigError
from Adb import AdbError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('-v', '--verbose')
    args = vars(parser.parse_args())
    # Add a verbose option

    try:
        experiment = Experiment(config_file=expanduser(args['file']))
        experiment.start()
    except ConfigError as e:
        print("There are some errors in the config file:")
        print('\n'.join(['- ' + m for m in e.message]))
    except AdbError as e:
        print(e.message)


if __name__ == "__main__":
    main()
