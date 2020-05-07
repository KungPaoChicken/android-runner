import logging

from .util import ConfigError

def is_integer(number, minimum=0):
    if not isinstance(number, int):
        raise ConfigError('%s is not an integer' % number)
    if number < minimum:
        raise ConfigError('%s should be equal or larger than %i' % (number, minimum))
    return number


def is_string(string):
    if not isinstance(string, str):
        raise ConfigError('String expected, got %s' % type(string))
    return string


def check_dependencies(devices, dependencies):
    for device in devices:
        installed_apps = device.is_installed(dependencies)
        not_installed_apps = [name for name, installed in list(installed_apps.items()) if not installed]
        if not_installed_apps:
            for name in not_installed_apps:
                logging.error('%s: Required package %s is not installed' % (device.id, name))
            raise ConfigError('Required packages %s are not installed on device %s' % (not_installed_apps, device.id))
