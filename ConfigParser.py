import os.path as op
import sys
import errno
from imp import find_module
import json


class ConfigError(Exception):
    """Raised when a config error occurred"""
    pass


class ConfigParser:
    def __init__(self, config_file):
        self.config = None
        self.errors = []
        self.mandatory_keys = ['devices', 'type', 'replications', 'measurements', 'scripts']
        self.defaults = {
            'paths': [],
            'basedir': op.abspath(op.dirname(config_file))
        }

        try:
            self.config = load_json(config_file)
        except (ValueError, IOError):
            raise ConfigError('Configuration not valid')

    def append_exceptions(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigError as e:
            self.errors.append(e.message)

    def parse(self):
        parsed_config = {}
        ae = self.append_exceptions
        for k in self.mandatory_keys:
            parsed_config[k] = ae(get_value, self.config, k, mandatory=True)

        for k, v in self.defaults.items():
            parsed_config[k] = ae(get_value, self.config, k, default=self.defaults[k])

        dependencies = []

        if self.config['type'] == 'web':
            dependencies = dependencies + ae(get_value, self.config, 'browsers', mandatory=True)

        # if self.config['measurements']:
        #     dependencies = dependencies + self.config['measurements'].keys()

        app_list = {'chrome': 'com.android.chrome',
                    'opera': 'com.opera.browser',
                    'firefox': 'org.mozilla.firefox',
                    'trepn': 'com.quicinc.trepn'
                    }

        parsed_config['dependencies'] = ae(map_or_fail, dependencies, app_list, "%s is not found in the app list")

        parsed_config['scripts'] = {n: op.join(parsed_config['basedir'], p) for n, p in parsed_config['scripts'].items()}
        # for _, s in parsed_config['scripts'].items():
        #     parsed_config = ae(can_be_imported, s)

        parsed_config['devices'] = ae(get_device_ids, parsed_config['devices'])

        # parsed_config['measurements'] = []

        if self.errors:
            raise ConfigError(self.errors)
        return parsed_config


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


def get_value(obj, key, mandatory=False, default=None):
    try:
        return obj[key]
    except KeyError:
        if mandatory:
            raise ConfigError("Mandatory key '%s' is missing" % key)
        else:
            return default


def can_be_imported(script):
    # return
    try:
        find_module(op.splitext(script)[0])
        return True
    except ImportError:
        raise ConfigError("'%s' cannot be imported" % script)


def get_device_ids(names):
    try:
        ids = load_json(op.dirname(op.realpath(__file__)) + '/devices.json')
        return map_or_fail(names, ids, "Device %s is not found in devices.json")
    except (ValueError, IOError):
        sys.exit(1)


def map_or_fail(keys, dictionary, error_string):
    for k in filter(lambda d: not dictionary.get(d, None), keys):
        raise ConfigError(error_string % k)
    return {k: v for k, v in dictionary.items() if k in keys}


def test_apks(apks):
    for f in filter(lambda x: not op.isfile(x), apks):
        raise ConfigError("File %s not found" % f)
