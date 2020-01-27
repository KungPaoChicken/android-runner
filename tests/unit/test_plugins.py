import csv
import os.path as op
from os import chmod, listdir

import pytest
from mock import Mock, call, patch

import paths
from ExperimentRunner.Plugins.Android import Android, ConfigError as AndroidConfigError
from ExperimentRunner.Plugins.Batterystats import Batterystats, ConfigError as BsConfigError, \
    FileFormatError as BsFileFormatError, FileNotFoundError as BsFileNotFounError
from ExperimentRunner.Plugins.Profiler import Profiler
from ExperimentRunner.Plugins.Trepn import FileFormatError as TrFileFormatError, \
    FileNotFoundError as TrFileNotFoundError, Trepn


class TestPluginTemplate(object):
    @pytest.fixture()
    def profiler_template(self):
        return Profiler('config', [])

    @pytest.fixture()
    def mock_device(self):
        return Mock()

    def test_init(self):
        Profiler('config', [])

    def test_dependencies(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.dependencies()

    def test_load(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.load(mock_device)

    def test_start_profiling(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.start_profiling(mock_device)

    def test_stop_profiling(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.stop_profiling(mock_device)

    def test_collect_results(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.collect_results(mock_device)

    def test_unload(self, profiler_template, mock_device):
        with pytest.raises(NotImplementedError):
            profiler_template.unload(mock_device)

    def test_set_output(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.set_output('output/dir')

    def test_aggregate_subject(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.aggregate_subject()

    def test_aggregate_end(self, profiler_template):
        with pytest.raises(NotImplementedError):
            profiler_template.aggregate_end('data/dir', 'output/file.csv')


class TestAndroidPlugin(object):
    @pytest.fixture()
    def mock_device(self):
        return Mock()

    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    @pytest.fixture()
    def android_plugin(self):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem']}
        test_paths = {'path1': 'path/1'}
        return Android(test_config, test_paths)

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

    @staticmethod
    def get_dataset(filename):
        with open(filename, mode='r') as csv_file:
            dataset = set(map(tuple, csv.reader(csv_file)))
        return dataset

    @patch('ExperimentRunner.Plugins.Profiler.__init__')
    def test_android_plugin_succes(self, super_init):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        super_init.assert_called_once_with(test_config, test_paths)
        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 1
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]

    @patch('logging.Logger.warning')
    def test_android_plugin_invalid_datapoints(self, logger_warning):
        test_config = {'sample_interval': 1000, 'data_points': ['cpu', 'mem', 'invalid']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 1
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]
        logger_warning.assert_called_once_with("Invalid data points in config: ['invalid']")

    def test_android_plugin_default_interval(self):
        test_config = {'data_points': ['cpu', 'mem', 'invalid']}
        test_paths = {'path1': 'path/1'}
        ap = Android(test_config, test_paths)

        assert ap.output_dir == ''
        assert ap.paths == test_paths
        assert ap.profile is False
        assert ap.interval == 0
        assert ap.data_points == ['cpu', 'mem']
        assert ap.data == [['datetime', 'cpu', 'mem']]

    def test_get_cpu_usage(self, android_plugin, mock_device):
        mock_device.shell.return_value = '30% TOTAL: 21% user + 6.7% kernel + 1.2% iowait + 0.7% irq + 0.5% softirq'
        cpu_usage = android_plugin.get_cpu_usage(mock_device)

        assert cpu_usage == '30'
        mock_device.shell.assert_called_once_with('dumpsys cpuinfo | grep TOTAL')

    def test_get_cpu_usage_minus_in(self, android_plugin, mock_device):
        mock_device.shell.return_value = '30.-6% TOTAL: 21% user + 6.7% kernel + 1.2% iowait + 0.7% irq + 0.5% softirq'
        cpu_usage = android_plugin.get_cpu_usage(mock_device)

        assert cpu_usage == '30.6'
        mock_device.shell.assert_called_once_with('dumpsys cpuinfo | grep TOTAL')

    def test_get_mem_usage_no_app(self, android_plugin, mock_device):
        mock_device.shell.return_value = 'Used RAM: 1016104 kB (819528 used pss + 196576 kernel)'

        mem_usage = android_plugin.get_mem_usage(mock_device, None)

        assert mem_usage == "1016104"
        mock_device.shell.assert_called_once_with('dumpsys meminfo | grep Used')

    def test_get_mem_usage_app_found(self, android_plugin, mock_device):
        mock_device.shell.return_value = ' TOTAL    20411     7516    10228      980    36740    28499     8240   ' \
                                         'TOTAL:    20411      TOTAL SWAP (KB):      980'

        mem_usage = android_plugin.get_mem_usage(mock_device, 'com.google.android.calendar')

        assert mem_usage == "20411"
        mock_device.shell.assert_called_once_with('dumpsys meminfo com.google.android.calendar | grep TOTAL')

    def test_get_mem_usage_app_not_found(self, android_plugin, mock_device):
        mock_device.shell.side_effect = ['', 'No process found for: fake.app']

        with pytest.raises(Exception) as exception:
            android_plugin.get_mem_usage(mock_device, 'fake.app')

        assert str(exception.value) == 'Android Profiler: No process found for: fake.app'
        mock_device.shell.mock_calls[0]('dumpsys meminfo fake.app | grep TOTAL')
        mock_device.shell.mock_calls[1]('dumpsys meminfo fake.app')

    @patch('ExperimentRunner.Plugins.Android.Android.get_data')
    def test_start_profiling_with_app(self, get_data_mock, android_plugin, mock_device):
        kwargs = {'arg1': 1, 'app': 'test.app'}
        android_plugin.start_profiling(mock_device, **kwargs)

        assert android_plugin.profile is True
        get_data_mock.assert_called_once_with(mock_device, 'test.app')

    @patch('ExperimentRunner.Plugins.Android.Android.get_data')
    def test_start_profiling_without_app(self, get_data_mock, android_plugin, mock_device):
        kwargs = {'arg1': 1}
        android_plugin.start_profiling(mock_device, **kwargs)

        assert android_plugin.profile is True
        get_data_mock.assert_called_once_with(mock_device, None)

    @patch('timeit.default_timer')
    @patch('threading.Timer')
    @patch('ExperimentRunner.Plugins.Android.Android.get_cpu_usage')
    @patch('ExperimentRunner.Plugins.Android.Android.get_mem_usage')
    def test_get_data_all_points(self, get_mem_usage_mock, get_cpu_usage_mock, timer_mock, timeit_mock,
                                 android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        mock_timer_result = Mock()
        timer_mock.return_value = mock_timer_result
        android_plugin.profile = True
        android_plugin.interval = 200
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'cpu_usage', 'mem_usage']
        timer_mock.assert_called_once_with(100, android_plugin.get_data, args=(mock_device, 'app'))
        mock_timer_result.start.assert_called_once()

    @patch('timeit.default_timer')
    @patch('ExperimentRunner.Plugins.Android.Android.get_cpu_usage')
    @patch('ExperimentRunner.Plugins.Android.Android.get_mem_usage')
    def test_get_data_only_mem(self, get_mem_usage_mock, get_cpu_usage_mock, timeit_mock,
                               android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        android_plugin.data_points = ['mem']
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'mem_usage']

    @patch('timeit.default_timer')
    @patch('ExperimentRunner.Plugins.Android.Android.get_cpu_usage')
    @patch('ExperimentRunner.Plugins.Android.Android.get_mem_usage')
    def test_get_data_only_cpu(self, get_mem_usage_mock, get_cpu_usage_mock, timeit_mock,
                               android_plugin, mock_device):
        timeit_mock.side_effect = [100, 200]
        mock_device.shell.return_value = 'device_time'
        get_mem_usage_mock.return_value = "mem_usage"
        get_cpu_usage_mock.return_value = "cpu_usage"
        android_plugin.data_points = ['cpu']
        android_plugin.get_data(mock_device, 'app')

        assert android_plugin.data[1] == ['device_time', 'cpu_usage']

    def test_stop_profiling(self, android_plugin, mock_device):
        android_plugin.profile = True

        android_plugin.stop_profiling(mock_device)

        assert android_plugin.profile is False

    @patch('time.strftime')
    def test_collect_results(self, time_mock, android_plugin, mock_device, tmpdir, fixture_dir):
        test_output_dir = str(tmpdir)
        time_mock.return_value = 'time'
        mock_device.id = 'device_id'
        time_mock.return_value = 'experiment_time'
        android_plugin.data = self.csv_reader_to_table(op.join(fixture_dir, 'test_android_output.csv'))
        android_plugin.output_dir = test_output_dir

        android_plugin.collect_results(mock_device)

        assert op.isfile(op.join(test_output_dir, '{}_{}.csv'.format('device_id', 'experiment_time')))

        file_content_created = self.get_dataset(
            op.join(test_output_dir, '{}_{}.csv'.format('device_id', 'experiment_time')))
        file_content_original = self.get_dataset(op.join(fixture_dir, 'test_android_output.csv'))
        assert file_content_created == file_content_original

    def test_set_output(self, android_plugin):
        test_output_dir = "asdfgbfsdgbf/hjbdsfavav"
        android_plugin.set_output(test_output_dir)

        assert android_plugin.output_dir == test_output_dir

    def test_dependencies(self, android_plugin):
        assert android_plugin.dependencies() == []

    def test_load(self, android_plugin, mock_device):
        assert android_plugin.load(mock_device) is None

    def test_unload(self, android_plugin, mock_device):
        assert android_plugin.unload(mock_device) is None

    @patch('ExperimentRunner.Plugins.Android.Android.write_to_file')
    @patch('ExperimentRunner.Plugins.Android.Android.aggregate_android_subject')
    def test_aggregate_subject(self, aggregate_mock, write_to_file_mock, android_plugin):
        test_output_dir = 'test/output/dir'
        android_plugin.output_dir = test_output_dir
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        android_plugin.aggregate_subject()

        aggregate_mock.assert_called_once_with(test_output_dir)
        expected_list = list()
        expected_list.append(mock_rows)
        write_to_file_mock.assert_called_once_with(op.join(test_output_dir, 'Aggregated.csv'), expected_list)

    @patch('ExperimentRunner.Plugins.Android.Android.write_to_file')
    @patch('ExperimentRunner.Plugins.Android.Android.aggregate_final')
    def test_aggregate_end(self, aggregate_mock, write_to_file_mock, android_plugin):
        test_data_dir = 'test/output/dir'
        test_output_file = 'test/output/file.csv'
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        android_plugin.aggregate_end(test_data_dir, test_output_file)

        aggregate_mock.assert_called_once_with(test_data_dir)
        write_to_file_mock.assert_called_once_with(test_output_file, mock_rows)

    def test_aggregate_android_subject(self, android_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'android_subject_result')

        test_logs_aggregated = android_plugin.aggregate_android_subject(test_subject_log_dir)
        assert len(test_logs_aggregated) == 2
        assert test_logs_aggregated['android_cpu'] == 32.94186117467583
        assert test_logs_aggregated['android_mem'] == 1131976.3141113652

    @patch("ExperimentRunner.Plugins.Android.Android.aggregate_android_final")
    def test_aggregate_final_web(self, aggregate_mock, android_plugin, fixture_dir):
        test_struct_dir_web = op.join(fixture_dir, 'test_dir_struct', 'data_web')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = android_plugin.aggregate_final(test_struct_dir_web)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 4

    @patch("ExperimentRunner.Plugins.Android.Android.aggregate_android_final")
    def test_aggregate_final_native(self, aggregate_mock, android_plugin, fixture_dir):
        test_struct_dir_native = op.join(fixture_dir, 'test_dir_struct', 'data_native')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = android_plugin.aggregate_final(test_struct_dir_native)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 3

    def test_aggregate_android_final(self, android_plugin, fixture_dir):
        test_log_dir = op.join(fixture_dir, 'aggregate_final', 'android')
        aggregated_final_rows = android_plugin.aggregate_android_final(test_log_dir)

        assert len(aggregated_final_rows) == 2
        assert aggregated_final_rows['android_cpu'] == '19.017852474323064'
        assert aggregated_final_rows['android_mem'] == '1280213.4222222222'

    def test_list_subdir(self, android_plugin, fixture_dir):
        test_dir = op.join(fixture_dir, 'test_dir_struct')

        result_subdirs = android_plugin.list_subdir(test_dir)

        assert len(result_subdirs) == 2
        assert 'data_native' in result_subdirs
        assert 'data_web' in result_subdirs

    def test_write_to_file(self, android_plugin, tmpdir):
        tmp_file = op.join(str(tmpdir), 'test_output.csv')
        test_rows = [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value3', 'key2': 'value4'}]
        android_plugin.write_to_file(tmp_file, test_rows)

        assert op.isfile(tmp_file)
        assert self.csv_reader_to_table(tmp_file) == list(
            [['key2', 'key1'], ['value2', 'value1'], ['value4', 'value3']])

    def test_is_integer_not_int(self, android_plugin):
        with pytest.raises(AndroidConfigError) as except_result:
            android_plugin.is_integer("error")
        assert 'error is not an integer' in except_result.value

    def test_is_integer_too_small(self, android_plugin):
        with pytest.raises(AndroidConfigError) as except_result:
            android_plugin.is_integer(-1)
        assert '-1 should be equal or larger than 0' in except_result.value

    def test_is_integer_succes(self, android_plugin):
        assert android_plugin.is_integer(10) == 10


class TestBatterystatsPlugin(object):

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

    @staticmethod
    def file_content(filename):
        with open(filename, 'r') as myfile:
            content_string = myfile.read().replace('\n', '')
        return content_string

    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    @pytest.fixture()
    def mock_device(self):
        return Mock()

    @pytest.fixture()
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.is_integer')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.load_json')
    def batterystats_plugin(self, load_json_mock, is_integer_mock):
        config = {'cleanup': True}
        paths.CONFIG_DIR = 'test/path'
        paths.ORIGINAL_CONFIG_DIR = 'original/path'
        load_json_return_value = {'type': 'web', 'powerprofile_path': 'power/profile/path'}
        load_json_mock.return_value = load_json_return_value
        is_integer_mock.return_value = 0
        return Batterystats(config, paths.paths_dict())

    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.is_integer')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.load_json')
    @patch('ExperimentRunner.Plugins.Profiler.__init__')
    def test_init(self, super_mock, load_json_mock, is_integer_mock):
        config = {'cleanup': True}
        paths.CONFIG_DIR = 'test/path'
        paths.ORIGINAL_CONFIG_DIR = 'original/path'
        load_json_return_value = {'type': 'web', 'systrace_path': 'sys/trace/path',
                                  'powerprofile_path': 'power/profile/path', 'duration': 2000}
        load_json_mock.return_value = load_json_return_value
        is_integer_mock.return_value = 2000
        test_batterystats = Batterystats(config, paths.paths_dict())

        super_mock.assert_called_once_with(config, paths.paths_dict())
        load_json_mock.assert_called_once_with(op.join(paths.CONFIG_DIR, 'original/path'))
        assert test_batterystats.output_dir == ''
        assert test_batterystats.paths == paths.paths_dict()
        assert test_batterystats.profile is False
        assert test_batterystats.cleanup is True
        assert test_batterystats.type == 'web'
        assert test_batterystats.systrace == 'sys/trace/path'
        assert test_batterystats.powerprofile == 'power/profile/path'
        assert test_batterystats.duration == 2

    @patch('time.strftime')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.get_data')
    def test_start_profiling_native(self, get_data_mock, time_mock, batterystats_plugin, mock_device, tmpdir, capsys):
        batterystats_plugin.type = 'native'
        kwargs = {'app': 'testapp1'}
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device, **kwargs)
        capsys.readouterr()  # Catch print

        mock_device.shell.assert_called_once_with('dumpsys batterystats --reset')
        get_data_mock.assert_called_once_with(mock_device, 'testapp1')
        assert batterystats_plugin.profile is True

    @patch('time.strftime')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.get_data')
    def test_start_profiling_web(self, get_data_mock, time_mock, batterystats_plugin, mock_device, tmpdir, capsys):
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)

        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        mock_device.shell.assert_called_once_with('dumpsys batterystats --reset')
        get_data_mock.assert_called_once_with(mock_device, 'com.android.chrome')
        assert batterystats_plugin.profile is True

    @patch('time.strftime')
    @patch('subprocess.Popen')
    def test_get_data(self, popen_mock, time_mock, batterystats_plugin, mock_device, tmpdir, capsys):
        mock_device.id = '123'
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)

        batterystats_plugin.start_profiling(mock_device)  # start profiling call get_data

        capsys.readouterr()  # Catch print
        popen_mock.assert_called_once_with('systrace freq idle -e 123 -a com.android.chrome -t 5 -o {}'
                                           .format(op.join(str(tmpdir), 'systrace_123_strftime.html')), shell=True)

    def test_stop_profiling(self, batterystats_plugin, mock_device):
        batterystats_plugin.profile = True

        batterystats_plugin.stop_profiling(mock_device)

        assert batterystats_plugin.profile is False

    @patch('time.strftime')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.get_data')
    def test_pull_logcat(self, get_data_mock, time_mock, batterystats_plugin, mock_device, tmpdir, capsys):
        get_data_mock.return_value = None
        # set global variables
        mock_device.id = '123'
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        batterystats_plugin.pull_logcat(mock_device)

        expected_calls = [call.shell('logcat -f /mnt/sdcard/logcat.txt -d'),
                          call.pull('/mnt/sdcard/logcat.txt', op.join(str(tmpdir), 'logcat_123_strftime.txt')),
                          call.shell('rm -f /mnt/sdcard/logcat.txt')]
        assert mock_device.mock_calls[1:] == expected_calls

    @patch('ExperimentRunner.Plugins.BatterystatsParser.parse_batterystats')
    @patch('time.strftime')
    @patch('subprocess.Popen')
    def test_get_batterystats_results(self, popen_mock, time_mock, parse_mock, batterystats_plugin, mock_device, tmpdir,
                                      capsys):
        # set global variables
        popen_return_value = Mock()
        popen_mock.return_value = popen_return_value
        parse_return_value = Mock()
        parse_mock.return_value = parse_return_value
        mock_device.id = '123'
        mock_device.shell.return_value = 'dumpsys_return_value'
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        parse_return_value = Mock()
        parse_mock.return_value = parse_return_value

        get_batterystats_result = batterystats_plugin.get_batterystats_results(mock_device)

        assert get_batterystats_result == parse_return_value
        assert mock_device.mock_calls[1] == call.shell('dumpsys batterystats --history')
        assert self.file_content(
            op.join(str(tmpdir), 'batterystats_history_123_strftime.txt')) == 'dumpsys_return_value'
        parse_mock.assert_called_once_with('com.android.chrome',
                                           op.join(str(tmpdir), 'batterystats_history_123_strftime.txt'),
                                           batterystats_plugin.powerprofile)

    def test_get_consumed_joules(self, batterystats_plugin, mock_device):
        dumpsys_volt = '0 (1) 091 status=discharging health=good plug=none temp=260 volt=4246 +running +wake_lock ' \
                       '+wifi_radio +screen phone_signal_strength=great brightness=bright +wifi_running +wifi ' \
                       'wifi_signal_strength=4 wifi_suppl=completed +4m07s375ms (2) 090 volt=4225 +16m24s239ms (3) ' \
                       '089 volt=4195'
        dumpsys_charge = '3450, Computed drain: 150, actual drain: 104-138'
        mock_device.shell.side_effect = [dumpsys_charge, dumpsys_volt]
        calculated_j_consumed = batterystats_plugin.get_consumed_joules(mock_device)
        assert calculated_j_consumed == 2292.84

    @patch('os.remove')
    def test_cleanup_logs_false(self, os_remove_mock, batterystats_plugin):
        batterystats_plugin.cleanup = False

        batterystats_plugin.cleanup_logs()

        assert os_remove_mock.call_count == 0

    @patch('time.strftime')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.get_data')
    @patch('os.remove')
    def test_cleanup_logs_true(self, os_remove_mock, get_data_mock, time_mock, batterystats_plugin, mock_device, tmpdir,
                               capsys):
        get_data_mock.return_value = None
        batterystats_plugin.cleanup = True
        # set global variables
        mock_device.id = '123'
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        batterystats_plugin.cleanup_logs()

        assert os_remove_mock.call_count == 3
        assert call(op.join(str(tmpdir), 'systrace_123_strftime.html')) in os_remove_mock.mock_calls
        assert call(op.join(str(tmpdir), 'logcat_123_strftime.txt')) in os_remove_mock.mock_calls
        assert call(op.join(str(tmpdir), 'batterystats_history_123_strftime.txt')) in os_remove_mock.mock_calls

    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.cleanup_logs")
    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.write_results")
    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.get_systrace_results")
    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.get_consumed_joules")
    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.get_batterystats_results")
    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.pull_logcat")
    def test_collect_results(self, pull_logcat_mock, get_batterystats_results_mock, get_consumed_joules_mock,
                             get_systrace_results_mock, write_results_mock, cleanup_logs_mock, batterystats_plugin,
                             mock_device):
        batterystats_result_mock = Mock()
        get_batterystats_results_mock.return_value = batterystats_result_mock
        consumed_joules_mock = Mock()
        get_consumed_joules_mock.return_value = consumed_joules_mock
        systrace_result_mock = Mock()
        get_systrace_results_mock.return_value = systrace_result_mock
        mock_manager = Mock()
        mock_manager.attach_mock(pull_logcat_mock, 'pull_logcat_managed')
        mock_manager.attach_mock(get_batterystats_results_mock, 'get_batterystats_results_managed')
        mock_manager.attach_mock(get_consumed_joules_mock, 'get_consumed_joules_managed')
        mock_manager.attach_mock(get_systrace_results_mock, 'get_systrace_results_managed')
        mock_manager.attach_mock(write_results_mock, 'write_results_managed')
        mock_manager.attach_mock(cleanup_logs_mock, 'cleanup_logs_managed')

        batterystats_plugin.collect_results(mock_device)

        expected_calls = [call.pull_logcat_managed(mock_device),
                          call.get_batterystats_results_managed(mock_device),
                          call.get_consumed_joules_managed(mock_device),
                          call.get_systrace_results_managed(mock_device),
                          call.write_results_managed(batterystats_result_mock, systrace_result_mock,
                                                     consumed_joules_mock),
                          call.cleanup_logs_managed()]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Plugins.BatterystatsParser.parse_systrace')
    @patch('time.strftime')
    @patch('subprocess.Popen')
    def test_get_systrace_result(self, popen_mock, time_mock, parse_mock, batterystats_plugin, mock_device, tmpdir,
                                 capsys):
        # set global variables
        popen_return_value = Mock()
        popen_mock.return_value = popen_return_value
        parse_return_value = Mock()
        parse_mock.return_value = parse_return_value
        mock_device.id = '123'
        mock_device.shell.return_value = 8
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        parse_return_value = Mock()
        parse_mock.return_value = parse_return_value

        get_sysrace_result = batterystats_plugin.get_systrace_results(mock_device)

        assert get_sysrace_result == parse_return_value
        popen_return_value.wait.assert_called_once()
        parse_mock.assert_called_once_with('com.android.chrome', op.join(str(tmpdir), 'systrace_123_strftime.html'),
                                           op.join(str(tmpdir), 'logcat_123_strftime.txt'),
                                           op.join(str(tmpdir), 'batterystats_history_123_strftime.txt'),
                                           batterystats_plugin.powerprofile, 8)

    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.get_data')
    @patch('time.strftime')
    def test_write_results(self, time_mock, get_data, batterystats_plugin, mock_device, tmpdir, capsys):
        get_data.return_value = None
        mock_device.id = '123'
        mock_device.shell.return_value = 8
        batterystats_plugin.type = 'web'
        time_mock.return_value = 'strftime'
        batterystats_plugin.output_dir = str(tmpdir)
        batterystats_plugin.start_profiling(mock_device)
        capsys.readouterr()  # Catch print

        batterystats_results = ['0,13.395,13.395,screen bright,12.309721026',
                                '0,13.395,13.395,wifi running,0.1838313726']
        systrace_results = ['0.0,5.985252,5.985252,core 0 cpu_idle start,0.092214777564',
                            '0.0,6.00117999999,6.00117999999,core 1 cpu_idle start,0.0924601802599']
        energy_consumed_j = 2292.84

        batterystats_plugin.write_results(batterystats_results, systrace_results, energy_consumed_j)
        expected_joule_result_file = op.join(batterystats_plugin.output_dir, 'Joule_results_123_strftime.csv')
        expected_result_file = op.join(batterystats_plugin.output_dir, 'results_123_strftime.csv')
        expected_joule_result_file_content = [['Joule_calculated'], ['2292.84']]
        expected_result_file_content = [['Start Time (Seconds)', 'End Time (Seconds)', 'Duration (Seconds)',
                                         'Component', 'Energy Consumption (Joule)'], ['0', '13.395', '13.395',
                                                                                      'screen bright', '12.309721026'],
                                        ['0', '13.395', '13.395', 'wifi running',
                                         '0.1838313726'], ['0.0', '5.985252', '5.985252', 'core 0 cpu_idle start',
                                                           '0.092214777564'], ['0.0', '6.00117999999', '6.00117999999',
                                                                               'core 1 cpu_idle start',
                                                                               '0.0924601802599']]
        assert op.isfile(expected_joule_result_file)
        assert self.csv_reader_to_table(expected_joule_result_file) == expected_joule_result_file_content
        assert op.isfile(expected_result_file)
        assert self.csv_reader_to_table(expected_result_file) == expected_result_file_content

    def test_set_output(self, batterystats_plugin):
        test_output_dir = "asdfgbfsdgbf/hjbdsfavav"
        batterystats_plugin.set_output(test_output_dir)

        assert batterystats_plugin.output_dir == test_output_dir

    def test_dependencies(self, batterystats_plugin):
        assert batterystats_plugin.dependencies() == []

    def test_load(self, batterystats_plugin, mock_device):
        assert batterystats_plugin.load(mock_device) is None

    def test_unload(self, batterystats_plugin, mock_device):
        assert batterystats_plugin.unload(mock_device) is None

    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.write_to_file')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.aggregate_battery_subject')
    def test_aggregate_subject(self, aggregate_mock, write_to_file_mock, batterystats_plugin):
        test_output_dir = 'test/output/dir'
        batterystats_plugin.output_dir = test_output_dir
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        batterystats_plugin.aggregate_subject()

        expected_list = list()
        expected_list.append(mock_rows)
        write_to_file_mock.assert_called_once_with(op.join(test_output_dir, 'Aggregated.csv'), expected_list)

    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.write_to_file')
    @patch('ExperimentRunner.Plugins.Batterystats.Batterystats.aggregate_final')
    def test_aggregate_end(self, aggregate_mock, write_to_file_mock, batterystats_plugin):
        test_data_dir = 'test/output/dir'
        test_output_file = 'test/output/file.csv'
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        batterystats_plugin.aggregate_end(test_data_dir, test_output_file)

        aggregate_mock.assert_called_once_with(test_data_dir)
        write_to_file_mock.assert_called_once_with(test_output_file, mock_rows)

    def test_aggregate_battery_subject_joules_false(self, batterystats_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'batterystats_subject_result')

        test_logs_aggregated = batterystats_plugin.aggregate_battery_subject(test_subject_log_dir, False)

        assert len(test_logs_aggregated) == 0

    def test_aggregate_battery_subject_joules_true(self, batterystats_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'batterystats_subject_result')

        test_logs_aggregated = batterystats_plugin.aggregate_battery_subject(test_subject_log_dir, True)

        assert len(test_logs_aggregated) == 1
        assert round(test_logs_aggregated['batterystats_Joule_calculated'],6) == 101.227896

    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.aggregate_battery_final")
    def test_aggregate_final_web(self, aggregate_mock, batterystats_plugin, fixture_dir):
        test_struct_dir_web = op.join(fixture_dir, 'test_dir_struct', 'data_web')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = batterystats_plugin.aggregate_final(test_struct_dir_web)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 4

    @patch("ExperimentRunner.Plugins.Batterystats.Batterystats.aggregate_battery_final")
    def test_aggregate_final_native(self, aggregate_mock, batterystats_plugin, fixture_dir):
        test_struct_dir_native = op.join(fixture_dir, 'test_dir_struct', 'data_native')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = batterystats_plugin.aggregate_final(test_struct_dir_native)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 3

    def test_aggregate_battery_final(self, batterystats_plugin, fixture_dir):
        test_log_dir = op.join(fixture_dir, 'aggregate_final', 'batterystats')
        aggregated_final_rows = batterystats_plugin.aggregate_battery_final(test_log_dir)

        assert len(aggregated_final_rows) == 1
        assert aggregated_final_rows['batterystats_Joule_calculated'] == '101.227896'

    def test_list_subdir(self, batterystats_plugin, fixture_dir):
        test_dir = op.join(fixture_dir, 'test_dir_struct')

        result_subdirs = batterystats_plugin.list_subdir(test_dir)

        assert len(result_subdirs) == 2
        assert 'data_native' in result_subdirs
        assert 'data_web' in result_subdirs

    def test_write_to_file(self, batterystats_plugin, tmpdir):
        tmp_file = op.join(str(tmpdir), 'test_output.csv')
        test_rows = [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value3', 'key2': 'value4'}]
        batterystats_plugin.write_to_file(tmp_file, test_rows)

        assert op.isfile(tmp_file)
        assert self.csv_reader_to_table(tmp_file) == list(
            [['key2', 'key1'], ['value2', 'value1'], ['value4', 'value3']])

    def test_is_integer_not_int(self, batterystats_plugin):
        with pytest.raises(BsConfigError) as except_result:
            batterystats_plugin.is_integer("error")
        assert 'error is not an integer' in except_result.value

    def test_is_integer_too_small(self, batterystats_plugin):
        with pytest.raises(BsConfigError) as except_result:
            batterystats_plugin.is_integer(-1)
        assert '-1 should be equal or larger than 0' in except_result.value

    def test_is_integer_succes(self, batterystats_plugin):
        assert batterystats_plugin.is_integer(10) == 10

    def test_load_json_succes(self, batterystats_plugin, fixture_dir):
        config = batterystats_plugin.load_json(op.join(fixture_dir, 'test_config.json'))
        assert config['type'] == 'web'
        assert config['devices'] == ['nexus6p']
        assert config['randomization'] == 'False'
        assert config['replications'] == 3

    def test_load_json_file_format_error(self, batterystats_plugin, fixture_dir):
        with pytest.raises(BsFileFormatError) as except_result:
            batterystats_plugin.load_json(op.join(fixture_dir, 'test_progress.xml'))
        assert op.join(fixture_dir, 'test_progress.xml') in except_result.value

    def test_load_json_file_file_not_found(self, batterystats_plugin, fixture_dir):
        with pytest.raises(BsFileNotFounError) as except_result:
            batterystats_plugin.load_json(op.join(fixture_dir, 'fake_file.json'))
        assert "FileNotFoundError" in except_result.typename

    def test_load_json_file_permission_denied(self, tmpdir, batterystats_plugin):
        tmp_file = op.join(str(tmpdir), 'tmp_file.txt')
        open(tmp_file, "w+")
        chmod(tmp_file, 0o222)
        with pytest.raises(IOError) as except_result:
            batterystats_plugin.load_json(tmp_file)
        assert "Permission denied" in except_result.value


class TestTrepnPlugin(object):

    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    @pytest.fixture()
    def mock_device(self):
        return Mock()

    @pytest.fixture()
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.build_preferences')
    @patch('ExperimentRunner.Plugins.Profiler.__init__')
    def trepn_plugin(self, super_mock, build_preferences_mock):
        super_mock.return_value = None
        build_preferences_mock.return_value = None
        config_mock = Mock()
        test_paths = paths.paths_dict()
        return Trepn(config_mock, test_paths)

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

    @staticmethod
    def file_content(filename):
        with open(filename, 'r') as myfile:
            content_string = myfile.read()
        return content_string

    @patch('ExperimentRunner.Plugins.Trepn.Trepn.build_preferences')
    @patch('ExperimentRunner.Plugins.Profiler.__init__')
    def test_int(self, super_mock, build_preferences_mock):
        config_mock = Mock()
        test_paths = paths.paths_dict()
        trepn_plugin = Trepn(config_mock, test_paths)

        super_mock.assert_called_once_with(config_mock, test_paths)
        assert trepn_plugin.output_dir == ''
        assert trepn_plugin.paths == paths.paths_dict()
        assert trepn_plugin.pref_dir is None
        assert trepn_plugin.remote_pref_dir == op.join(trepn_plugin.DEVICE_PATH, 'saved_preferences/')
        build_preferences_mock.assert_called_once_with(config_mock)

    def test_dependencies(self, trepn_plugin):
        assert trepn_plugin.dependencies() == ['com.quicinc.trepn']

    def test_build_preferences(self, trepn_plugin, tmpdir, fixture_dir):
        test_params = {'sample_interval': 300, 'data_points': ['battery_power', 'mem_usage']}
        trepn_plugin.paths['OUTPUT_DIR'] = str(tmpdir)

        trepn_plugin.build_preferences(test_params)

        expected_dir = op.join(trepn_plugin.paths['OUTPUT_DIR'], 'trepn.pref/')
        expected_pref_file = op.join(expected_dir, 'com.quicinc.trepn_preferences.xml')
        expected_dp_file = op.join(expected_dir, 'com.quicinc.preferences.saved_data_points.xml')
        assert trepn_plugin.pref_dir == expected_dir
        assert op.isdir(expected_dir)
        assert op.isfile(expected_pref_file)
        assert op.isfile(expected_dp_file)
        assert self.file_content(expected_pref_file) == self.file_content(op.join(fixture_dir, 'exp_trepn_pref.xml'))
        assert self.file_content(expected_dp_file) == self.file_content(op.join(fixture_dir, 'exp_saved_dp.xml'))

    @patch('time.sleep')
    def test_load(self, sleep_mock, trepn_plugin, mock_device, tmpdir):
        test_pref_dir = str(tmpdir)
        trepn_plugin.pref_dir = test_pref_dir
        mock_manager = Mock()
        mock_manager.attach_mock(sleep_mock, 'sleep_managed')
        mock_manager.attach_mock(mock_device, 'device_managed')

        trepn_plugin.load(mock_device)

        expected_calls = [call.device_managed.push(test_pref_dir, trepn_plugin.remote_pref_dir),
                          call.device_managed.launch_package('com.quicinc.trepn'),
                          call.sleep_managed(5),
                          call.device_managed.shell('am broadcast -a com.quicinc.trepn.load_preferences '
                                                    '-e com.quicinc.trepn.load_preferences_file "%s"'
                                                    % op.join(trepn_plugin.remote_pref_dir, 'trepn.pref')),
                          call.sleep_managed(1),
                          call.device_managed.force_stop('com.quicinc.trepn'),
                          call.sleep_managed(2),
                          call.device_managed.shell('am startservice com.quicinc.trepn/.TrepnService')]
        assert mock_manager.mock_calls == expected_calls

    def test_start_profiling(self, trepn_plugin, mock_device):
        trepn_plugin.start_profiling(mock_device)

        mock_device.shell.assert_called_once_with('am broadcast -a com.quicinc.trepn.start_profiling')

    def test_stop_profiling(self, trepn_plugin, mock_device):
        trepn_plugin.stop_profiling(mock_device)

        mock_device.shell.assert_called_once_with('am broadcast -a com.quicinc.trepn.stop_profiling')

    @patch('time.sleep')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.filter_results')
    def test_collect_results(self, filter_results_mock, sleep_mock, trepn_plugin, mock_device, tmpdir):
        tmpdir_str = str(tmpdir)
        trepn_plugin.output_dir = tmpdir_str
        mock_device.id = '123'
        mock_device.shell.return_value = 'Trepn_2019.08.21_224812.db'
        mock_manager = Mock()
        mock_manager.attach_mock(mock_device, 'device_managed')
        mock_manager.attach_mock(sleep_mock, 'sleep_managed')
        mock_manager.attach_mock(filter_results_mock, 'filter_managed')

        trepn_plugin.collect_results(mock_device)

        expected_calls = [call.device_managed.shell(r'ls /sdcard/trepn/ | grep "\.db$"'),
                          call.device_managed.shell('am broadcast -a com.quicinc.trepn.export_to_csv '
                                                    '-e com.quicinc.trepn.export_db_input_file '
                                                    '"Trepn_2019.08.21_224812.db" '
                                                    '-e com.quicinc.trepn.export_csv_output_file '
                                                    '"123_Trepn_2019.08.21_224812.csv"'),
                          call.sleep_managed(1),
                          call.device_managed.pull(op.join(trepn_plugin.DEVICE_PATH, '123_Trepn_2019.08.21_224812.csv')
                                                   , tmpdir_str),
                          call.sleep_managed(1),
                          call.device_managed.shell(
                              'rm %s' % op.join(trepn_plugin.DEVICE_PATH, 'Trepn_2019.08.21_224812.db')),
                          call.device_managed.shell(
                              'rm %s' % op.join(trepn_plugin.DEVICE_PATH, '123_Trepn_2019.08.21_224812.csv')),
                          call.filter_managed(op.join(tmpdir_str, '123_Trepn_2019.08.21_224812.csv'))]
        assert mock_manager.mock_calls == expected_calls

    def test_read_csv(self, trepn_plugin, fixture_dir):
        test_file = op.join(fixture_dir, 'test_trepn_data_to_filter.csv')
        assert trepn_plugin.read_csv(test_file) == self.csv_reader_to_table(test_file)

    @patch('ExperimentRunner.Plugins.Trepn.Trepn.write_list_to_file')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.filter_data')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.read_csv')
    def test_filter_result(self, read_csv_mock, filter_data_mock, write_mock, trepn_plugin, tmpdir, fixture_dir):
        test_filename = op.join(str(tmpdir), 'test_file.txt')
        test_data = self.csv_reader_to_table(op.join(fixture_dir, 'test_output_orig_trepn.csv'))
        read_csv_mock.return_value = test_data
        filter_data_result = Mock()
        filter_data_mock.return_value = filter_data_result
        statistic_to_filter_out = ['332', '328']
        trepn_plugin.data_points = statistic_to_filter_out

        trepn_plugin.filter_results(test_filename)
        read_csv_mock.assert_called_once_with(test_filename)
        write_mock.assert_called_once_with(test_filename, filter_data_result)
        filter_data_mock.assert_called_once_with(['Battery Power*', 'Memory Usage'], self.csv_reader_to_table(
            op.join(fixture_dir, 'test_trepn_data_to_filter.csv')))

    def test_write_list_to_file(self, trepn_plugin, tmpdir):
        test_filename = op.join(str(tmpdir), 'test_file.txt')
        test_data = [[], [], []]
        for i in range(0, 40):
            test_data[0].append('column_%s' % i)
            test_data[1].append('column_%s' % i)
            test_data[2].append('column_%s' % i)

        trepn_plugin.write_list_to_file(test_filename, test_data)

        assert op.isfile(test_filename)
        assert self.csv_reader_to_table(test_filename) == test_data

    @patch('ExperimentRunner.Plugins.Trepn.Trepn.filter_columns')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.get_wanted_columns')
    def test_filter_data(self, get_wanted_columns_mock, filter_columns_mock, trepn_plugin):
        wanted_statistics_mock = Mock()
        data_mock = Mock()
        data_mock_list = [data_mock]
        wanted_columns_mock = Mock()
        get_wanted_columns_mock.return_value = wanted_columns_mock
        filtered_data_mock = Mock()
        filter_columns_mock.return_value = filtered_data_mock

        filtered_data = trepn_plugin.filter_data(wanted_statistics_mock, data_mock_list)

        get_wanted_columns_mock.assert_called_once_with(wanted_statistics_mock, data_mock)
        filter_columns_mock.assert_called_once_with(wanted_columns_mock, data_mock_list)
        assert filtered_data == filtered_data_mock

    def test_filter_columns(self, trepn_plugin):
        wanted_columns = [6, 7, 16, 17, 30, 31]
        data_columns = [[], []]
        for i in range(0, 40):
            data_columns[0].append('column_%s' % i)
            data_columns[1].append('column_%s' % i)
        remaining_data = trepn_plugin.filter_columns(wanted_columns, data_columns)
        assert len(remaining_data[0]) == len(remaining_data[1]) == 6
        for row in remaining_data:
            column_count = 0
            for column in row:
                assert column == 'column_%s' % wanted_columns[column_count]
                column_count += 1

    def test_get_wanted_columns(self, trepn_plugin):
        test_wanted_statistics = ['value_3', 'value_8', 'value_15']
        test_header_row = []
        for i in range(0, 30):
            test_header_row.append('Time [%s]' % i)
            test_header_row.append('value_%s [tst]' % i)

        result_columns = trepn_plugin.get_wanted_columns(test_wanted_statistics, test_header_row)

        assert result_columns == [6, 7, 16, 17, 30, 31]

    def test_unload(self, trepn_plugin, mock_device):
        trepn_plugin.unload(mock_device)

        expected_calls = [call.shell('am stopservice com.quicinc.trepn/.TrepnService'),
                          call.shell('rm -r %s' % op.join(trepn_plugin.remote_pref_dir, 'trepn.pref'))]
        assert mock_device.mock_calls == expected_calls

    def test_set_output(self, trepn_plugin, tmpdir):
        test_output_dir = str(tmpdir)

        trepn_plugin.set_output(test_output_dir)

        assert trepn_plugin.output_dir == test_output_dir

    @patch('ExperimentRunner.Plugins.Trepn.Trepn.write_to_file')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.aggregate_trepn_subject')
    def test_aggregate_subject(self, aggregate_mock, write_to_file_mock, trepn_plugin):
        test_output_dir = 'test/output/dir'
        trepn_plugin.output_dir = test_output_dir
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        trepn_plugin.aggregate_subject()

        aggregate_mock.assert_called_once_with(test_output_dir)
        expected_list = list()
        expected_list.append(mock_rows)
        write_to_file_mock.assert_called_once_with(op.join(test_output_dir, 'Aggregated.csv'), expected_list)

    @patch('ExperimentRunner.Plugins.Trepn.Trepn.write_to_file')
    @patch('ExperimentRunner.Plugins.Trepn.Trepn.aggregate_final')
    def test_aggregate_end(self, aggregate_mock, write_to_file_mock, trepn_plugin):
        test_data_dir = 'test/output/dir'
        test_output_file = 'test/output/file.csv'
        mock_rows = Mock()
        aggregate_mock.return_value = mock_rows

        trepn_plugin.aggregate_end(test_data_dir, test_output_file)

        aggregate_mock.assert_called_once_with(test_data_dir)
        write_to_file_mock.assert_called_once_with(test_output_file, mock_rows)

    def test_write_to_file(self, trepn_plugin, tmpdir):
        tmp_file = op.join(str(tmpdir), 'test_output.csv')
        test_rows = [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value3', 'key2': 'value4'}]
        trepn_plugin.write_to_file(tmp_file, test_rows)

        assert op.isfile(tmp_file)
        assert self.csv_reader_to_table(tmp_file) == list(
            [['key2', 'key1'], ['value2', 'value1'], ['value4', 'value3']])

    def test_aggregate_trepn_subject(self, trepn_plugin, fixture_dir):
        test_subject_log_dir = op.join(fixture_dir, 'trepn_subject_result')

        test_logs_aggregated = trepn_plugin.aggregate_trepn_subject(test_subject_log_dir)

        assert len(test_logs_aggregated) == 4
        assert test_logs_aggregated['Battery Power* [uW] (Delta)'] == 1230355.5
        assert test_logs_aggregated['Battery Power* [uW] (Raw)'] == 2301245.088235294
        assert test_logs_aggregated['Battery Temperature [1/10 C]'] == 300.0
        assert test_logs_aggregated['Memory Usage [KB]'] == 2650836.2352941176

    @patch("ExperimentRunner.Plugins.Trepn.Trepn.aggregate_trepn_final")
    def test_aggregate_final_web(self, aggregate_mock, trepn_plugin, fixture_dir):
        test_struct_dir_web = op.join(fixture_dir, 'test_dir_struct', 'data_web')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = trepn_plugin.aggregate_final(test_struct_dir_web)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 4

    @patch("ExperimentRunner.Plugins.Trepn.Trepn.aggregate_trepn_final")
    def test_aggregate_final_native(self, aggregate_mock, trepn_plugin, fixture_dir):
        test_struct_dir_native = op.join(fixture_dir, 'test_dir_struct', 'data_native')
        aggregate_mock.side_effect = [{'avg': 1}, {'avg': 2}]

        final_aggregated_result = trepn_plugin.aggregate_final(test_struct_dir_native)

        assert len(final_aggregated_result) == 2
        assert len(final_aggregated_result[0]) == 3

    def test_aggregate_trepn_final(self, trepn_plugin, fixture_dir):
        test_log_dir = op.join(fixture_dir, 'aggregate_final', 'trepn')
        aggregated_final_rows = trepn_plugin.aggregate_trepn_final(test_log_dir)

        assert len(aggregated_final_rows) == 4
        assert aggregated_final_rows['Battery Power* [uW] (Delta)'] == '1230355.5'
        assert aggregated_final_rows['Battery Power* [uW] (Raw)'] == '2301245.088235294'
        assert aggregated_final_rows['Battery Temperature [1/10 C]'] == '300.0'
        assert aggregated_final_rows['Memory Usage [KB]'] == '2650836.2352941176'

    def test_list_subdir(self, trepn_plugin, fixture_dir):
        test_dir = op.join(fixture_dir, 'test_dir_struct')

        result_subdirs = trepn_plugin.list_subdir(test_dir)

        assert len(result_subdirs) == 2
        assert 'data_native' in result_subdirs
        assert 'data_web' in result_subdirs

    def test_makedirs_success(self, tmpdir, trepn_plugin):
        dir_path = op.join(str(tmpdir), 'test1')
        assert op.isdir(dir_path) is False
        trepn_plugin.makedirs(dir_path)
        assert op.isdir(dir_path) is True

    def test_makedirs_fail_already_exist(self, tmpdir, trepn_plugin):
        dir_path = op.join(str(tmpdir), 'test1')
        assert op.isdir(dir_path) is False
        trepn_plugin.makedirs(dir_path)
        trepn_plugin.makedirs(dir_path)
        assert op.isdir(dir_path) is True
        files_in_path = [f for f in listdir(str(tmpdir)) if op.isdir(op.join(str(tmpdir), f))]

        assert len(files_in_path) == 1

    def test_makedirs_fail(self, tmpdir, trepn_plugin):
        chmod(str(tmpdir), 0o444)
        dir_path = op.join(str(tmpdir), 'test2')
        assert op.isdir(dir_path) is False
        with pytest.raises(OSError) as except_result:
            trepn_plugin.makedirs(dir_path)
        assert "Permission denied" in except_result.value
        assert op.isdir(dir_path) is False

    def test_load_json_succes(self, trepn_plugin, fixture_dir):
        config = trepn_plugin.load_json(op.join(fixture_dir, 'test_config.json'))
        assert config['type'] == 'web'
        assert config['devices'] == ['nexus6p']
        assert config['randomization'] == 'False'
        assert config['replications'] == 3

    def test_load_json_file_format_error(self, trepn_plugin, fixture_dir):
        with pytest.raises(TrFileFormatError) as except_result:
            trepn_plugin.load_json(op.join(fixture_dir, 'test_progress.xml'))
        assert op.join(fixture_dir, 'test_progress.xml') in except_result.value

    def test_load_json_file_file_not_found(self, trepn_plugin, fixture_dir):
        with pytest.raises(TrFileNotFoundError) as except_result:
            trepn_plugin.load_json(op.join(fixture_dir, 'fake_file.json'))
        assert "FileNotFoundError" in except_result.typename

    def test_load_json_file_permission_denied(self, tmpdir, trepn_plugin):
        tmp_file = op.join(str(tmpdir), 'tmp_file.txt')
        open(tmp_file, "w+")
        chmod(tmp_file, 0o222)
        with pytest.raises(IOError) as except_result:
            trepn_plugin.load_json(tmp_file)
        assert "Permission denied" in except_result.value
