import logging
from collections import OrderedDict
import json
import errno
import os
import os.path as op

from PythonScript import PythonScript
from MonkeyRunner import MonkeyRunner


class ConfigError(Exception):
    pass


class Scripts(object):
    def __init__(self, config_dir, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scripts = {}
        for name, script in config.items():
            self.scripts[name] = []
            if isinstance(script, basestring):
                path = op.join(config_dir, script)
                self.scripts[name].append(PythonScript(path))
                continue
            for s in script:
                path = op.join(config_dir, s['path'])
                timeout = s.get('timeout', 0)
                logcat_regex = s.get('logcat_regex', None)
                if s['type'] == 'python':
                    self.scripts[name].append(PythonScript(path, timeout, logcat_regex))
                elif s['type'] == 'monkeyrunner':
                    self.scripts[name].append(MonkeyRunner(path, timeout, logcat_regex, config_dir))
                else:
                    raise ConfigError('Unknown script type')

    def run(self, device, name, current_activity):
        for script in self.scripts[name]:
            script.run(device, current_activity)


class FileNotFoundError(Exception):
    pass


class FileFormatError(Exception):
    pass


def load_json(path):
    try:
        with open(path, 'r') as f:
            try:
                return json.loads(f.read(), object_pairs_hook=OrderedDict)
            except ValueError:
                raise FileFormatError()
    except IOError as e:
        if e.errno == errno.ENOENT:
            raise FileNotFoundError()


def map_or_fail(keys, dictionary, error_string):
    for k in filter(lambda d: not dictionary.get(d, None), keys):
        raise ConfigError(error_string % k)
    return {k: v for k, v in dictionary.items() if k in keys}


def makedirs(path):
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
