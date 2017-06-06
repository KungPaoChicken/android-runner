import os
import sys
import errno
from importlib import import_module
import json
import android
from adb import usb_exceptions
# import pprint


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

    @staticmethod
    def load_json(path):
        try:
            with open(path, 'r') as f:
                try:
                    return json.loads(f.read())
                except ValueError:
                    print("File '%s' is not valid JSON" % path)
                    raise
        except IOError as e:
            if e.errno == errno.ENOENT:
                print("File '%s' not found, please check the path." % path)
            raise

    def from_config(self, config_file):
        try:
            self.parameters['basedir'] = os.path.dirname(os.path.abspath(config_file))
            self.config = Experiment.load_json(config_file)
        except (ValueError, IOError):
            sys.exit(1)
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
            ref = import_module(os.path.splitext(mod)[0])
            return ref
        except ImportError:
            self.config_errors.append("Error: Module '%s' cannot be imported" % mod)
            return None

    def check_device(self, device_id):
        try:
            d = android.connect(device_id)
            # print(d.List('/sdcard/Download'))
            return d
        except usb_exceptions.DeviceNotFoundError:
            self.config_errors.append("Cannot connect to device with id %s" % device_id)

    def is_valid(self):
        p = self.parameters
        p = {k: self.value_or_default(k) for k, v in p.iteritems()}
        p.update({k: self.value_or_error(k) for k in self.mandatory_keys})
        if p['type'] == 'web':
            p['browsers'] = self.value_or_error('browsers')
        sys.path.append(p['basedir'])
        p['scripts'] = {k: self.import_script(v) for k, v in p['scripts'].iteritems()}

        # pprint.pprint(p, width=1)
        # Convert device names into id if possible
        try:
            ids = Experiment.load_json('devices.json')
            p['devices'] = [ids.get(d, d) for d in p['devices']]
        except (ValueError, IOError):
            sys.exit(1)

        for device in p['devices']:
            self.check_device(device)

        if self.config_errors:
            print('\n'.join(self.config_errors))
            return False
        return True

    def run(self):
        pass
