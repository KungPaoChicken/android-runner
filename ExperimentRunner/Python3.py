import os.path as op
from imp import load_source

from .Script import Script


class Python3(Script):
    def __init__(self, path, timeout=0, logcat_regex=None):
        super(Python3, self).__init__(path, timeout, logcat_regex)
        try:
            self.module = load_source(op.splitext(op.basename(path))[0], op.join(path))
            self.logger.debug('Imported %s' % path)
        except ImportError:
            self.logger.error('Cannot import %s' % path)
            raise ImportError("Cannot import %s" % path)

    def execute_script(self, device, *args, **kwargs):
        super(Python3, self).execute_script(device, *args, **kwargs)
        return self.module.main(device, *args, **kwargs)
