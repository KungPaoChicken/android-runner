
class Trepn:
    def __init__(self, config):
        pass

    pass


def init(adb):
    adb.shell_command('am startservice com.quicinc.trepn/.TrepnService')


def start_profiling(adb, name):
    adb.shell_command('am broadcast -a com.quicinc.trepn.start_profiling -e com.quicinc.trepn.database_file "%s"' % name)


def stop_profiling(adb):
    adb.shell_command('am broadcast -a com.quicinc.trepn.stop_profiling')


def load_settings(adb):
    adb.shell_command('am broadcast -a com.quicinc.trepn.load_preferences –e com.quicinc.trepn.load_preferences_file')


def db_to_csv(adb, db_path, csv_path):
    adb.shell_command('am broadcast -a com.quicinc.trepn.export_to_csv -e com.quicinc.trepn.export_db_input_file "db_path" -e com.quicinc.trepn.export_csv_output_file "%s"' % (csv_path))
