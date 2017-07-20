from imp import load_source
import logging
import json
import errno
import os
import os.path as op

import signal
import multiprocessing


class TimeoutError(Exception):
    pass

class ConfigError(Exception):
    pass

# https://stackoverflow.com/a/22348885
class timeout:
    def __init__(self, seconds):
        self.seconds = float(seconds)

    def handle_timeout(self, signum, frame):
        raise TimeoutError()

    def __enter__(self):
        if self.seconds != 0:
            signal.signal(signal.SIGALRM, self.handle_timeout)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)

    def __exit__(self, type, value, traceback):
        if self.seconds != 0:
            signal.alarm(0)


class Scripts(object):
    def __init__(self, config_dir, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scripts = {}
        for name, path in config.items():
            try:
                self.scripts[name] = load_source(name, op.join(config_dir, path))
                self.logger.info('Imported %s' % path)
            except ImportError:
                self.logger.error('Cannot import %s' % path)
                raise ImportError("Cannot import %s" % path)

    def run(self, device, name, *args, **kwargs):
        current_activity = device.current_activity()
        self.logger.debug('%s: Execute %s, current activity "%s"' % (device.id, name, current_activity))
        self.logger.info('Execute %s' % name)
        return self.scripts[name].main(device.id, current_activity, *args, **kwargs)

    def sommething(self):
        # if config.get('interaction_end_condition', None):
        #     end_condition = config['interaction_end_condition']
        #     self.timeout = end_condition.get('timeout', 0) / 1000
        #     self.logcat_event = end_condition.get('logcat_event', None)
        pass

    def mp_interaction(self, device, path, run, queue):
        self.interaction(device, path, run)
        queue.put('interaction')

    def mp_logcat_regex(self, device, regex, queue):
        # https://stackoverflow.com/a/21936682
        # pyadb uses subprocess.communicate(), therefore it blocks
        device.logcat_regex(regex)
        queue.put('logcat')

    def interaction_select(self, device, path, run):
        # https://stackoverflow.com/a/6286343
        with timeout(seconds=self.timeout):
            processes = []
            try:
                queue = multiprocessing.Queue()
                if self.logcat_event:
                    processes.append(multiprocessing.Process(target=self.mp_logcat_regex,
                                                             args=(device, self.logcat_event, queue)))
                processes.append(multiprocessing.Process(target=self.mp_interaction,
                                                         args=(device, path, run, queue)))
                for p in processes:
                    p.start()
                result = queue.get()
            except TimeoutError:
                self.logger.debug('Interaction function timeout (%sms)' % self.timeout)
                result = 'timeout'
            finally:
                for p in processes:
                    p.terminate()
            return result


class MonkeyRunner(object):
    def __init__(self, path):
        if not op.isfile(path):
            raise ImportError()

    def run(self):
        pass
        # import subprocess
        # subprocess.check_output()


class FileNotFoundError(Exception):
    pass


class FileFormatError(Exception):
    pass


def load_json(path):
    try:
        with open(path, 'r') as f:
            try:
                return json.loads(f.read())
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
