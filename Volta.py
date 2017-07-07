import os.path as op
import time
from Measurement import Measurement, makedirs
import Adb


class Volta(Measurement):
    def __init__(self, basedir, config):
        super(Volta, self).__init__(basedir, config)
        # print('Volta initialized')

    def start_measurement(self, device_id):
        super(Volta, self).start_measurement(device_id)
        Adb.shell(device_id, 'dumpsys batterystats --reset')
        Adb.unplug(device_id)  # reset plugs the device back in

    def stop_measurement(self, device_id):
        super(Volta, self).stop_measurement(device_id)

    def get_results(self, device_id):
        output_dir = op.join(self.basedir, 'output/volta/')
        makedirs(output_dir)
        with open(op.join(output_dir, '%s_%s.txt' % (device_id, time.strftime('%Y.%m.%d_%H%M%S'))), 'w+') as f:
            f.write(Adb.shell(device_id, 'dumpsys batterystats'))
