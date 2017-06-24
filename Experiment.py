import sys
from os.path import splitext
from imp import find_module, load_module
from importlib import import_module
from adb import Adb, AdbError


class Experiment:
    def __init__(self, config):
        self.config = config
        self.devices = config['devices']
        self.replications = config['replications']
        self.adb = None
        sys.path.append(config['basedir'])
        self.scripts = {k: import_module(splitext(k)[0]) for k in config['scripts'].keys()}
        # map(lambda (n, m): load_module(n, *m), self.scripts.items())
        # print(self.scripts['setup'])

    def test(self):
        try:cd 
            self.adb = Adb(self.devices)
        except AdbError as e:
            print(e.message)
            exit(0)

        results = self.adb.is_installed(['com.quicinc.trepn'])
        error_msg = []
        for device, apps in results.items():
            not_installed = [a for a, installed in apps.items() if not installed]
            error_msg = [a + " is not installed on %s" % device for a in not_installed]
        if error_msg:
            raise AdbError('\n'.join(error_msg))
        return True

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

    def measure(self):
        pass

    def start(self):
        if self.test():
            self.setup()
            for i in range(self.replications):
                self.before_run()
                self.measure()
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
    def __init__(self, config):
        Experiment.__init__(self, config)
        self.browsers = config['browsers']

    def test(self):
        if not Experiment.test(self):
            return False
        browsers_list = {'chrome': 'com.android.chrome',
                         'opera': 'com.opera.browser',
                         'firefox': 'org.mozilla.firefox'
                         }
        browsers = map(browsers_list.get, self.browsers)
        results = self.adb.is_installed(browsers)
        error_msg = []
        for device, apps in results.items():
            not_installed = [a for a, installed in apps.items() if not installed]
            error_msg = [a + " is not installed on %s" % device for a in not_installed]
        if error_msg:
            # print('\n'.join(error_msg))
            # return False
            return True
        return True
        # return self.adb.browser_check(self.devices, self.config['browsers'])
