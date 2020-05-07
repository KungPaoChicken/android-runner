import logging
import os.path as op

import paths
from .MonkeyReplay import MonkeyReplay
from .MonkeyRunner import MonkeyRunner
from .Python3 import Python3
from .util import ConfigError


class Scripts(object):
    def __init__(self, config, monkeyrunner_path='monkeyrunner'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scripts = {}
        for name, script in list(config.items()):
            self.scripts[name] = []
            if isinstance(script, str):
                path = op.join(paths.CONFIG_DIR, script)
                self.scripts[name].append(Python3(path))
                continue
            for s in script:
                path = op.join(paths.CONFIG_DIR, s['path'])
                timeout = s.get('timeout', 0)
                logcat_regex = s.get('logcat_regex', None)

                if s['type'] == 'python3':
                    script = Python3(path, timeout, logcat_regex)
                elif s['type'] == 'monkeyreplay':
                    script = MonkeyReplay(path, timeout, logcat_regex, monkeyrunner_path)
                elif s['type'] == 'monkeyrunner':
                    script = MonkeyRunner(path, timeout, logcat_regex, monkeyrunner_path)
                else:
                    raise ConfigError('Unknown script type: {}'.format(s['type']))

                self.scripts[name].append(script)

    def run(self, name, device, *args, **kwargs):
        self.logger.debug('Running hook {} on device {}\nargs: {}\nkwargs: {}'.format(name, device, args, kwargs))
        for script in self.scripts.get(name, []):
            script.run(device, *args, **kwargs)
