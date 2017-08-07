import os.path as op
import time

import lxml.etree as et

from util import load_json, makedirs
from Profiler import Profiler


class Trepn(Profiler):
    DEVICE_PATH = '/sdcard/trepn/'

    @staticmethod
    def dependencies():
        return ['com.quicinc.trepn']

    def __init__(self, config_dir, config):
        super(Trepn, self).__init__(config_dir, config)
        self.pref_dir = None
        self.remote_pref_dir = op.join(Trepn.DEVICE_PATH, 'saved_preferences/')
        self.build_preferences(config)

    def build_preferences(self, config):
        current_dir = op.dirname(op.realpath(__file__))
        # lxml is not the most secure parser, it is up to the user for valid configurations
        # https://docs.python.org/2/library/xml.html#xml-vulnerabilities
        self.pref_dir = op.join(self.config_dir, 'trepn.pref/')
        makedirs(self.pref_dir)

        preferences_file = et.parse(op.join(current_dir, 'trepn/preferences.xml'))
        if 'sample_interval' in config:
            for i in preferences_file.getroot().iter('int'):
                if i.get('name') == 'com.quicinc.preferences.general.profiling_interval':
                    i.set('value', str(config['sample_interval']))
        preferences_file.write(op.join(self.pref_dir, 'com.quicinc.trepn_preferences.xml'), encoding='utf-8',
                               xml_declaration=True, standalone=True)

        datapoints_file = et.parse(op.join(current_dir, 'trepn/data_points.xml'))
        dp_root = datapoints_file.getroot()
        data_points = load_json(op.join(current_dir, 'trepn/data_points.json'))
        for dp in config['data_points']:
            dp = str(data_points[dp])
            dp_root.append(et.Element('int', {'name': dp, 'value': dp}))
        datapoints_file.write(op.join(self.pref_dir, 'com.quicinc.preferences.saved_data_points.xml'), encoding='utf-8',
                              xml_declaration=True, standalone=True)

    def load(self, device):
        super(Trepn, self).load(device)
        device.shell('am startservice com.quicinc.trepn/.TrepnService')
        device.push(self.pref_dir, self.remote_pref_dir)
        # There is no way to know if the following succeeded
        device.shell('am broadcast -a com.quicinc.trepn.load_preferences '
                     '-e com.quicinc.trepn.load_preferences_file "%s"'
                     % op.join(self.remote_pref_dir, 'trepn.pref'))
        time.sleep(1)  # adb returns instantly, while the command takes time

    def start_profiling(self, device):
        super(Trepn, self).start_profiling(device)
        device.shell('am broadcast -a com.quicinc.trepn.start_profiling')

    def stop_profiling(self, device):
        super(Trepn, self).stop_profiling(device)
        device.shell('am broadcast -a com.quicinc.trepn.stop_profiling')

    def collect_results(self, device, path=None):
        # Gives the latest result
        super(Trepn, self).collect_results(device)
        newest_db = device.shell('ls -t %s | grep ".db" | head -n1' % Trepn.DEVICE_PATH).strip()
        csv_filename = '%s_%s.csv' % (device.id, op.splitext(newest_db)[0])
        if newest_db:
            device.shell('am broadcast -a com.quicinc.trepn.export_to_csv '
                         '-e com.quicinc.trepn.export_db_input_file "%s" '
                         '-e com.quicinc.trepn.export_csv_output_file "%s"' % (newest_db, csv_filename))
            time.sleep(1)  # adb returns instantly, while the command takes time
            output_dir = op.join(self.config_dir, 'output/trepn/')
            makedirs(output_dir)
            device.pull(op.join(Trepn.DEVICE_PATH, csv_filename), output_dir)
            time.sleep(1)  # adb returns instantly, while the command takes time
            # Delete the originals
            device.shell('rm %s' % op.join(Trepn.DEVICE_PATH, newest_db))
            device.shell('rm %s' % op.join(Trepn.DEVICE_PATH, csv_filename))

    def unload(self, device):
        super(Trepn, self).unload(device)
        device.shell('am stopservice com.quicinc.trepn/.TrepnService')
        device.shell('rm -r %s' % op.join(self.remote_pref_dir, 'trepn.pref'))
