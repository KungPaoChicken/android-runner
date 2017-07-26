import os.path as op
from Script import Script
import subprocess


class MonkeyRunnerError(Exception):
    pass


class MonkeyRunner(Script):
    def __init__(self, path, timeout, logcat_regex, config_path, monkeyrunner_path='monkeyrunner'):
        super(MonkeyRunner, self).__init__(path, timeout, logcat_regex)
        if not op.isfile(path):
            raise ImportError('%s is not a file' % path)
        self.monkeyrunner = monkeyrunner_path
        self.logger.info('Script path: %s' % self.path)
        self.config_path = config_path

    def execute_script(self, device_id, current_activity):
        super(MonkeyRunner, self).execute_script(device_id, current_activity)
        # https://docs.python.org/2/library/subprocess.html
        try:
            args = [self.monkeyrunner, self.path, device_id, current_activity, self.config_path]
            cmdp = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, error = cmdp.communicate()
            return_code = cmdp.wait()
            if error:
                raise MonkeyRunnerError(error)
            return return_code
        except OSError, e:
            print(str(e))
