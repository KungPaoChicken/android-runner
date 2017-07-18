from imp import load_source
from importlib import import_module
import logging


class Scripts(object):
    def __init__(self, scripts):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scripts = {}
        for name, filename in scripts.items():
            try:
                self.scripts[name] = load_source(name, filename)
                self.logger.info('Imported %s' % filename)
            except ImportError:
                self.logger.error('Cannot import %s' % filename)
                raise ImportError("Cannot import %s" % filename)

    def run(self, device, name, *args, **kwargs):
        current_activity = device.current_activity()
        self.logger.debug('%s: Execute %s, current activity "%s"' % (device.id, name, current_activity))
        self.logger.info('Execute %s' % name)
        return self.scripts[name].main(device.id, current_activity, *args, **kwargs)


class Profilers(object):
    def __init__(self, basedir, classes):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.profilers = {}
        for name, classname in classes.items():
            self.profilers[name] = getattr(import_module(name), name)(basedir, classname)

    def run(self, method, device):
        for c in self.profilers.values():
            getattr(c, method)(device.id)
