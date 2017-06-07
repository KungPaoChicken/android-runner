import os.path as op
import sys
import errno
from imp import find_module
import json


def load_json(path):
    try:
        with open(path, 'r') as f:
            try:
                return json.loads(f.read())
            except ValueError:
                print("'%s' is not valid JSON" % path)
                raise
    except IOError as e:
        if e.errno == errno.ENOENT:
            print("'%s' not found" % path)
        raise


class ConfigError(Exception):
    pass


class ConfigParser:

    def __init__(self, config_file):
        # File loader
        self.config = None
        self.config_errors = []
        # Config file entries
        self.mandatory_keys = ['name', 'devices', 'type', 'runs', 'metrics', 'scripts']
        self.parsed_config = {
            'interface': 'adb',
            'paths': [],
            'basedir': op.abspath(op.dirname(config_file))
        }
        print(self.parsed_config['basedir'])
        try:
            self.config = load_json(config_file)
        except (ValueError, IOError):
            sys.exit(1)

    def get_value(self, key, exception=False):
        try:
            value = self.config[key]
        except KeyError:
            if exception:
                self.config_errors.append("Error: Key '%s' does not exist" % key)
                return None
            else:
                value = self.parsed_config[key]
        return value

    def test_imports(self, imports):
        for k, v in imports.iteritems():
            try:
                find_module(op.splitext(v)[0])
            except ImportError:
                self.config_errors.append("Error: '%s' cannot be imported" % v)

    def find_devices(self, devices):
        try:
            ids = load_json('devices.json')
            for device in devices:
                if not ids.get(device, None):
                    self.config_errors.append("Device '%s' not found in devices.json" % device)
        except (ValueError, IOError):
            sys.exit(1)

    def test_apks(self, apks):
        for f in filter(lambda x: not op.isfile(x), apks):
            self.config_errors.append("Error: File '%s' not found" % f)

    def parse(self):
        p = self.parsed_config
        p = {k: self.get_value(k) for k, v in p.iteritems()}
        p.update({k: self.get_value(k, exception=True) for k in self.mandatory_keys})

        if p['type'] == 'web':
            p['browsers'] = self.get_value('browsers')

        sys.path.append(p['basedir'])
        self.test_imports(p['scripts'])

        if len(self.config_errors) > 0:
            print('\n'.join(self.config_errors))
            return False
        self.parsed_config = p
        return True

    def run(self):
        pass
