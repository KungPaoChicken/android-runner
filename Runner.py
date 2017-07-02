from imp import load_source
from Adb import Adb, AdbError


class Runner:
    def __init__(self, devices, scripts):
        self.devices = devices
        self.scripts = {}
        for k, v in scripts.items():
            try:
                self.scripts[k] = load_source(k, v)
            except ImportError:
                raise ImportError("Cannot import %s" % v)

    def run(self, name, device_id, current_activity, *args, **kwargs):
        return self.scripts[name].main(device_id, current_activity, *args, **kwargs)

    def measure(self):
        pass


class WebRunner(Runner):
    def __init__(self, config):
        Runner.__init__(self, config)
        self.browsers = config['browsers']
