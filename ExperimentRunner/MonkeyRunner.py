from Script import Script
import subprocess


class MonkeyRunnerError(Exception):
    pass


class MonkeyRunner(Script):
    def __init__(self, path, config_dir, timeout=0, logcat_regex=None, monkeyrunner_path='monkeyrunner'):
        super(MonkeyRunner, self).__init__(path, timeout, logcat_regex)
        self.monkeyrunner = monkeyrunner_path
        self.logger.debug('Script path: %s' % self.path)
        self.config_dir = config_dir

    def execute_script(self, device_id, current_activity):
        super(MonkeyRunner, self).execute_script(device_id, current_activity)
        # https://docs.python.org/2/library/subprocess.html
        args = [self.monkeyrunner, self.path, device_id, current_activity, self.config_dir]
        cmdp = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = cmdp.communicate()
        return_code = cmdp.wait()
        if return_code != 0:
            raise MonkeyRunnerError(output)
        return return_code
