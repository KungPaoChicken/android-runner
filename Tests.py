import logging
import os.path as op
from util import ConfigError


def valid_files(paths):
    for f in filter(lambda x: not op.isfile(x), paths):
        raise ConfigError("File %s not found" % f)


def is_integer(number, minimum=0):
    if not isinstance(number, (int, long)):
        raise ConfigError('%s is not an integer' % number)
    if number < minimum:
        raise ConfigError('%s should be equal or larger than %i' % (number, minimum))
    return number


# DOUBLE CHECK
def check_dependencies(devices, dependencies):
    for device in devices:
        for name, installed in device.is_installed(dependencies).items():
            if not installed:
                logging.error('Required package %s is not installed' % name)
