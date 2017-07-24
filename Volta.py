import os.path as op
import time
from util import makedirs
from Profiler import Profiler
import Adb


class Volta(Profiler):
    def __init__(self, config_dir, config):
        super(Volta, self).__init__(config_dir, config)

    def start_profiling(self, device_id):
        super(Volta, self).start_profiling(device_id)
        Adb.shell(device_id, 'dumpsys batterystats --reset')
        Adb.unplug(device_id)  # reset plugs the device back in

    def stop_profiling(self, device_id):
        super(Volta, self).stop_profiling(device_id)

    def collect_results(self, device_id, path=None):
        super(Volta, self).collect_results(device_id)
        output_dir = op.join(self.config_dir, 'output/volta/')
        makedirs(output_dir)
        with open(op.join(output_dir, '%s_%s.txt' % (device_id, time.strftime('%Y.%m.%d_%H%M%S'))), 'w+') as f:
            f.write(Adb.shell(device_id, 'dumpsys batterystats'))
