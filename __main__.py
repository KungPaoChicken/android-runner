import sys
from os.path import expanduser
from config_parser import ConfigParser, ConfigError


def main():
    if len(sys.argv) == 1:
        print("Usage: android-runner config_file")

    '''
    Preconditions:
    1. Valid config file
    2. Devices can be connected
    3. Browsers and other tools are available
    '''

    # Check config file
    parser = ConfigParser(expanduser(sys.argv[1]))
    try:
        if parser.parse():
            parsed_config = parser.config
    except ConfigError:
        pass

    # print("Config file is valid")
    # sys
    # print
    # Check the devices


if __name__ == "__main__":
    main()
