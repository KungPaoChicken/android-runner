from collections import OrderedDict
import json
import errno
import os


class ConfigError(Exception):
    pass


class FileNotFoundError(Exception):
    pass


class FileFormatError(Exception):
    pass


def load_json(path):
    try:
        with open(path, 'r') as f:
            try:
                return json.loads(f.read(), object_pairs_hook=OrderedDict)
            except ValueError:
                raise FileFormatError(path)
    except IOError as e:
        if e.errno == errno.ENOENT:
            raise FileNotFoundError(path)
        else:
            raise e


def makedirs(path):
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
