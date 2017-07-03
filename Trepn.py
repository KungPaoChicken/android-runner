from Volta import Measurement
import xml.etree.cElementTree as cET
import Adb


class Trepn(Measurement):
    def __init__(self):
        super(Trepn, self).__init__()
        pass

    def build_config_files(self, device_id):
        # The XML module are not secure, but the file here are trusted
        # https://docs.python.org/2/library/xml.html#xml-vulnerabilities

        # Copy directory -> modify config
        preferences = cET.parse('trepn/com.quicinc.trepn_preferences.xml').getroot()
        config_file = '/sdcard/trepn/saved_preferences/some_preferences.pref'
        Adb.shell(device_id, 'am startservice com.quicinc.trepn/.TrepnService')
        # There is no way to know if this succeeded
        Adb.shell(device_id,
                  'am broadcast -a com.quicinc.trepn.load_preferences '
                  '-e com.quicinc.trepn.load_preferences_file "%s"' % config_file)

    def start_measurement(self, device_id):
        super(Trepn, self).start_measurement(device_id)
        Adb.shell(device_id, 'am broadcast -a com.quicinc.trepn.start_profiling')

    def stop_measurement(self, device_id):
        super(Trepn, self).stop_measurement(device_id)
        Adb.shell(device_id, 'am broadcast -a com.quicinc.trepn.stop_profiling')

    def get_results(self, device_id):
        Adb.shell(device_id, ' am broadcast -a com.quicinc.trepn.export_to_csv '
                             '-e com.quicinc.trepn.export_db_input_file "<existing_database_name>" '
                             '-e com.quicinc.trepn.export_csv_output_file "<output_csv_file>"')
