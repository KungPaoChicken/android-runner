import os
from shutil import copyfile

import pytest
from mock import MagicMock, Mock, patch

import paths
from ExperimentRunner.PluginHandler import PluginHandler
from ExperimentRunner.Profilers import Profilers
from ExperimentRunner.util import load_json, makedirs


class TestProfilers(object):

    @pytest.fixture()
    @patch('ExperimentRunner.PluginHandler.PluginHandler.__init__')
    def profilers(self, mock):
        mock.return_value = None
        params = {"test1": "waarde1", "test2": "waarde2"}
        config = {"testPlugin": params}
        return Profilers(config)

    @patch('ExperimentRunner.PluginHandler.PluginHandler.__init__')
    def test_init(self, mock):
        mock.return_value = None
        params = {"test1": "waarde1", "test2": "waarde2"}
        config = {"testPlugin": params}
        current_profiler = Profilers(config)
        mock.assert_called_once_with('testPlugin', params)
        assert len(current_profiler.profilers) == 1
        assert type(current_profiler.profilers[0]) == PluginHandler

    @patch('ExperimentRunner.PluginHandler.PluginHandler.__init__')
    def test_init_error(self, mock):
        mock.side_effect = ImportError
        params = {"test1": "waarde1", "test2": "waarde2"}
        config = {"testPlugin": params}
        with pytest.raises(ImportError):
            Profilers(config)

    def test_dependencies(self, profilers):
        profiler1 = Mock()
        profiler1.dependencies.return_value = ["dependencie1"]
        profiler2 = Mock()
        profiler2.dependencies.return_value = ["dependencie2"]
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        dependencies = profilers.dependencies()
        assert len(dependencies) == 2
        assert "dependencie1" in dependencies
        assert "dependencie2" in dependencies

    def test_load_empty(self, profilers):
        fake_device = Mock
        fake_device.name = "fake_device"
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m

        assert len(profilers.loaded_devices) == 0
        profilers.load(fake_device)
        profiler1.load.assert_called_once_with(fake_device)
        profiler2.load.assert_called_once_with(fake_device)
        assert len(profilers.loaded_devices) == 1
        assert profilers.loaded_devices[0] == "fake_device"

    def test_load_non_empty(self, profilers):
        fake_device = Mock
        fake_device.name = "fake_device"
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.loaded_devices.append("fake_device")

        assert len(profilers.loaded_devices) == 1
        profilers.load(fake_device)
        assert profiler1.load.call_count == 0
        assert profiler2.load.call_count == 0
        assert len(profilers.loaded_devices) == 1

    def test_start_profiling(self, profilers):
        fake_device = Mock()
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.start_profiling(fake_device, arg1="arg1", arg2="arg2")
        profiler1.start_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")
        profiler2.start_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")

    def test_stop_profiling(self, profilers):
        fake_device = Mock()
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.stop_profiling(fake_device, arg1="arg1", arg2="arg2")
        profiler1.stop_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")
        profiler2.stop_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")

    def test_collect_results(self, profilers):
        fake_device = Mock()
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.collect_results(fake_device)
        profiler1.collect_results.assert_called_once_with(fake_device)
        profiler2.collect_results.assert_called_once_with(fake_device)

    def test_unload(self, profilers):
        fake_device = Mock()
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.unload(fake_device)
        profiler1.unload.assert_called_once_with(fake_device)
        profiler2.unload.assert_called_once_with(fake_device)

    def test_set_output(self, profilers):
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.set_output()
        profiler1.set_output.assert_called_once_with()
        profiler2.set_output.assert_called_once_with()

    def test_aggregate_subject(self, profilers):
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.aggregate_subject()
        profiler1.aggregate_subject.assert_called_once()
        profiler2.aggregate_subject.assert_called_once()

    def test_aggregate_end(self, profilers):
        profiler1 = Mock()
        profiler2 = Mock()
        m = MagicMock()
        m.__iter__.return_value = [profiler1, profiler2]
        profilers.profilers = m
        profilers.aggregate_end("fake/dir/path")
        profiler1.aggregate_data_end.assert_called_once_with("fake/dir/path")
        profiler2.aggregate_data_end.assert_called_once_with("fake/dir/path")


