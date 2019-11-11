import filecmp
import os
from collections import OrderedDict

import pytest
from mock import MagicMock, Mock, call, patch

import paths
from ExperimentRunner.Devices import Devices
from ExperimentRunner.Experiment import Experiment
from ExperimentRunner.ExperimentFactory import ExperimentFactory
from ExperimentRunner.NativeExperiment import NativeExperiment
from ExperimentRunner.Profilers import Profilers
from ExperimentRunner.Progress import Progress
from ExperimentRunner.Scripts import Scripts
from ExperimentRunner.WebExperiment import WebExperiment
from ExperimentRunner.util import ConfigError, makedirs
from tests.PluginTests import PluginTests


# noinspection PyUnusedLocal
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
        return Experiment(device_config, None, False)

    def test_init_empty_config(self):
        empty_config = {}
        with pytest.raises(ConfigError):
            Experiment(empty_config, None, False)

    @patch('ExperimentRunner.Experiment.Experiment.prepare_device')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_only_device_config_no_restart(self, mock_devices, mock_test, mock_prepare):
        paths.OUTPUT_DIR = 'fake/path/name'
        device_config = {'devices': 'fake_device'}
        mock_devices.return_value = None
        experiment = Experiment(device_config, None, False)

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
        assert mock_prepare.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.prepare_device')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__iter__')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_only_device_config_restart(self, mock_devices, mock_devices_itter, mock_test, mock_prepare):
        paths.OUTPUT_DIR = 'fake/path/name'
        device_config = {'devices': 'fake_device'}
        mock_devices_itter.return_value = ['dev1', 'dev2', 'dev3'].__iter__()
        mock_devices.return_value = None
        experiment = Experiment(device_config, None, True)

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
        assert mock_prepare.call_count == 3
        assert mock_prepare.mock_calls[0] == call('dev1', restart=True)
        assert mock_prepare.mock_calls[1] == call('dev2', restart=True)
        assert mock_prepare.mock_calls[2] == call('dev3', restart=True)

    @patch('ExperimentRunner.Experiment.Experiment.prepare_device')
    @patch('ExperimentRunner.Scripts.Scripts.__init__')
    @patch('ExperimentRunner.Experiment.Profilers')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_full_config_no_restart(self, mock_devices, mock_test, mock_profilers, mock_scripts, mock_prepare, test_config):
        paths.OUTPUT_DIR = 'fake/path/name'
        mock_devices.return_value = None
        profiler_instance = MagicMock()
        profiler_instance.dependencies.return_value = []
        mock_profilers.return_value = profiler_instance
        mock_scripts.return_value = None
        mock_progress = Mock()
        experiment = Experiment(test_config, mock_progress, False)

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
        assert mock_prepare.call_count == 0

    def test_prepare_device(self, default_experiment):
        mock_profilers = Mock()
        fake_device = Mock()
        mock_manager = Mock()
        mock_manager.mock_profilers = mock_profilers
        mock_manager.fake_device = fake_device
        default_experiment.profilers = mock_profilers

        default_experiment.prepare_device(fake_device)

        expected_calls = [call.mock_profilers.load(fake_device), call.fake_device.unplug(False)]
        assert mock_manager.mock_calls == expected_calls

    def test_cleanup(self, default_experiment):
        mock_profilers = Mock()
        fake_device = Mock()
        mock_manager = Mock()
        mock_manager.mock_profilers = mock_profilers
        mock_manager.fake_device = fake_device
        default_experiment.profilers = mock_profilers

        default_experiment.cleanup(fake_device)

        expected_calls = [call.fake_device.plug(), call.mock_profilers.stop_profiling(fake_device),
                          call.mock_profilers.unload(fake_device)]
        assert mock_manager.mock_calls == expected_calls

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

        correct_file_structure_list1 = default_experiment.walk_to_list(
            os.walk(os.path.join(paths.BASE_OUTPUT_DIR, 'data')))
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

    @patch('ExperimentRunner.Experiment.Experiment.prepare_device')
    @patch('ExperimentRunner.Experiment.Experiment.before_experiment')
    def test_first_run_device(self, before_experiment, prepare_device, default_experiment):
        mock_progress = Mock()
        mock_progress.device_first.return_value = True
        default_experiment.progress = mock_progress
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        fake_dict = {'device': 'fake_device'}
        mock_manager = Mock()
        mock_manager.attach_mock(before_experiment, "before_experiment_managed")
        mock_manager.attach_mock(prepare_device, "prepare_device_managed")

        default_experiment.first_run_device(fake_dict)
        expected_calls = [call.prepare_device_managed(mock_device), call.before_experiment_managed(mock_device)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.before_run_subject')
    def test_before_every_run_subject(self, before_run_subject, default_experiment):
        mock_devices = Mock()
        mock_device = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        fake_dict = {'device': 'fake_device', 'path': 'test/path'}

        default_experiment.before_every_run_subject(fake_dict)

        before_run_subject.assert_called_once_with(mock_device, fake_dict['path'])

    @patch('ExperimentRunner.Experiment.Experiment.after_experiment')
    def test_last_run_device_false(self, after_experiment, default_experiment):
        mock_progress = Mock()
        mock_progress.device_finished.return_value = False
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device'}

        default_experiment.last_run_device(fake_dict)

        assert after_experiment.call_count == 0

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

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    @patch('ExperimentRunner.Experiment.Experiment.aggregate_subject')
    def test_last_run_false(self, aggregate_subject, after_last_run, default_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = False
        default_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path'}

        default_experiment.last_run_subject(fake_dict)

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

        default_experiment.last_run_subject(fake_dict)

        after_last_run.assert_called_once_with(mock_device, fake_dict['path'])
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
        mock_manager = Mock()
        mock_manager.attach_mock(before_run, "before_run_managed")
        mock_manager.attach_mock(start_profiling, "start_profiling_managed")
        mock_manager.attach_mock(interaction, "interaction_managed")
        mock_manager.attach_mock(stop_profiling, "stop_profiling_managed")
        mock_manager.attach_mock(after_run, "after_run_managed")

        default_experiment.run(mock_device, path, run, None)

        expected_calls = [call.before_run_managed(mock_device, path, run),
                          call.start_profiling_managed(mock_device, path, run),
                          call.interaction_managed(mock_device, path, run),
                          call.stop_profiling_managed(mock_device, path, run),
                          call.after_run_managed(mock_device, path, run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_before_experiment(self, run_script_mock, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()

        default_experiment.before_experiment(mock_device, *args, **kwargs)

        run_script_mock.assert_called_once_with('before_experiment', mock_device, *args, **kwargs)

    def test_before_first_run(self, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        default_experiment.before_run_subject(mock_device, path, *args, **kwargs)

    @patch('ExperimentRunner.Profilers.Profilers.set_output')
    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_before_run(self, script_run, set_output, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 1234566789
        mock_manager = Mock()
        mock_manager.attach_mock(set_output, 'set_output_managed')
        mock_manager.attach_mock(mock_device, 'mock_device_managed')
        mock_manager.attach_mock(script_run, 'script_run_managed')
        default_experiment.before_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.set_output_managed(),
                          call.mock_device_managed.shell('logcat -c'),
                          call.script_run_managed('before_run', mock_device, *args, **kwargs)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Scripts.Scripts.run')
    def test_after_launch(self, script_run, default_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 123
        current_activity = 'Working on theses'
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 1234566789

        default_experiment.after_launch(mock_device, path, run, *args, **kwargs)

        script_run.assert_called_once_with('after_launch', mock_device, 123, current_activity)

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
        mock_device.id = 123
        current_activity = 'Working on theses'
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 1234566789

        default_experiment.before_close(mock_device, path, run, *args, **kwargs)

        script_run.assert_called_once_with('before_close', mock_device, 123, current_activity)

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
        mock_manager = Mock()
        mock_manager.attach_mock(script_run, "script_run_managed")
        mock_manager.attach_mock(collect_results, "collect_results_managed")
        mock_manager.attach_mock(sleep, "sleep_managed")

        default_experiment.after_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.script_run_managed('after_run', mock_device, *args, **kwargs),
                          call.collect_results_managed(mock_device),
                          call.sleep_managed(2)]
        assert mock_manager.mock_calls == expected_calls

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

    @patch('ExperimentRunner.Experiment.Experiment.aggregate_end')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    @patch('ExperimentRunner.Experiment.Experiment.check_result_files')
    def test_finish_experiment_regular_no_devices(self, check_result_files, cleanup, aggregate_end, default_experiment):
        fake_file_structure = 'test_structure'
        default_experiment.result_file_structure = fake_file_structure
        default_experiment.devices = []
        mock_manager = Mock()
        mock_manager.attach_mock(check_result_files, "check_result_files_managed")
        mock_manager.attach_mock(aggregate_end, "aggregate_end_managed")

        default_experiment.finish_experiment(False, False)

        expected_calls = [call.check_result_files_managed(fake_file_structure),
                          call.aggregate_end_managed()]
        assert mock_manager.mock_calls == expected_calls
        assert cleanup.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.aggregate_end')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    @patch('ExperimentRunner.Experiment.Experiment.check_result_files')
    def test_finish_experiment_regular_multiple_devices(self, check_result_files, cleanup, aggregate_end,
                                                        default_experiment):
        fake_file_structure = 'test_structure'
        default_experiment.result_file_structure = fake_file_structure
        default_experiment.devices = ['1', '2', '3']
        mock_manager = Mock()
        mock_manager.attach_mock(check_result_files, "check_result_files_managed")
        mock_manager.attach_mock(aggregate_end, "aggregate_end_managed")
        mock_manager.attach_mock(cleanup, "cleanup_managed")

        default_experiment.finish_experiment(False, False)

        expected_calls = [call.check_result_files_managed(fake_file_structure),
                          call.cleanup_managed('1'),
                          call.cleanup_managed('2'),
                          call.cleanup_managed('3'),
                          call.aggregate_end_managed()]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.aggregate_end')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    @patch('ExperimentRunner.Experiment.Experiment.check_result_files')
    def test_finish_experiment_error(self, check_result_files, cleanup, aggregate_end, default_experiment):
        fake_file_structure = 'test_structure'
        default_experiment.devices = ['1']
        default_experiment.result_file_structure = fake_file_structure
        default_experiment.finish_experiment(True, False)

        check_result_files.assert_called_once_with(fake_file_structure)
        cleanup.assert_called_once_with('1')
        assert aggregate_end.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.aggregate_end')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    @patch('ExperimentRunner.Experiment.Experiment.check_result_files')
    def test_finish_experiment_interrupted(self, check_result_files, cleanup, aggregate_end, default_experiment):
        fake_file_structure = 'test_structure'
        default_experiment.devices = ['1']
        default_experiment.result_file_structure = fake_file_structure

        default_experiment.finish_experiment(False, True)

        check_result_files.assert_called_once_with(fake_file_structure)
        cleanup.assert_called_once_with('1')
        assert aggregate_end.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.aggregate_end')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    @patch('ExperimentRunner.Experiment.Experiment.check_result_files')
    def test_finish_experiment_error_in_cleanup(self, check_result_files, cleanup, aggregate_end, default_experiment):
        fake_file_structure = 'test_structure'
        default_experiment.devices = ['1']
        default_experiment.result_file_structure = fake_file_structure
        cleanup.side_effect = Exception
        default_experiment.finish_experiment(True, False)
        check_result_files.assert_called_once_with(fake_file_structure)
        cleanup.assert_called_once_with('1')
        assert aggregate_end.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.finish_run')
    @patch('ExperimentRunner.Experiment.Experiment.run_run')
    @patch('ExperimentRunner.Experiment.Experiment.prepare_run')
    def test_run_experiment(self, prepare_run, run_run, finish_run, default_experiment):
        test_run = Mock()
        mock_manager = Mock()
        mock_manager.attach_mock(prepare_run, "prepare_run_managed")
        mock_manager.attach_mock(run_run, "run_run_managed")
        mock_manager.attach_mock(finish_run, "finish_run_managed")

        default_experiment.run_experiment(test_run)

        expected_calls = [call.prepare_run_managed(test_run),
                          call.run_run_managed(test_run),
                          call.finish_run_managed(test_run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.prepare_output_dir')
    @patch('ExperimentRunner.Experiment.Experiment.first_run_device')
    @patch('ExperimentRunner.Experiment.Experiment.before_every_run_subject')
    def test_prepare_run(self, before_every_run_subject, first_run_device, prepare_output_dir, default_experiment):
        test_run = Mock()
        mock_manager = Mock()
        mock_manager.attach_mock(before_every_run_subject, "before_every_run_subject_managed")
        mock_manager.attach_mock(first_run_device, "first_run_device_managed")
        mock_manager.attach_mock(prepare_output_dir, "prepare_output_dir_managed")

        default_experiment.prepare_run(test_run)

        expected_calls = [call.prepare_output_dir_managed(test_run),
                          call.first_run_device_managed(test_run),
                          call.before_every_run_subject_managed(test_run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.run')
    def test_run_run_w_browser(self, run, default_experiment):
        mock_device = Mock()
        mock_devices = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        test_run = {'device': 'test_device', 'path': 'test_path', 'runCount': '123', 'browser': 'test_browser'}
        default_experiment.run_run(test_run)

        run.assert_called_once_with(mock_device, test_run['path'], int(test_run['runCount']), test_run['browser'])

    @patch('ExperimentRunner.Experiment.Experiment.run')
    def test_run_run_wo_browser(self, run, default_experiment):
        mock_device = Mock()
        mock_devices = Mock()
        mock_devices.get_device.return_value = mock_device
        default_experiment.devices = mock_devices
        test_run = {'device': 'test_device', 'path': 'test_path', 'runCount': '123'}
        default_experiment.run_run(test_run)

        run.assert_called_once_with(mock_device, test_run['path'], int(test_run['runCount']), None)

    @patch('ExperimentRunner.Experiment.Experiment.last_run_device')
    @patch('ExperimentRunner.Experiment.Experiment.last_run_subject')
    def test_finish_run(self, last_run_subject, last_run_device, default_experiment):
        mock_progres = Mock()
        default_experiment.progress = mock_progres
        test_run = {'device': 'test_device', 'path': 'test_path', 'runId': '123'}
        mock_manager = Mock()
        mock_manager.attach_mock(mock_progres, "mock_progres_managed")
        mock_manager.attach_mock(last_run_subject, "last_run_managed")
        mock_manager.attach_mock(last_run_device, "last_run_device_managed")

        default_experiment.finish_run(test_run)

        expected_calls = [call.mock_progres_managed.run_finished(test_run['runId']),
                          call.last_run_managed(test_run),
                          call.last_run_device_managed(test_run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('threading.Thread.join')
    @patch('threading.Thread.start')
    @patch('threading.Thread.__init__')
    def test_save_progress(self, mock_threading_init, mock_threading_start, mock_threading_join, default_experiment):
        mock_threading_init.return_value = None
        mock_manager = Mock()
        mock_manager.attach_mock(mock_threading_init, "mock_threading_init_managed")
        mock_manager.attach_mock(mock_threading_start, "mock_threading_start_managed")
        mock_manager.attach_mock(mock_threading_join, "mock_threading_join_managed")

        default_experiment.save_progress()

        expected_calls = [call.mock_threading_init_managed(target=default_experiment.update_progress),
                          call.mock_threading_start_managed(),
                          call.mock_threading_join_managed()]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.finish_experiment')
    def test_start_error(self, finish_experiment_mock, capsys, default_experiment):
        mock_logger = Mock()
        default_experiment.logger = mock_logger
        paths.BASE_OUTPUT_DIR = None  # raises AttributeError
        with pytest.raises(Exception):
            default_experiment.start()
        captured = capsys.readouterr()  # Catch std out
        finish_experiment_mock.assert_called_once_with(True, False)
        mock_logger.error.assert_called_once_with("AttributeError: 'NoneType' object has no attribute 'endswith'")

    @patch("ExperimentRunner.Experiment.Experiment.walk_to_list")
    @patch('ExperimentRunner.Experiment.Experiment.finish_experiment')
    def test_start_interupt(self, finish_experiment_mock, walk_to_list_mock, default_experiment):
        paths.BASE_OUTPUT_DIR = "test"
        walk_to_list_mock.side_effect = KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            default_experiment.start()
        finish_experiment_mock.assert_called_once_with(False, True)

    @patch("ExperimentRunner.Experiment.walk")
    @patch("ExperimentRunner.Experiment.Experiment.get_experiment")
    @patch('ExperimentRunner.Experiment.Experiment.run_experiment')
    @patch('ExperimentRunner.Experiment.Experiment.save_progress')
    @patch("ExperimentRunner.Experiment.Experiment.walk_to_list")
    @patch('ExperimentRunner.Experiment.Experiment.finish_experiment')
    def test_start_experiment_finished(self, finish_experiment_mock, walk_to_list_mock, save_progress_mock,
                                       run_experiment_mock, get_experiment_mock, walk_mock, default_experiment):
        paths.BASE_OUTPUT_DIR = "test"
        mock_walk_to_list_result = Mock()
        walk_to_list_mock.return_value = mock_walk_to_list_result
        mock_walk_result = Mock()
        walk_mock.return_value = mock_walk_result
        mock_progress = Mock()
        mock_progress.experiment_finished_check.return_value = True
        default_experiment.progress = mock_progress

        default_experiment.start()

        assert get_experiment_mock.call_count == run_experiment_mock.call_count == save_progress_mock.call_count == 0
        walk_to_list_mock.assert_called_once_with(mock_walk_result)
        finish_experiment_mock.assert_called_once_with(False, False)

    @patch("ExperimentRunner.Experiment.walk")
    @patch("ExperimentRunner.Experiment.Experiment.get_experiment")
    @patch('ExperimentRunner.Experiment.Experiment.run_experiment')
    @patch('ExperimentRunner.Experiment.Experiment.save_progress')
    @patch("ExperimentRunner.Experiment.Experiment.walk_to_list")
    @patch('ExperimentRunner.Experiment.Experiment.finish_experiment')
    def test_start_experiment_one_run(self, finish_experiment_mock, walk_to_list_mock, save_progress_mock,
                                      run_experiment_mock, get_experiment_mock, walk_mock, default_experiment):
        paths.BASE_OUTPUT_DIR = "test"
        mock_walk_to_list_result = Mock()
        walk_to_list_mock.return_value = mock_walk_to_list_result
        mock_walk_result = Mock()
        walk_mock.return_value = mock_walk_result
        mock_progress = Mock()
        mock_progress.experiment_finished_check.side_effect = [False, True]
        default_experiment.progress = mock_progress
        mock_get_experiment_result = Mock()
        get_experiment_mock.return_value = mock_get_experiment_result
        mock_manager = Mock()
        mock_manager.attach_mock(walk_mock, 'walk_mock_managed')
        mock_manager.attach_mock(walk_to_list_mock, 'walk_to_list_managed')
        mock_manager.attach_mock(mock_progress, 'mock_progress_managed')
        mock_manager.attach_mock(get_experiment_mock, 'get_experiment_managed')
        mock_manager.attach_mock(run_experiment_mock, 'run_experiment_managed')
        mock_manager.attach_mock(save_progress_mock, 'save_progress_managed')
        mock_manager.attach_mock(finish_experiment_mock, 'finish_experiment_managed')

        default_experiment.start()
        expected_calls = [call.walk_mock_managed(os.path.join('test', 'data')),
                          call.walk_to_list_managed(mock_walk_result),
                          call.mock_progress_managed.experiment_finished_check(),
                          call.get_experiment_managed(),
                          call.run_experiment_managed(mock_get_experiment_result),
                          call.save_progress_managed(),
                          call.mock_progress_managed.experiment_finished_check(),
                          call.finish_experiment_managed(False, False)]
        assert mock_manager.mock_calls == expected_calls

    @patch("ExperimentRunner.Experiment.walk")
    @patch("ExperimentRunner.Experiment.Experiment.get_experiment")
    @patch('ExperimentRunner.Experiment.Experiment.run_experiment')
    @patch('ExperimentRunner.Experiment.Experiment.save_progress')
    @patch("ExperimentRunner.Experiment.Experiment.walk_to_list")
    @patch('ExperimentRunner.Experiment.Experiment.finish_experiment')
    def test_start_experiment_multiple_runs(self, finish_experiment_mock, walk_to_list_mock, save_progress_mock,
                                            run_experiment_mock, get_experiment_mock, walk_mock, default_experiment):
        paths.BASE_OUTPUT_DIR = "test"
        mock_walk_to_list_result = Mock()
        walk_to_list_mock.return_value = mock_walk_to_list_result
        mock_walk_result = Mock()
        walk_mock.return_value = mock_walk_result
        mock_progress = Mock()
        mock_progress.experiment_finished_check.side_effect = [False] * 9 + [True]
        default_experiment.progress = mock_progress
        mock_get_experiment_result = Mock()
        get_experiment_mock.return_value = mock_get_experiment_result

        default_experiment.start()

        assert get_experiment_mock.call_count == run_experiment_mock.call_count == save_progress_mock.call_count == 9


class TestWebExperiment(object):
    @pytest.fixture()
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def web_experiment(self, device, check_dependencies):
        device.return_value = None
        device_config = {'devices': 'fake_device'}
        return WebExperiment(device_config, None, False)

    @patch('ExperimentRunner.BrowserFactory.BrowserFactory.get_browser')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_empty_config(self, device, check_dependencies, get_browser):
        mock_browser = Mock()
        get_browser.return_value = mock_browser

        device.return_value = None
        device_config = {'devices': 'fake_device'}
        web_experiment = WebExperiment(device_config, None, False)

        assert check_dependencies.call_count == 2
        assert web_experiment.duration == 0
        get_browser.assert_called_once_with('chrome')
        mock_browser.assert_called_once_with(device_config)

    @patch('ExperimentRunner.BrowserFactory.BrowserFactory.get_browser')
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def test_init_nom_empty_config(self, device, check_dependencies, get_browser):
        device.return_value = None
        device_config = {'devices': 'fake_device', 'browsers': ['firefox', 'opera'], 'duration': 1000}
        web_experiment = WebExperiment(device_config, None, False)

        assert check_dependencies.call_count == 2
        assert web_experiment.duration == 1
        assert len(web_experiment.browsers) == 2
        expected_calls = [call('firefox'), call()(device_config), call('opera'), call()(device_config)]
        assert get_browser.mock_calls == expected_calls

    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_run')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.before_close')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.stop_profiling')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.interaction')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.start_profiling')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_launch')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.before_run')
    def test_run(self, before_run, after_launch, start_profiling, interaction, stop_profiling, before_close, after_run,
                 web_experiment):
        mock_device = Mock()
        path = "test/path"
        run = 123456789
        mock_browser = Mock()
        mock_browser.to_string.return_value = 'chrome'
        web_experiment.browsers = [mock_browser]
        web_experiment.run(mock_device, path, run, 'chrome')

        mock_manager = Mock()
        mock_manager.attach_mock(before_run, "before_run_managed")
        mock_manager.attach_mock(after_launch, "after_launch_managed")
        mock_manager.attach_mock(start_profiling, "start_profiling_managed")
        mock_manager.attach_mock(interaction, "interaction_managed")
        mock_manager.attach_mock(stop_profiling, "stop_profiling_managed")
        mock_manager.attach_mock(before_close, "before_close_managed")
        mock_manager.attach_mock(after_run, "after_run_managed")

        web_experiment.run(mock_device, path, run, 'chrome')

        expected_calls = [call.before_run_managed(mock_device, path, run, mock_browser),
                          call.after_launch_managed(mock_device, path, run, mock_browser),
                          call.start_profiling_managed(mock_device, path, run, mock_browser),
                          call.interaction_managed(mock_device, path, run, mock_browser),
                          call.stop_profiling_managed(mock_device, path, run, mock_browser),
                          call.before_close_managed(mock_device, path, run, mock_browser),
                          call.after_run_managed(mock_device, path, run, mock_browser)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.WebExperiment.WebExperiment.after_last_run')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.aggregate_subject')
    def test_last_run_false(self, aggregate_subject, after_last_run, web_experiment):
        mock_progress = Mock()
        mock_progress.subject_finished.return_value = False
        web_experiment.progress = mock_progress
        fake_dict = {'device': 'fake_device', 'path': 'test/path', 'browser': 'fake_browser'}

        web_experiment.last_run_subject(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'],
                                                               fake_dict['browser'])
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
        mock_manager = Mock()
        mock_manager.attach_mock(after_last_run, "after_last_run_managed")
        mock_manager.attach_mock(aggregate_subject, "aggregate_subject_managed")

        web_experiment.last_run_subject(fake_dict)

        mock_progress.subject_finished.assert_called_once_with(fake_dict['device'], fake_dict['path'],
                                                               fake_dict['browser'])
        expected_calls = [call.after_last_run_managed(mock_device, fake_dict['path']),
                          call.aggregate_subject_managed()]
        assert mock_manager.mock_calls == expected_calls

    def test_prepare_output_dir(self, tmpdir, web_experiment):
        paths.BASE_OUTPUT_DIR = str(tmpdir)
        fake_dict = {'device': 'fake_device', 'path': 'fake_path', 'browser': 'fake_browser'}

        web_experiment.prepare_output_dir(fake_dict)

        assert os.path.isdir(paths.OUTPUT_DIR)
        assert paths.OUTPUT_DIR == os.path.join(paths.BASE_OUTPUT_DIR, 'data', 'fake_device', 'fake_path',
                                                'fake_browser')

    @patch('ExperimentRunner.Experiment.Experiment.before_run_subject')
    def test_before_run_subject(self, before_run_subject, web_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        web_experiment.before_run_subject(mock_device, path, *args, **kwargs)

        before_run_subject.assert_called_once_with(mock_device, path)

    @patch('time.sleep')
    @patch('ExperimentRunner.Experiment.Experiment.before_run')
    def test_before_run(self, before_run, sleep, web_experiment):
        mock_browser = Mock()
        args = (mock_browser, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 'id'
        current_activity = "playing euro truck simulator 2"
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 123456789
        mock_manager = Mock()
        mock_manager.attach_mock(before_run, "before_run_managed")
        mock_manager.attach_mock(mock_browser, "mock_browser_managed")
        mock_manager.attach_mock(sleep, "sleep_managed")

        web_experiment.before_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.before_run_managed(mock_device, path, run),
                          call.mock_browser_managed.start(mock_device),
                          call.sleep_managed(5)]
        assert mock_manager.mock_calls == expected_calls

    @patch('time.sleep')
    @patch('ExperimentRunner.Experiment.Experiment.interaction')
    def test_interaction(self, interaction, sleep, web_experiment):
        mock_browser = Mock()
        args = (mock_browser, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 123456789
        mock_manager = Mock()
        mock_manager.attach_mock(mock_browser, "mock_browser_managed")
        mock_manager.attach_mock(sleep, "sleep_managed")
        mock_manager.attach_mock(interaction, "interaction_managed")

        web_experiment.interaction(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.mock_browser_managed.load_url(mock_device, path),
                          call.sleep_managed(5),
                          call.interaction_managed(mock_device, path, run, *args, **kwargs),
                          call.sleep_managed(web_experiment.duration)]
        assert mock_manager.mock_calls == expected_calls

    @patch('time.sleep')
    @patch('ExperimentRunner.Experiment.Experiment.after_run')
    def test_after_run(self, after_run,  sleep, web_experiment):
        mock_browser = Mock()
        args = (mock_browser, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 'id'
        current_activity = "playing euro truck simulator 2"
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 123456789
        mock_manager = Mock()
        mock_manager.attach_mock(mock_browser, "mock_browser_managed")
        mock_manager.attach_mock(sleep, "sleep_managed")
        mock_manager.attach_mock(after_run, "after_run_managed")

        web_experiment.after_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.mock_browser_managed.stop(mock_device, clear_data=True),
                          call.sleep_managed(3),
                          call.after_run_managed(mock_device, path, run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    def test_after_last_run(self, after_last_run, web_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        web_experiment.after_last_run(mock_device, path, *args, **kwargs)

        after_last_run.assert_called_once_with(mock_device, path, *args, **kwargs)

    @patch('ExperimentRunner.Browsers.Browser.Browser.stop')
    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    def test_cleanup_empty_browsers(self, cleanup, stop, web_experiment):
        mock_device = Mock()
        web_experiment.browsers = []
        web_experiment.cleanup(mock_device)

        cleanup.assert_called_once_with(mock_device)
        assert stop.call_count == 0

    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    def test_cleanup_non_empty_browsers(self, cleanup, web_experiment):
        mock_device = Mock()
        mock_browser = Mock()
        fake_browsers = []
        for _ in range(5):
            fake_browsers.append(mock_browser)
        web_experiment.browsers = fake_browsers
        web_experiment.cleanup(mock_device)

        cleanup.assert_called_once_with(mock_device)
        assert mock_browser.stop.call_count == 5
        for mock_call in mock_browser.stop.mock_calls:
            assert mock_call == call(mock_device, clear_data=True)


class TestNativeExperiment(object):
    @pytest.fixture()
    @patch('ExperimentRunner.Tests.check_dependencies')
    @patch('ExperimentRunner.Devices.Devices.__init__')
    def native_experiment(self, device, check_dependencies):
        device.return_value = None
        device_config = {'devices': 'fake_device'}
        return NativeExperiment(device_config, None, False)

    @patch('os.path.isfile')
    @patch('ExperimentRunner.Experiment.Experiment.__init__')
    def test_init_empty_config(self, experiment, isfile):
        native_experiment = NativeExperiment({}, None, False)

        experiment.assert_called_once_with({}, None, False)
        assert native_experiment.duration == 0
        assert isfile.call_count == 0

    @patch('os.path.isfile')
    @patch('ExperimentRunner.Experiment.Experiment.__init__')
    def test_init_non_empty_config_all_files_found(self, experiment, isfile):
        test_paths = ['path1', 'path2', 'path3']
        config = {'paths': test_paths, 'duration': 1000}
        isfile.return_value = True

        native_experiment = NativeExperiment(config, None, False)

        experiment.assert_called_once_with(config, None, False)
        assert native_experiment.duration == 1
        assert isfile.call_count == 3
        isfile.has_calls([call(test_paths[0]), call(test_paths[1]), call(test_paths[2])])

    @patch('os.path.isfile')
    @patch('ExperimentRunner.Experiment.Experiment.__init__')
    def test_init_non_empty_config_file_not_found(self, experiment, isfile):
        test_paths = ['path1']
        config = {'paths': test_paths}
        isfile.return_value = False
        with pytest.raises(ConfigError):
            NativeExperiment(config, None, False)

        experiment.assert_called_once_with(config, None, False)
        isfile.assert_called_once_with(test_paths[0])

    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    def test_cleanup_app_not_installed(self, cleanup, native_experiment):
        mock_device = Mock()
        mock_device.get_app_list.return_value = []
        native_experiment.package = 'com.fake.package'

        native_experiment.cleanup(mock_device)

        cleanup.assert_called_once_with(mock_device)
        assert mock_device.uninstall.call_count == 0
        mock_device.get_app_list.assert_called_once()

    @patch('ExperimentRunner.Experiment.Experiment.cleanup')
    def test_cleanup_app_installed(self, cleanup, native_experiment):
        mock_device = Mock()
        mock_device.get_app_list.return_value = ['com.mock.package1', 'com.mock.package2', 'com.mock.package3']
        native_experiment.package = 'com.mock.package2'

        native_experiment.cleanup(mock_device)

        cleanup.assert_called_once_with(mock_device)
        mock_device.uninstall.assert_called_once_with('com.mock.package2')
        mock_device.get_app_list.assert_called_once()

    @patch('ExperimentRunner.Experiment.Experiment.before_experiment')
    def test_before_experiment(self, before_experiment, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'

        native_experiment.before_experiment(mock_device, path, *args, **kwargs)

        before_experiment.assert_called_once_with(mock_device)

    @patch('ExperimentRunner.Experiment.Experiment.before_run_subject')
    def test_before_run_subject_pre_app_installed(self, before_run_subject, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        test_package = 'com.test.app'
        path = os.path.join(test_package)
        mock_device.get_app_list.return_value = [test_package]
        native_experiment.pre_installed_apps = ['com.test.app']

        native_experiment.before_run_subject(mock_device, path, *args, **kwargs)

        before_run_subject.assert_called_once_with(mock_device, path)
        assert mock_device.install.call_count == 0
        assert mock_device.get_app_list.call_count == 0
        assert native_experiment.package == 'com.test.app'

    @patch('ExperimentRunner.Experiment.Experiment.before_run_subject')
    def test_before_run_subject_in_app_list(self, before_run_subject, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        test_package = 'com.test.app.apk'
        path = os.path.join('test', test_package)
        mock_device.get_app_list.return_value = [test_package]

        native_experiment.before_run_subject(mock_device, path, *args, **kwargs)

        before_run_subject.assert_called_once_with(mock_device, path)
        mock_device.get_app_list.assert_called_once()
        assert mock_device.install.call_count == 0
        assert native_experiment.package == 'com.test.app'

    @patch('ExperimentRunner.Experiment.Experiment.before_run_subject')
    def test_before_run_subject_app_not_installed(self, before_run_subject, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        test_package_file = 'com.test.app.apk'
        path = os.path.join('test', test_package_file)
        mock_device.get_app_list.return_value = []

        native_experiment.before_run_subject(mock_device, path, *args, **kwargs)

        before_run_subject.assert_called_once_with(mock_device, path)
        mock_device.get_app_list.assert_called_once()
        mock_device.install.assert_called_once_with(path)
        assert native_experiment.package == 'com.test.app'

    @patch('ExperimentRunner.Experiment.Experiment.after_launch')
    @patch('ExperimentRunner.Experiment.Experiment.before_run')
    def test_before_run(self, before_run, after_launch, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 'id'
        current_activity = "playing euro truck simulator 2"
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 123456789
        native_experiment.package = 'com.test.app'
        mock_manager = Mock()
        mock_manager.attach_mock(before_run, 'before_run_managed')
        mock_manager.attach_mock(mock_device, 'mock_device_managed')
        mock_manager.attach_mock(after_launch, 'after_launch_managed')

        native_experiment.before_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.before_run_managed(mock_device, path, run),
                          call.mock_device_managed.launch_package('com.test.app'),
                          call.after_launch_managed(mock_device, path, run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('time.sleep')
    @patch('ExperimentRunner.Profilers.Profilers.start_profiling')
    def test_start_profiling(self, start_profiling, sleep, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        path = 'test/path'
        run = 123456789
        native_experiment.package = 'com.test.app'
        mock_manager = Mock()
        mock_manager.attach_mock(start_profiling, 'start_profiling_managed')
        mock_manager.attach_mock(sleep, 'sleep_managed')

        native_experiment.start_profiling(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.start_profiling_managed(mock_device, app='com.test.app'),
                          call.sleep_managed(native_experiment.duration)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.after_run')
    def test_after_run(self, after_run, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.id = 'id'
        current_activity = "playing euro truck simulator 2"
        mock_device.current_activity.return_value = current_activity
        path = 'test/path'
        run = 123456789
        native_experiment.package = 'com.test.app'
        mock_manager = Mock()
        mock_manager.attach_mock(mock_device, 'mock_device_managed')
        mock_manager.attach_mock(after_run, 'after_run_managed')

        native_experiment.after_run(mock_device, path, run, *args, **kwargs)

        expected_calls = [call.mock_device_managed.current_activity(),
                          call.mock_device_managed.force_stop(native_experiment.package),
                          call.after_run_managed(mock_device, path, run)]
        assert mock_manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    def test_after_last_run_pre_installed(self, after_last_run, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.get_app_list.return_value = ['com.test.app']
        path = 'test/path'
        native_experiment.pre_installed_apps = ['com.test.app']
        native_experiment.package = 'com.test.app'


        native_experiment.after_last_run(mock_device, path, *args, **kwargs)

        assert mock_device.uninstall.call_count == 0
        assert native_experiment.package is None

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    def test_after_last_run_not_installed(self, after_last_run, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.get_app_list.return_value = []
        path = 'test/path'
        native_experiment.pre_installed_apps = ['com.test.app']
        native_experiment.package = 'com.test.app'


        native_experiment.after_last_run(mock_device, path, *args, **kwargs)

        assert mock_device.uninstall.call_count == 0
        assert native_experiment.package is None

    @patch('ExperimentRunner.Experiment.Experiment.after_last_run')
    def test_after_last_run_not_pre_installed(self, after_last_run, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()
        mock_device.get_app_list.return_value = ['com.test.app']
        path = 'test/path'
        native_experiment.pre_installed_apps = []
        native_experiment.package = 'com.test.app'
        mock_manager = Mock()
        mock_manager.attach_mock(after_last_run, 'after_last_run_managed')
        mock_manager.attach_mock(mock_device, 'mock_device_managed')

        native_experiment.after_last_run(mock_device, path, *args, **kwargs)

        expected_calls = [call.after_last_run_managed(mock_device, path),
                          call.mock_device_managed.get_app_list(),
                          call.mock_device_managed.uninstall('com.test.app')]
        assert mock_manager.mock_calls == expected_calls
        assert native_experiment.package is None

    @patch('ExperimentRunner.Experiment.Experiment.after_experiment')
    def test_after_experiment(self, after_experiment, native_experiment):
        args = (1, 2, 3)
        kwargs = {'arg1': 1, 'arg2': 2}
        mock_device = Mock()

        native_experiment.after_experiment(mock_device, *args, **kwargs)

        after_experiment.assert_called_once_with(mock_device)


class TestExperimentFactory(object):
    def test_init(self):
        ExperimentFactory()

    @patch('ExperimentRunner.Progress.Progress.__init__')
    @patch('ExperimentRunner.NativeExperiment.NativeExperiment.__init__')
    def test_from_json_native_progress(self, native_experiment, progress_init, tmpdir):
        native_experiment.return_value = None
        paths.OUTPUT_DIR = os.path.join(str(tmpdir), 'output')
        makedirs(paths.OUTPUT_DIR)
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write('{"type":"native"}')
        mock_progress = Mock()

        experiment = ExperimentFactory.from_json(str(tmp_file), mock_progress)

        assert isinstance(experiment, NativeExperiment)
        native_experiment.assert_called_once_with({'type': 'native'}, mock_progress, True)
        assert progress_init.call_count == 0
        assert os.path.isfile(os.path.join(paths.OUTPUT_DIR, 'config.json'))
        assert filecmp.cmp(str(tmp_file), os.path.join(paths.OUTPUT_DIR, 'config.json'), False)

    @patch('ExperimentRunner.Progress.Progress.__init__')
    @patch('ExperimentRunner.WebExperiment.WebExperiment.__init__')
    def test_from_json_web_progress(self, web_experiment, progress_init, tmpdir):
        web_experiment.return_value = None
        paths.OUTPUT_DIR = os.path.join(str(tmpdir), 'output')
        makedirs(paths.OUTPUT_DIR)
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write('{"type":"web"}')
        mock_progress = Mock()

        experiment = ExperimentFactory.from_json(str(tmp_file), mock_progress)

        assert isinstance(experiment, WebExperiment)
        web_experiment.assert_called_once_with({'type': 'web'}, mock_progress, True)
        assert progress_init.call_count == 0
        assert os.path.isfile(os.path.join(paths.OUTPUT_DIR, 'config.json'))
        assert filecmp.cmp(str(tmp_file), os.path.join(paths.OUTPUT_DIR, 'config.json'), False)

    @patch('ExperimentRunner.Progress.Progress.__init__')
    @patch('ExperimentRunner.Experiment.Experiment.__init__')
    def test_from_json_experiment_progress(self, mock_experiment, progress_init, tmpdir):
        mock_experiment.return_value = None
        paths.OUTPUT_DIR = os.path.join(str(tmpdir), 'output')
        makedirs(paths.OUTPUT_DIR)
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write('{"type":"regular"}')
        mock_progress = Mock()

        experiment = ExperimentFactory.from_json(str(tmp_file), mock_progress)

        assert isinstance(experiment, Experiment)
        mock_experiment.assert_called_once_with({'type': 'regular'}, mock_progress, True)
        assert progress_init.call_count == 0
        assert os.path.isfile(os.path.join(paths.OUTPUT_DIR, 'config.json'))
        assert filecmp.cmp(str(tmp_file), os.path.join(paths.OUTPUT_DIR, 'config.json'), False)

    @patch('ExperimentRunner.Progress.Progress.__init__')
    @patch('ExperimentRunner.Experiment.Experiment.__init__')
    def test_from_json_experiment_no_progres(self, mock_experiment, mock_progress, tmpdir):
        mock_experiment.return_value = None
        mock_progress.return_value = None
        paths.OUTPUT_DIR = os.path.join(str(tmpdir), 'output')
        makedirs(paths.OUTPUT_DIR)
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write('{"type":"regular"}')

        experiment = ExperimentFactory.from_json(str(tmp_file), None)

        mock_progress.assert_called_once_with(config_file=str(tmp_file), config={'type': 'regular'},
                                              load_progress=False)
        mock_experiment.assert_called_once()
        assert isinstance(experiment, Experiment)
        assert isinstance(mock_experiment.mock_calls[0][1][1], Progress)
        assert os.path.isfile(os.path.join(paths.OUTPUT_DIR, 'config.json'))
        assert filecmp.cmp(str(tmp_file), os.path.join(paths.OUTPUT_DIR, 'config.json'), False)

    @patch('ExperimentRunner.Progress.Progress.__init__')
    @patch('tests.PluginTests.PluginTests.__init__')
    def test_from_json_plugintester_no_progres(self, mock_experiment, mock_progress, tmpdir):
        mock_experiment.return_value = None
        mock_progress.return_value = None
        paths.OUTPUT_DIR = os.path.join(str(tmpdir), 'output')
        makedirs(paths.OUTPUT_DIR)
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write('{"type":"plugintest", "devices": {"nexus6p": {}}}')
        config = OrderedDict([(u'type', u'plugintest'), (u'devices', OrderedDict([(u'nexus6p', OrderedDict())]))])
        experiment = ExperimentFactory.from_json(str(tmp_file), None)

        assert mock_progress.call_count == 0
        mock_experiment.assert_called_once_with(config)
        assert isinstance(experiment, PluginTests)
        assert os.path.isfile(os.path.join(paths.OUTPUT_DIR, 'config.json'))
        assert filecmp.cmp(str(tmp_file), os.path.join(paths.OUTPUT_DIR, 'config.json'), False)