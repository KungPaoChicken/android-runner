import os.path as op
import sys
import errno
import importlib
import json


class ConfigError(Exception):
    """Raised when a configuration error occurred"""
    pass


class ConfigParser:
    def __init__(self, config_file):
        self.config = None
        self.errors = []
        self.mandatory_keys = ['devices', 'type']
        self.defaults = {
            'replications': 1,
            'paths': [],
            'basedir': op.abspath(op.dirname(config_file)),
            'measurements': {},
            'scripts': {'setup': '',
                        'before_run': '',
                        'interaction': '',
                        'after_run': '',
                        'teardown': ''
                        },
            'time_between_run': 0
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
        parsed = {}
        ae = self.append_exceptions
        for k in self.mandatory_keys:
            parsed[k] = ae(get_value, self.config, k, mandatory=True)

        for k, v in self.defaults.items():
            parsed[k] = ae(get_value, self.config, k, default=self.defaults[k])

        parsed['devices'] = ae(get_device_ids, parsed['devices'])

        parsed['dependencies'] = []

        app_list = {
            'chrome': 'com.android.chrome',
            'opera': 'com.opera.browser',
            'firefox': 'org.mozilla.firefox'
        }

        if parsed['type'] == 'web':
            browsers = ae(get_value, self.config, 'browsers', mandatory=True)
            if not browsers:
                raise ConfigError("No browsers are given for a Web experiment")
            parsed['dependencies'] = parsed['dependencies'] + map(lambda b: app_list[b], browsers)

        if parsed['measurements']:
            parsed['measurements'] = {k.capitalize(): v for k, v in parsed['measurements'].items()}
            for tool in parsed['measurements'].keys():
                tool_module = getattr(importlib.import_module(tool), tool)
                dep = tool_module.get_dependencies()
                if dep:
                    parsed['dependencies'] = parsed['dependencies'] + dep

        parsed['scripts'] = {n: op.join(parsed['basedir'], p) for n, p in
                                    parsed['scripts'].items()}

        # parsed_config['measurements'] = []

        if self.errors:
            raise ConfigError(self.errors)
        return parsed


def load_json(path):
    try:
        with open(path, 'r') as f:
            try:
                return json.loads(f.read())
            except ValueError:
                raise ConfigError("%s is not a valid JSON file" % path)
    except IOError as e:
        if e.errno == errno.ENOENT:
            raise ConfigError("%s not found" % path)


def get_value(obj, key, mandatory=False, default=None):
    try:
        return obj[key]
    except KeyError:
        if mandatory:
            raise ConfigError("Mandatory key '%s' is missing" % key)
        else:
            return default


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
