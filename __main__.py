import argparse
import sys
from os.path import expanduser
from ConfigParser import ConfigParser, ConfigError
from Experiment import Experiment, NativeExperiment, WebExperiment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('-v', '--verbose')
    args = vars(parser.parse_args())
    # Add a verbose option

    '''
    Preconditions:
    1. Valid config file
    2. Devices are connected
    3. Browsers and other tools are available
    '''

    try:
        parser = ConfigParser(expanduser(args['file']))
        parsed_config = parser.parse()
        # print("Config file is valid"
        if parsed_config['type'] == 'native':
            experiment = NativeExperiment(parsed_config)
        elif parsed_config['type'] == 'web':
            experiment = WebExperiment(parsed_config)
        else:
            experiment = Experiment(parsed_config)
        experiment.start()
    except ConfigError as e:
        print("There are some errors in the config file:")
        print('\n'.join(['- ' + m for m in e.message]))


if __name__ == "__main__":
    main()
