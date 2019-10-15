# https://stackoverflow.com/a/25389715
import os.path as op

ROOT_DIR = op.dirname(op.abspath(__file__))
CONFIG_DIR = None
OUTPUT_DIR = None
BASE_OUTPUT_DIR = None
ORIGINAL_CONFIG_DIR = None


def paths_dict():
    return {'ROOT_DIR': ROOT_DIR, 'CONFIG_DIR': CONFIG_DIR, 'OUTPUT_DIR': OUTPUT_DIR,
            'ORIGINAL_CONFIG_DIR': ORIGINAL_CONFIG_DIR, 'BASE_OUTPUT_DIR': BASE_OUTPUT_DIR}
