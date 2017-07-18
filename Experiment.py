import logging
import signal
import multiprocessing
import time

from ConfigParser import ConfigParser
from util import Scripts, Profilers
from Devices import Devices


class TimeoutError(Exception):
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


class Experiment(object):
    def __init__(self, config_file=None):
        self.basedir = None
        self.type = None
        self.replications = 1
        self.devices = None
        self.paths = []
        self.profilers = None
        self.scripts = None
        self.time_between_run = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = 0
        self.logcat_event = None
        if config_file:
            config = ConfigParser(config_file).parse()
            self.setup(config)

    def check_dependencies(self, dependencies):
        error = False
        for device in self.devices:
            for name, installed in device.is_installed(dependencies).items():
                if not installed:
                    error = True
                    self.logger.error('Required package %s is not installed' % name)
        if error:
            exit(0)

    def setup(self, config):
        self.basedir = config['basedir']
        self.type = config['type']
        self.replications = config['replications']
        self.devices = Devices(config['devices'])
        self.paths = config['paths']
        self.scripts = Scripts(config['scripts'])
        self.time_between_run = config['time_between_run']
        self.paths = config['paths']
        if config.get('interaction_end_condition', None):
            end_condition = config['interaction_end_condition']
            self.timeout = end_condition.get('timeout', 0) / 1000
            self.logcat_event = end_condition.get('logcat_event', None)

        self.check_dependencies(config['dependencies'])
        self.profilers = Profilers(self.basedir, config['profilers'])

    def before_experiment(self, device):
        self.logger.info('Device: %s' % device)
        self.profilers.run('load', device)
        self.scripts.run(device, 'before_experiment')
        device.unplug()

    def before_first_run(self, device, path):
        pass

    def before_run(self, device, path, run):
        self.logger.info('Run %s of %s' % (run + 1, self.replications))
        self.scripts.run(device, 'before_run')

    def interaction(self, device, path, run):
        self.scripts.run(device, 'interaction')

    def after_run(self, device, path, run):
        self.scripts.run(device, 'after_run')
        self.profilers.run('collect_results', device)
        self.logger.debug('Sleeping for %s milliseconds' % self.time_between_run)
        time.sleep(self.time_between_run / 1000.0)

    def after_last_run(self, device, path):
        pass

    def after_experiment(self, device):
        self.logger.info('Experiment completed, start cleanup')
        self.scripts.run(device, 'after_experiment')
        device.plug()
        self.profilers.run('unload', device)

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

    def start(self):
        for device in self.devices:
            self.before_experiment(device)
            for path in self.paths:
                self.before_first_run(device, path)
                for run in range(self.replications):
                    self.before_run(device, path, run)
                    self.profilers.run('start_profiling', device)
                    self.interaction_select(device, path, run)
                    self.profilers.run('stop_profiling', device)
                    self.after_run(device, path, run)
                self.after_last_run(device, path)
            self.logger.info('Experiment completed, start cleanup')
            self.after_experiment(device)
