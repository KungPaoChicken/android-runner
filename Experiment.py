import sys
from os.path import splitext
from imp import find_module, load_module
from adb import Adb, AdbError


class Experiment:
    def __init__(self, config):
        self.config = config
        self.devices = config['devices']
        self.replications = config['replications']
        self.adb = None
        sys.path.append(config['basedir'])
        print(config['scripts'])
        self.scripts = {k: find_module(splitext(k)[0]) for k, v in config['scripts'].items()}
        map(lambda (n, m): load_module(n, *m), self.scripts.items())
        # print(self.scripts)

    def test(self):
        try:
            self.adb = Adb(self.devices)
            return True
        except AdbError as e:
            print(e.message)
            exit(0)

    def setup(self, *args, **kwargs):
        return self.scripts['setup'].main(*args, **kwargs)

    def before_run(self, *args, **kwargs):
        return self.scripts['before_run'].main(*args, **kwargs)

    def interaction(self, *args, **kwargs):
        return self.scripts['interaction'].main(*args, **kwargs)

    def after_run(self, *args, **kwargs):
        return self.scripts['after_run'].main(*args, **kwargs)

    def teardown(self, *args, **kwargs):
        return self.scripts['teardown'].main(*args, **kwargs)

    def start(self):
        if self.test():
            print('Tests passed')
            self.setup()
            for i in range(self.replications):
                self.before_run()
                self.interaction()
                self.after_run()
            self.teardown()


class NativeExperiment(Experiment):
    def test(self):
        if not Experiment.test(self):
            return False
        # Install APKs
        self.adb.install(self.config['paths'])


class WebExperiment(Experiment):
    def test(self):
        if not Experiment.test(self):
            return False
        try:
            pass
            # bc = self.adb.browser_check(self.config['browsers'])
        except AdbError as e:
            print(e.message)
            return False
        return True
        # return self.adb.browser_check(self.devices, self.config['browsers'])
