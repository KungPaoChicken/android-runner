import pytest
import paths
import os
from ExperimentRunner.Browsers.Chrome import Chrome
from ExperimentRunner.Browsers.Opera import Opera
from ExperimentRunner.Browsers.Firefox import Firefox
from ExperimentRunner.Browsers.Browser import Browser
from ExperimentRunner.Devices import Devices
from ExperimentRunner.Scripts import Scripts
from ExperimentRunner.Profilers import Profilers
from ExperimentRunner.ExperimentFactory import ExperimentFactory
from ExperimentRunner.Experiment import Experiment
from ExperimentRunner.NativeExperiment import NativeExperiment
from ExperimentRunner.WebExperiment import WebExperiment
from mock import patch, Mock, MagicMock, call
from ExperimentRunner.util import ConfigError, makedirs


class TestExperiment(object):

    @pytest.fixture()
    def test_config(self):
        config = dict()
        config['randomization'] = True
        config['adb_path'] = 'test_adb'
        config['devices'] = ['dev1', 'dev2']
        config['replications'] = 10
        config['paths'] = ['test/paths/1', 'test/paths/2']
        config['profilers'] = {'fake': {'config1': 1, 'config2': 2}}
        config['monkeyrunner_path'] = 'monkey_path'
        config['scripts'] = {'script1': 'path/to/1'}
        config['time_between_run'] = 10
        return config

    @pytest.fixture()
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def default_experiment(self, mock_devices, mock_test):
        paths.OUTPUT_DIR = 'fake/path/name'
        device_config = {'devices': 'fake_device'}
        mock_devices.return_value = None
        return Experiment(device_config, None)

    def test_init_empty_config(self):
        empty_config = {}
        with pytest.raises(ConfigError):
            Experiment(empty_config, None)

    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_only_device_config(self, mock_devices, mock_test):
        paths.OUTPUT_DIR = 'fake/path/name'
        device_config = {'devices': 'fake_device'}
        mock_devices.return_value = None
        experiment = Experiment(device_config, None)

        assert experiment.progress is None
        assert experiment.basedir is None
        assert experiment.random is False
        assert isinstance(experiment.devices, Devices)
        assert experiment.replications == 1
        assert experiment.paths == []
        assert isinstance(experiment.profilers, Profilers)
        assert isinstance(experiment.scripts, Scripts)
        assert experiment.time_between_run == 0
        assert experiment.output_root == paths.OUTPUT_DIR
        assert experiment.result_file_structure is None

    @patch('ExperimentRunner.Scripts.Scripts.__init__')
    @patch('ExperimentRunner.Experiment.Profilers')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_full_config(self, mock_devices, mock_test, mock_profilers, mock_scripts, test_config):
        paths.OUTPUT_DIR = 'fake/path/name'
        mock_devices.return_value = None
        profiler_instance = MagicMock()
        profiler_instance.dependencies.return_value = []
        mock_profilers.return_value = profiler_instance
        mock_scripts.return_value = None
        mock_progress = Mock()
        experiment = Experiment(test_config, mock_progress)

        assert experiment.progress == mock_progress
        assert experiment.basedir is None
        assert experiment.random is True
        assert isinstance(experiment.devices, Devices)
        assert experiment.replications == 10
        assert experiment.paths == ['test/paths/1', 'test/paths/2']
        assert 'Profilers()' in str(experiment.profilers)
        assert isinstance(experiment.scripts, Scripts)
        assert experiment.time_between_run == 10
        assert experiment.output_root == paths.OUTPUT_DIR
        assert experiment.result_file_structure is None
        mock_devices.assert_called_once_with(['dev1', 'dev2'], adb_path='test_adb')
        mock_profilers.assert_called_once_with({'fake': {'config1': 1, 'config2': 2}})
        mock_scripts.assert_called_once_with({'script1': 'path/to/1'}, monkeyrunner_path='monkey_path')
        mock_test.assert_called_once_with(experiment.devices, [])

    def test_prepare(self, default_experiment):
        mock_profilers = Mock()
        default_experiment.profilers = mock_profilers
        fake_device = Mock()

        default_experiment.prepare(fake_device)

        mock_profilers.load.assert_called_once_with(fake_device)
        fake_device.unplug.assert_called_once()

    def test_cleanup(self, default_experiment):
        mock_profilers = Mock()
        default_experiment.profilers = mock_profilers
        fake_device = Mock()

        default_experiment.cleanup(fake_device)
        mock_profilers.stop_profiling(fake_device)
        mock_profilers.unload.assert_called_once_with(fake_device)
        assert 'stop_profiling' in str(mock_profilers.mock_calls[0])
        assert 'unload' in str(mock_profilers.mock_calls[1])
        fake_device.plug.assert_called_once()

    def test_get_progress_xml_file(self, default_experiment):
        xml_path = 'path/to/progress/xml.xml'
        mock_progress = Mock()
        mock_progress.progress_xml_file = xml_path
        default_experiment.progress = mock_progress
        assert default_experiment.get_progress_xml_file() == xml_path

    def test_update_progress_empty_folder(self, default_experiment, tmpdir):
        mock_progress = Mock()
        default_experiment.progress = mock_progress
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        makedirs(os.path.join(paths.BASE_OUTPUT_DIR, 'data'))
        default_experiment.update_progress()

        mock_progress.write_progress_to_file.assert_called_once()
        result_walk_list = list(default_experiment.result_file_structure)
        expected_walk_list = default_experiment.walk_to_list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
        assert result_walk_list == expected_walk_list

    def test_update_progress_non_empty_folder(self, default_experiment, tmpdir):
        mock_progress = Mock()
        default_experiment.progress = mock_progress
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        folder_path = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '1', '2')
        makedirs(folder_path)
        open(os.path.join(folder_path, "test.txt"), "w+")
        default_experiment.update_progress()

        mock_progress.write_progress_to_file.assert_called_once()
        result_walk_list = list(default_experiment.result_file_structure)
        expected_walk_list = default_experiment.walk_to_list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
        assert result_walk_list == expected_walk_list

    def test_walk_to_list(self, default_experiment, tmpdir):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        folder_path1 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '1', '1')
        folder_path2 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '2', '1')
        makedirs(folder_path1), makedirs(folder_path2)
        open(os.path.join(folder_path1, "test.txt"), "w+")
        open(os.path.join(folder_path2, "test.txt"), "w+")

        walk_list = default_experiment.walk_to_list(os.walk(paths.BASE_OUTPUT_DIR))
        assert len(walk_list) == 7
        assert 'data/1/1/test.txt' in walk_list[0]
        assert 'data/2/1/test.txt' in walk_list[2]

    def test_check_result_files_correct(self, default_experiment, tmpdir):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        folder_path1 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '1', '1')
        folder_path2 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '2', '1')
        makedirs(folder_path1), makedirs(folder_path2)
        open(os.path.join(folder_path1, "test.txt"), "w+")
        open(os.path.join(folder_path2, "test.txt"), "w+")
        correct_file_structure1 = os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data'))
        correct_file_structure2 = os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data'))

        default_experiment.check_result_files(correct_file_structure1)

        current_file_structure = os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data'))

        assert list(current_file_structure) == list(correct_file_structure2)

    def test_check_result_files_incorrect(self, default_experiment, tmpdir):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        folder_path1 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '1', '1')
        folder_path2 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '2', '1')
        folder_path3 = os.path.join(paths.BASE_OUTPUT_DIR, 'data', '3', '1')
        makedirs(folder_path1), makedirs(folder_path2)
        open(os.path.join(folder_path1, "test.txt"), "w+")
        open(os.path.join(folder_path2, "test.txt"), "w+")

        correct_file_structure_list1 = default_experiment.walk_to_list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
        correct_file_structure_list2 = list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))

        makedirs(folder_path3)
        open(os.path.join(folder_path3, "test.txt"), "w+")

        incorrect_file_structure_list = list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
        assert not correct_file_structure_list2 == incorrect_file_structure_list

        default_experiment.check_result_files(correct_file_structure_list1)

        current_file_structure_list = list(os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
        assert current_file_structure_list == correct_file_structure_list2

    def test_get_experiment(self, default_experiment):
        default_experiment.random = False
        mock_progress = Mock()
        get_next_run_mock = Mock()
        mock_progress.get_next_run.return_value = get_next_run_mock
        default_experiment.progress = mock_progress

        assert default_experiment.get_experiment() == get_next_run_mock

    def test_get_experiment_random(self, default_experiment):
        default_experiment.random = True
        mock_progress = Mock()
        get_random_run_mock = Mock()
        mock_progress.get_random_run.return_value = get_random_run_mock
        default_experiment.progress = mock_progress

        assert default_experiment.get_experiment() == get_random_run_mock

    @patch('ExperimentRunner.Experiment.Experiment.prepare')
    @patch('ExperimentRunner.Experiment.Experiment.before_experiment')
    def test_first_run_device(self, before_experiment, prepare, default_experiment):
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        fake_dict = {'device': 'fake_device'}

        default_experiment.first_run_device(fake_dict)

        prepare.assert_called_once_with(mock_device)
        before_experiment.assert_called_once_with(mock_device)
        mock_devices.get_device.assert_has_calls([call('fake_device'), call('fake_device')])

    @patch('ExperimentRunner.Experiment.Experiment.before_first_run')
    def test_first_run(self, before_first_run, default_experiment):
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        fake_dict = {'device': 'fake_device', 'path': 'test/path'}

        default_experiment.first_run(fake_dict)

        before_first_run.assert_called_once_with(mock_device, fake_dict['path'])
        mock_devices.get_device.assert_called_once_with(fake_dict['device'])

    @patch('ExperimentRunner.Experiment.Experiment.after_experiment')
    def test_last_run_device_false(self, after_experiment, default_experiment):
        mock_progress = Mock()
        mock_progress.device_finished.return_value = False
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device'}

        default_experiment.last_run_device(fake_dict)

        assert after_experiment.call_count == 0
        mock_progress.device_finished.assert_called_once_with(fake_dict['device'])

    @patch('ExperimentRunner.Experiment.Experiment.after_experiment')
    def test_last_run_device_true(self, after_experiment, default_experiment):
        mock_progress = Mock()
        mock_progress.device_finished.return_value = True
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device'}
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices

        default_experiment.last_run_device(fake_dict)

        after_experiment.assert_called_once_with(mock_device)
        mock_progress.device_finished.assert_called_once_with(fake_dict['device'])
        mock_devices.get_device.assert_called_once_with(fake_dict['device'])

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    @patch('ExperimentRunner.Experiment.Experiment.aggregate_subject')
    def test_last_run_false(self, aggregate_subject, after_last_run, default_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = False
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path'}

        default_experiment.last_run(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'])
        assert after_last_run.call_count == 0
        assert aggregate_subject.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    @patch('ExperimentRunner.Experiment.Experiment.aggregate_subject')
    def test_last_run_true(self, aggregate_subject, after_last_run, default_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = True
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path'}
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices

        default_experiment.last_run(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'])
        after_last_run.assert_called_once_with(mock_device, fake_dict['path'])
        mock_devices.get_device.assert_called_once_with(fake_dict['device'])
        aggregate_subject.assert_called_once()

    def test_prepare_output_dir(self, tmpdir, default_experiment):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        fake_dict = {'device': 'fake_device', 'path': 'fake_path'}

        default_experiment.prepare_output_dir(fake_dict)

        assert os.path.isdir(paths.OUTPUT_DIR)
        assert paths.OUTPUT_DIR == os.path.join(paths.BASE_OUTPUT_DIR, 'data', 'fake_device', 'fake_path')

    @patch('ExperimentRunner.Experiment.Experiment.after_run')
    @patch('ExperimentRunner.Experiment.Experiment.stop_profiling')
    @patch('ExperimentRunner.Experiment.Experiment.interaction')
    @patch('ExperimentRunner.Experiment.Experiment.start_profiling')
    @patch('ExperimentRunner.Experiment.Experiment.before_run')
    def test_run(self, before_run, start_profiling, interaction, stop_profiling, after_run, default_experiment):
        mock_device = Mock()
        path = "test/path"
        run = 123456789

        default_experiment.run(mock_device, path, run, None)

        before_run.assert_called_once_with(mock_device, path, run)
        start_profiling.assert_called_once_with(mock_device, path, run)
        interaction.assert_called_once_with(mock_device, path, run)
        stop_profiling.assert_called_once_with(mock_device, path, run)
        after_run.assert_called_once_with(mock_device, path, run)

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_before_experiment(self, run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()

        default_experiment.before_experiment(mock_device, *args, **kwargs)

        run.assert_called_once_with('before_experiment', mock_device, *args, **kwargs)

    def test_before_first_run(self, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        default_experiment.before_first_run(mock_device, path, *args, **kwargs)

    @patch('ExperimentRunner.Profilers.Profilers.set_output')
    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_before_run(self, script_run, set_output, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789
        default_experiment.before_run(mock_device, path, run, *args, **kwargs)

        set_output.assert_called_once()
        mock_device.shell.assert_called_once_with('logcat -c')
        script_run.assert_called_once_with('before_run', mock_device, *args, **kwargs)

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_after_launch(self, script_run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789

        default_experiment.after_launch(mock_device, path, run, *args, **kwargs)
        script_run.assert_called_once_with('after_launch', mock_device, *args, **kwargs)

    @patch('ExperimentRunner.Profilers.Profilers.start_profiling')
    def test_start_profiling(self, start_profiling, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789

        default_experiment.start_profiling(mock_device, path, run, *args, **kwargs)
        start_profiling.assert_called_once_with(mock_device)

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_interaction(self, script_run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789

        default_experiment.interaction(mock_device, path, run, *args, **kwargs)
        script_run.assert_called_once_with('interaction', mock_device, *args, **kwargs)

    @patch('ExperimentRunner.Profilers.Profilers.stop_profiling')
    def test_stop_profiling(self, start_profiling, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789

        default_experiment.stop_profiling(mock_device, path, run, *args, **kwargs)
        start_profiling.assert_called_once_with(mock_device)

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_before_close(self, script_run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789

        default_experiment.before_close(mock_device, path, run, *args, **kwargs)
        script_run.assert_called_once_with('before_close', mock_device, *args, **kwargs)

    @patch('time.sleep')
    @patch('ExperimentRunner.Profilers.Profilers.collect_results')
    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_after_run(self, script_run, collect_results, sleep, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789
        default_experiment.time_between_run = 2000

        default_experiment.after_run(mock_device, path, run, *args, **kwargs)
        script_run.assert_called_once_with('after_run', mock_device, *args, **kwargs)
        collect_results.assert_called_once_with(mock_device)
        sleep.assert_called_once_with(2)

    def test_after_last_run(self, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        default_experiment.after_last_run(mock_device, path, *args, **kwargs)

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_after_experiment(self, script_run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()

        default_experiment.after_experiment(mock_device, *args, **kwargs)
        script_run.assert_called_once_with('after_experiment', mock_device, *args, **kwargs)

    @patch('ExperimentRunner.Profilers.Profilers.aggregate_subject')
    def test_aggregate_subject(self, aggregate_subject, default_experiment):
        default_experiment.aggregate_subject()
        aggregate_subject.assert_called_once()

    @patch('ExperimentRunner.Profilers.Profilers.aggregate_end')
    def test_aggregate_end(self, aggregate_end, default_experiment, tmpdir):
        default_experiment.output_root = str(tmpdir)
        default_experiment.aggregate_end()
        aggregate_end.assert_called_once_with(default_experiment.output_root)


class TestWebExperiment(object):
    @pytest.fixture()
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def web_experiment(self, device, check_dependencies):
        device.return_value = None
        device_config = {'devices': 'fake_device'}
        return WebExperiment(device_config, None)

    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_empty_config(self, device, check_dependencies):
        device.return_value = None
        device_config = {'devices': 'fake_device'}
        web_experiment = WebExperiment(device_config, None)

        assert check_dependencies.call_count == 2
        assert web_experiment.duration == 0
        assert len(web_experiment.browsers) == 1
        assert isinstance(web_experiment.browsers[0], Chrome)

    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_nom_empty_config(self, device, check_dependencies):
        device.return_value = None
        device_config = {'devices': 'fake_device', 'browsers': ['firefox', 'opera'], 'duration': 1000}
        web_experiment = WebExperiment(device_config, None)

        assert check_dependencies.call_count == 2
        assert web_experiment.duration == 1
        assert len(web_experiment.browsers) == 2
        assert isinstance(web_experiment.browsers[0], Firefox)
        assert isinstance(web_experiment.browsers[1], Opera)

    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_run')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.before_close')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.stop_profiling')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.interaction')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.start_profiling')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_launch')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.before_run')
    def test_run(self, before_run, after_launch, start_profiling, interaction, stop_profiling, before_close, after_run, web_experiment):
        mock_device = Mock()
        path = "test/path"
        run = 123456789
        mock_browser = Mock()
        mock_browser.to_string.return_value = 'chrome'
        web_experiment.browsers = [mock_browser]
        web_experiment.run(mock_device, path, run, 'chrome')

        before_run.assert_called_once_with(mock_device, path, run, mock_browser)
        after_launch.assert_called_once_with(mock_device, path, run, mock_browser)
        start_profiling.assert_called_once_with(mock_device, path, run, mock_browser)
        interaction.assert_called_once_with(mock_device, path, run, mock_browser)
        stop_profiling.assert_called_once_with(mock_device, path, run, mock_browser)
        before_close.assert_called_once_with(mock_device, path, run, mock_browser)
        after_run.assert_called_once_with(mock_device, path, run, mock_browser)

    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_last_run')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.aggregate_subject')
    def test_last_run_false(self, aggregate_subject, after_last_run, web_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = False
        web_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path', 'browser': 'fake_browser'}

        web_experiment.last_run(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'], fake_dict['browser'])
        assert after_last_run.call_count == 0
        assert aggregate_subject.call_count == 0

    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_last_run')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.aggregate_subject')
    def test_last_run_true(self, aggregate_subject, after_last_run, web_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = True
        web_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path', 'browser': 'fake_browser'}
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        web_experiment.devices = mock_devices

        web_experiment.last_run(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'], fake_dict['browser'])
        after_last_run.assert_called_once_with(mock_device, fake_dict['path'])
        mock_devices.get_device.assert_called_once_with(fake_dict['device'])
        aggregate_subject.assert_called_once()

    def test_prepare_output_dir(self, tmpdir, web_experiment):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        fake_dict = {'device': 'fake_device', 'path': 'fake_path', 'browser': 'fake_browser'}

        web_experiment.prepare_output_dir(fake_dict)

        assert os.path.isdir(paths.OUTPUT_DIR)
        assert paths.OUTPUT_DIR == os.path.join(paths.BASE_OUTPUT_DIR, 'data', 'fake_device', 'fake_path', 'fake_browser')

    @patch('ExperimentRunner.Experiment.Experiment.before_first_run')
    def test_before_first_run(self, before_first_run, web_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        web_experiment.before_first_run(mock_device, path, *args, **kwargs)

        before_first_run.assert_called_once_with(mock_device, path)

    @patch('ExperimentRunner.Browsers.Browser.Browser.start')
    @patch('time.sleep')
    @patch('ExperimentRunner.Scripts.Scripts.run')
    @patch('ExperimentRunner.Experiment.Experiment.before_run')
    def test_before_run(self, before_run, scripts_run, sleep, browser_start, web_experiment):
        mock_browser = Browser({})
        args = (mock_browser, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 'id'
        current_activity = "playing euro truck simulator 2"
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 123456789

        web_experiment.before_run(mock_device, path, run, *args, **kwargs)

        before_run.assert_called_once_with(mock_device, path, run)
        browser_start.assert_called_once_with(mock_device)
        sleep.assert_called_once_with(5)
        scripts_run.assert_called_once_with('after_launch', mock_device, 'id', current_activity)