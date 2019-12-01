import errno
import json
import os
import re
from collections import OrderedDict
from slugify import slugify


class ConfigError(Exception):
    pass


class FileNotFoundError(Exception):
    def __init__(self, filename):
        Exception.__init__(self, '[Errno %s] %s: \'%s\'' % (errno.ENOENT, os.strerror(errno.ENOENT), filename))


class FileFormatError(Exception):
    pass


def load_json(path):
    """Load a JSON file from path, and returns an ordered dictionary or throws exceptions on formatting errors"""
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
    """Create a directory on path if it does not exist"""
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


# https://stackoverflow.com/a/295466
# noinspection PyTypeChecker
def slugify_dir(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    return slugify(value)
    # import unicodedata
    # #value = value.decode('unicode-escape')
    # value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    # value = str(re.sub(r'[^\w\s-]', '', value).strip().lower())
    # return str(re.sub(r'[-\s]+', '-', value))
