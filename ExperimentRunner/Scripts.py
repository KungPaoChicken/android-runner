import logging
import os.path as op

from util import ConfigError
from PythonScript import PythonScript
from MonkeyRunner import MonkeyRunner


class Scripts(object):
    def __init__(self, config_dir, config, monkeyrunner_path='monkeyrunner'):
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
                    self.scripts[name].append(
                        MonkeyRunner(path, timeout, logcat_regex, config_dir, monkeyrunner_path=monkeyrunner_path))
                else:
                    raise ConfigError('Unknown script type')

    def run(self, device, name, current_activity):
        for script in self.scripts[name]:
            script.run(device, current_activity)
