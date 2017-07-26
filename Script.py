import logging
import os.path as op
import signal
import multiprocessing as mp
import Tests


class Script(object):
    def __init__(self, path, timeout, logcat_regex=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.path = path
        self.filename = op.basename(path)
        self.timeout = Tests.is_integer(timeout) / 1000
        self.logcat_event = logcat_regex
        if logcat_regex is not None:
            self.logcat_event = Tests.is_string(logcat_regex)

    def execute_script(self, device_id, current_activity):
        self.logger.info(self.filename)

    def mp_run(self, device_id, current_activity, queue):
        output = self.execute_script(device_id, current_activity)
        self.logger.debug('%s returned %s' % (self.filename, output))
        queue.put('script')

    def mp_logcat_regex(self, device, regex, queue):
        # https://stackoverflow.com/a/21936682
        # pyadb uses subprocess.communicate(), therefore it blocks
        device.logcat_regex(regex)
        queue.put('logcat')

    def run(self, device, current_activity):
        # https://stackoverflow.com/a/6286343
        with script_timeout(seconds=self.timeout):
            processes = []
            try:
                queue = mp.Queue()
                if self.logcat_event:
                    processes.append(mp.Process(target=self.mp_logcat_regex,
                                                args=(device, self.logcat_event, queue)))
                processes.append(mp.Process(target=self.mp_run,
                                            args=(device.id, current_activity, queue)))
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


class TimeoutError(Exception):
    pass


# https://stackoverflow.com/a/22348885
class script_timeout:
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
