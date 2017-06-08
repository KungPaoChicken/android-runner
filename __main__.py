import sys
from os.path import expanduser
from config_parser import ConfigParser, ConfigError
import adb


def main():
    if len(sys.argv) == 1:
        print("Usage: android-runner config_file")

    '''
    Preconditions:
    1. Valid config file
    2. Devices can be connected
    3. Browsers and other tools are available
    '''

    def test_devices(devices):
        for device in devices:
            # print(adb.shell(device, 'dumpsys battery'))
            print(adb.shell(device, 'pm list packages'))

    # Check config file
    parser = ConfigParser(expanduser(sys.argv[1]))
    try:
        parsed_config = parser.parse()
        print("Config file is valid")
        test_devices(parsed_config['devices'])
    except ConfigError as e:
        print("There are some errors in the config file:")
        print('\n'.join(['- ' + m for m in e.message]))

    # experiment.run()


if __name__ == "__main__":
    main()
