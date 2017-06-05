import os
import errno
from importlib import import_module
import json
import pprint


class Experiment:
    def __init__(self):
        # File loader
        self.config = None
        self.config_errors = []
        # Config file entries
        self.mandatory_keys = ['name', 'devices', 'type', 'runs', 'metrics', 'scripts']
        self.parameters = {
            'interface': 'adb',
            'paths': [],
            'basedir': '',
        }

    def from_config(self, config_file):
        try:
            self.parameters['basedir'] = os.path.dirname(config_file)
            with open(config_file, 'r') as f:
                try:
                    self.config = json.loads(f.read())
                except ValueError:
                    print("File is not valid JSON")
        except IOError as e:
            if e.errno == errno.ENOENT:
                print("File not found, please check the path.")
            else:
                raise
        return self

    def value_or_error(self, key):
        try:
            return self.config[key]
        except KeyError:
            self.config_errors.append("Error: Key '%s' does not exist" % key)
            pass

    def value_or_default(self, key):
        try:
            value = self.config[key]
        except KeyError:
            value = self.parameters[key]
        return value

    def import_script(self, mod):
        try:
            ref = import_module(mod)
            return ref
        except ImportError:
            self.config_errors.append("Error: Module '%s' cannot be imported" % mod)
            return None

    def check_devices(self):
        try:
            for device in self.parameters['devices']:
                pass
            # connect(device)
        except:
            pass

    def is_valid(self):
        p = self.parameters
        p = {k: self.value_or_default(k) for k, v in p.iteritems()}
        p.update({k: self.value_or_error(k) for k in self.mandatory_keys})
        if p['type'] == 'web':
            p['browsers'] = self.value_or_error('browsers')
        p['scripts'] = {k: self.import_script(v) for k, v in p['scripts'].iteritems()}

        pprint.pprint(p, width=1)

        if self.config_errors:
            print('\n'.join(self.config_errors))
            return False

        self.check_devices()

        return True

    def run(self):
        pass