class TestPluginHandler(object):
    @pytest.fixture()
    def fixture_dir(self):
        fixture_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")
        return fixture_dir

    @pytest.fixture()
    def android_test_plugin_handler(self, tmpdir, fixture_dir):
        android_config = load_json(os.path.join(fixture_dir, 'test_config.json'))['profilers']['android']
        tmpdir = str(tmpdir)
        paths.CONFIG_DIR = tmpdir
        os.makedirs(os.path.join(tmpdir, 'Plugins'))
        copyfile(os.path.join(fixture_dir, 'Android1.py'), os.path.join(tmpdir, 'Plugins', 'Android1.py'))
        plugin_handler = PluginHandler('Android1', android_config)
        return plugin_handler

    @patch("pluginbase.PluginBase.make_plugin_source")
    @patch("pluginbase.PluginBase.__init__")
    def test_handler_init_default(self, plugin_base_init_mock, make_plugin_source_mock, fixture_dir):
        plugin_base_init_mock.return_value = None
        mock_loaded_plugin = Mock()
        mock_plugin_source = Mock()
        mock_plugin_source.load_plugin.return_value = mock_loaded_plugin
        make_plugin_source_mock.return_value = mock_plugin_source

        android_config = load_json(os.path.join(fixture_dir, 'test_config.json'))['profilers']['android']
        PluginHandler('Android', android_config)
        plugin_base_init_mock.assert_called_once()
        make_plugin_source_mock.assert_called_once_with(
            searchpath=[os.path.join(paths.ROOT_DIR, 'ExperimentRunner', 'Plugins')])
        mock_plugin_source.load_plugin.assert_called_once_with('Android')

    def test_handler_init_plugin(self, tmpdir, fixture_dir):
        android_config = load_json(os.path.join(fixture_dir, 'test_config.json'))['profilers']['android']
        tmpdir = str(tmpdir)
        paths.CONFIG_DIR = tmpdir
        os.makedirs(os.path.join(tmpdir, 'Plugins'))
        copyfile(os.path.join(fixture_dir, 'Android1.py'), os.path.join(tmpdir, 'Plugins', 'Android1.py'))
        plugin_handler = PluginHandler('Android1', android_config)
        assert plugin_handler.currentProfiler.__class__.__name__ == 'Android1'
        assert plugin_handler.currentProfiler.data_points == ['cpu', 'mem']

    def test_handler_init_error(self, tmpdir):
        paths.CONFIG_DIR = str(tmpdir)
        with pytest.raises(ImportError):
            PluginHandler('android2', dict())

    def test_dependencies_empty(self, android_test_plugin_handler):
        mock_profiler = Mock()
        mock_profiler.dependencies.return_value = []
        android_test_plugin_handler.currentProfiler = mock_profiler
        assert android_test_plugin_handler.dependencies() == []

    def test_dependencies_non_empty(self, android_test_plugin_handler):
        mock_profiler = Mock()
        mock_profiler.dependencies.return_value = ['test.dependencie']
        android_test_plugin_handler.currentProfiler = mock_profiler
        assert android_test_plugin_handler.dependencies() == ['test.dependencie']

    def test_load(self, android_test_plugin_handler):
        fake_device = Mock()
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.load(fake_device)

        mock_profiler.load.assert_called_once_with(fake_device)

    def test_start_profiling(self, android_test_plugin_handler):
        fake_device = Mock()
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.start_profiling(fake_device, arg1="arg1", arg2="arg2")

        mock_profiler.start_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")

    def test_stop_profiling(self, android_test_plugin_handler):
        fake_device = Mock()
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.stop_profiling(fake_device, arg1="arg1", arg2="arg2")

        mock_profiler.stop_profiling.assert_called_once_with(fake_device, arg1="arg1", arg2="arg2")

    def test_unload(self, android_test_plugin_handler):
        fake_device = Mock()
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.unload(fake_device)

        mock_profiler.unload.assert_called_once_with(fake_device)

    def test_set_output(self, android_test_plugin_handler, tmpdir):
        tmpdir = str(tmpdir)
        paths.OUTPUT_DIR = tmpdir
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.set_output()

        mock_profiler.set_output.assert_called_once_with(os.path.join(tmpdir, 'Android1'))
        assert os.path.isdir(os.path.join(tmpdir, 'Android1'))

    def test_list_dir_empty(self, tmpdir, android_test_plugin_handler):
        tmpdir = os.path.join(str(tmpdir), 'test')
        makedirs(tmpdir)
        assert android_test_plugin_handler.list_subdir(tmpdir) == []

    def test_list_dir_non_empty(self, tmpdir, android_test_plugin_handler):
        tmpdir = os.path.join(str(tmpdir), 'test')
        makedirs(tmpdir)
        os.makedirs(os.path.join(tmpdir, '1'))
        os.makedirs(os.path.join(tmpdir, '2'))
        sub_dirs = android_test_plugin_handler.list_subdir(tmpdir)
        assert len(sub_dirs) == 2
        assert '1' in sub_dirs
        assert '2' in sub_dirs

    def test_collect_result(self, android_test_plugin_handler):
        fake_device = Mock()
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.collect_results(fake_device)

        mock_profiler.collect_results.assert_called_once_with(fake_device)

    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_subject_no_selection(self, python, android_test_plugin_handler):
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.pluginParams = {}

        android_test_plugin_handler.aggregate_subject()

        mock_profiler.aggregate_subject.assert_called_once()
        assert python.call_count == 0
        assert android_test_plugin_handler.subject_aggregated
        assert android_test_plugin_handler.subject_aggregated_default

    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_subject_default(self, python, android_test_plugin_handler):
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.pluginParams = {'subject_aggregation': 'default'}
        android_test_plugin_handler.aggregate_subject()

        mock_profiler.aggregate_subject.assert_called_once()
        assert python.call_count == 0
        assert android_test_plugin_handler.subject_aggregated
        assert android_test_plugin_handler.subject_aggregated_default

    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_subject_none(self, python, android_test_plugin_handler):
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.pluginParams = {'subject_aggregation': 'none'}

        android_test_plugin_handler.aggregate_subject()

        assert mock_profiler.aggregate_subject.call_count == 0
        assert python.call_count == 0
        assert not android_test_plugin_handler.subject_aggregated
        assert not android_test_plugin_handler.subject_aggregated_default

    @patch('ExperimentRunner.Python3.Python3.__init__')
    @patch('ExperimentRunner.Python3.Python3.run')
    def test_aggregate_subject_user_script(self, python_run, python_init, android_test_plugin_handler):
        python_init.return_value = None
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.pluginParams = {'subject_aggregation': 'user_script'}

        android_test_plugin_handler.aggregate_subject()

        assert mock_profiler.aggregate_subject.call_count == 0
        python_init.assert_called_once_with(os.path.join(paths.CONFIG_DIR, 'user_script'))
        python_run.assert_called_once_with(None, paths.OUTPUT_DIR)
        assert android_test_plugin_handler.subject_aggregated
        assert not android_test_plugin_handler.subject_aggregated_default

    @patch('ExperimentRunner.PluginHandler.PluginHandler.aggregate_subjects_default')
    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_data_end_none(self, python, aggregate_subjects, android_test_plugin_handler):
        android_test_plugin_handler.pluginParams = {'experiment_aggregation': 'none'}
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.aggregate_data_end('fake/dir/')
        assert mock_profiler.aggregate_end.call_count == 0
        assert python.call_count == 0
        assert aggregate_subjects.call_count == 0

    @patch('ExperimentRunner.PluginHandler.PluginHandler.aggregate_subjects_default')
    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_data_end_default_subject_default(self, python, aggregate_subjects, android_test_plugin_handler):
        android_test_plugin_handler.pluginParams = {'experiment_aggregation': 'default'}
        mock_profiler = Mock()
        android_test_plugin_handler.subject_aggregated_default = True
        android_test_plugin_handler.subject_aggregated = True
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.aggregate_data_end('fake/dir/')

        mock_profiler.aggregate_end.assert_called_once_with('fake/dir/data', 'fake/dir/Aggregated_Results_Android1.csv')
        assert python.call_count == 0
        assert aggregate_subjects.call_count == 0

    @patch('ExperimentRunner.PluginHandler.PluginHandler.aggregate_subjects_default')
    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_data_end_default_no_subject(self, python, aggregate_subjects, android_test_plugin_handler):
        android_test_plugin_handler.pluginParams = {'experiment_aggregation': 'default'}
        mock_profiler = Mock()
        mock_manager = Mock()
        mock_manager.attach_mock(mock_profiler.aggregate_end, 'end')
        mock_manager.attach_mock(aggregate_subjects, 'subjects')
        android_test_plugin_handler.subject_aggregated_default = False
        android_test_plugin_handler.subject_aggregated = False
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.aggregate_data_end('fake/dir/')

        expected_call_order = "[call.subjects('fake/dir/data'),\n call.end('fake/dir/data', " \
                              "'fake/dir/Aggregated_Results_Android1.csv')]"
        assert expected_call_order == str(mock_manager.mock_calls)
        mock_profiler.aggregate_end.assert_called_once_with('fake/dir/data', 'fake/dir/Aggregated_Results_Android1.csv')
        assert python.call_count == 0
        aggregate_subjects.assert_called_once()

    @patch('ExperimentRunner.PluginHandler.PluginHandler.aggregate_subjects_default')
    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_data_end_default_user_aggregated(self, python, aggregate_subjects, android_test_plugin_handler):
        android_test_plugin_handler.pluginParams = {'experiment_aggregation': 'default'}
        mock_profiler = Mock()
        android_test_plugin_handler.subject_aggregated_default = False
        android_test_plugin_handler.subject_aggregated = True
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.aggregate_data_end('fake/dir/')

        assert mock_profiler.aggregate_end.call_count == 0
        assert python.call_count == 0
        assert aggregate_subjects.call_count == 0

    @patch('ExperimentRunner.PluginHandler.PluginHandler.aggregate_subjects_default')
    @patch('ExperimentRunner.Python3.Python3.run')
    @patch('ExperimentRunner.Python3.Python3.__init__')
    def test_aggregate_data_end_user_script(self, python_init, python_run, aggregate_subjects,
                                            android_test_plugin_handler):
        python_init.return_value = None
        android_test_plugin_handler.pluginParams = {'experiment_aggregation': 'user_script'}
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler
        android_test_plugin_handler.aggregate_data_end('fake/dir/')

        assert mock_profiler.aggregate_end.call_count == 0
        python_init.assert_called_once_with(os.path.join(paths.CONFIG_DIR, 'user_script'))
        python_run.assert_called_once_with(None, 'fake/dir/data', 'fake/dir/Aggregated_Results_Android1.csv')
        assert aggregate_subjects.call_count == 0

    def test_aggregate_subjects_default_no_data(self, android_test_plugin_handler, tmpdir):
        tmpdir = str(tmpdir)
        android_test_plugin_handler.aggregate_subjects_default(tmpdir)

    @staticmethod
    def make_paths(tmp_dir, paths_end):
        complete_paths = []
        for path_end in paths_end:
            complete_path = os.path.join(tmp_dir, path_end)
            makedirs(complete_path)
            complete_paths.append(complete_path)
        return complete_paths

    def test_aggregate_subject_default_native_experiment(self, android_test_plugin_handler, tmpdir):
        tmpdir = str(tmpdir)
        paths_ends = ['device1/native1/Android1', 'device1/native2/Android1', 'device1/native3/Android1']
        created_paths = self.make_paths(tmpdir, paths_ends)
        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.aggregate_subjects_default(tmpdir)

        assert mock_profiler.set_output.call_count == 3
        mock_profiler.set_output.called_with(created_paths[0])
        mock_profiler.set_output.called_with(created_paths[1])
        mock_profiler.set_output.called_with(created_paths[2])
        assert mock_profiler.aggregate_subject.call_count == 3

    def test_aggregate_subject_default_web_experiment(self, android_test_plugin_handler, tmpdir):
        tmpdir = str(tmpdir)
        paths_ends = ['device1/subject1/browser1/Android1', 'device1/subject2/browser1/Android1',
                      'device1/subject3/browser1/Android1']
        created_paths = self.make_paths(tmpdir, paths_ends)

        mock_profiler = Mock()
        android_test_plugin_handler.currentProfiler = mock_profiler

        android_test_plugin_handler.aggregate_subjects_default(tmpdir)

        assert mock_profiler.set_output.call_count == 3
        mock_profiler.set_output.called_with(created_paths[0])
        mock_profiler.set_output.called_with(created_paths[1])
        mock_profiler.set_output.called_with(created_paths[2])
        assert mock_profiler.aggregate_subject.call_count == 3
