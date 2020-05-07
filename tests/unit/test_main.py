import imp
import logging
import os.path as op
import sys

import pytest

import paths
from mock import patch, Mock, call
from AndroidRunner.util import makedirs
main = imp.load_source('runner_main', op.join(op.dirname(paths.__file__), '__main__.py'))


class TestRunnerMain(object):

    @patch('runner_main.set_stdout_logger')
    @patch('runner_main.set_file_logger')
    @patch('logging.getLogger')
    def test_setup_logger(self, get_logger_mock, set_file_logger_mock, set_stdout_logger_mock):
        test_filename = "asdfvgbnsaq"
        logger_mock = Mock()
        get_logger_mock.return_value = logger_mock
        file_logger_mock = Mock()
        set_file_logger_mock.return_value = file_logger_mock
        stdout_logger_mock = Mock()
        set_stdout_logger_mock.return_value = stdout_logger_mock

        result_logger = main.setup_logger(test_filename)

        logger_mock.setLevel.assert_called_once_with(logging.DEBUG)
        expected_calls = [call(file_logger_mock), call(stdout_logger_mock)]
        assert logger_mock.addHandler.mock_calls == expected_calls
        set_file_logger_mock.assert_called_once_with(op.join(test_filename, 'experiment.log'))
        set_stdout_logger_mock.assert_called_once_with()
        assert result_logger == logger_mock

    @patch('logging.Formatter')
    @patch('logging.FileHandler')
    def test_set_file_logger(self, filehandler_mock, formatter_mock):
        test_filename = "asdfvgbnsaq"
        handler_mock = Mock()
        filehandler_mock.return_value = handler_mock
        formatter_result_mock = Mock()
        formatter_mock.return_value = formatter_result_mock

        result_file_handler = main.set_file_logger(test_filename)

        assert result_file_handler == handler_mock
        handler_mock.setLevel.assert_called_once_with(logging.DEBUG)
        handler_mock.setFormatter.assert_called_once_with(formatter_result_mock)
        filehandler_mock.assert_called_once_with(test_filename)

    @patch('logging.Formatter')
    @patch('logging.StreamHandler')
    def test_set_stdout_logger(self, streamhandler_mock, formatter_mock):
        handler_mock = Mock()
        streamhandler_mock.return_value = handler_mock
        formatter_result_mock = Mock()
        formatter_mock.return_value = formatter_result_mock

        result_file_handler = main.set_stdout_logger()

        assert result_file_handler == handler_mock
        handler_mock.setLevel.assert_called_once_with(logging.INFO)
        handler_mock.setFormatter.assert_called_once_with(formatter_result_mock)
        streamhandler_mock.assert_called_once_with(sys.stdout)

    def test_setup_paths(self, tmpdir):
        temp_config_dir = op.join(str(tmpdir), 'config')
        makedirs(temp_config_dir)
        temp_config_file = op.join(temp_config_dir, 'config.json')
        open(temp_config_file, "w+")
        temp_log_dir = op.join(str(tmpdir), 'log')

        main.setup_paths(temp_config_file, temp_log_dir)

        assert paths.CONFIG_DIR == op.dirname(temp_config_file)
        assert op.isdir(temp_log_dir)
        assert paths.OUTPUT_DIR == temp_log_dir
        assert paths.BASE_OUTPUT_DIR == temp_log_dir
        assert op.join(paths.ROOT_DIR, 'AndroidRunner') in sys.path

    def test_parse_arguments_empty_args(self, capsys):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main.parse_arguments([])
        capsys.readouterr()  # Catch print
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 2

    def test_parse_arguments_one_args(self, capsys):
        fake_filename = 'test/file/name'
        result_args = main.parse_arguments([fake_filename])

        assert len(result_args) == 1
        assert result_args.get('file') == fake_filename

    def test_parse_arguments_both_args(self, capsys):
        fake_filename = 'test/file/name'
        fake_progress_file = 'path/to/progress'
        result_args = main.parse_arguments([fake_filename, '--progress', fake_progress_file])

        assert len(result_args) == 2
        assert result_args.get('file') == fake_filename
        assert result_args.get('progress') == fake_progress_file

    def test_set_progress_new(self, tmpdir):
        temp_config_file = op.join(str(tmpdir), 'fake_config.json')
        open(temp_config_file, "w+")
        args = {"file": temp_config_file}
        result_progress, result_log_dir = main.set_progress(args)
        assert result_progress is None
        assert result_log_dir.startswith(op.join(op.dirname(temp_config_file), 'output'))

    @patch('AndroidRunner.Progress.Progress.get_output_dir')
    @patch('AndroidRunner.Progress.Progress.__init__')
    def test_set_progress_restart(self, mock_progress_init, mock_progress_get_output, tmpdir):
        temp_config_file = op.join(str(tmpdir), 'fake_config.json')
        temp_progress_file = op.join(str(tmpdir), 'fake_progress.xml')
        open(temp_config_file, "w+")
        open(temp_progress_file, "w+")
        mock_progress_init.return_value = None
        mock_output_dir = Mock()
        mock_progress_get_output.return_value = mock_output_dir
        args = {"file": temp_config_file, "progress": temp_progress_file}

        result_progress, result_log_dir = main.set_progress(args)

        mock_progress_init.assert_called_once_with(progress_file=temp_progress_file,
                                                   config_file=temp_config_file, load_progress=True)
        assert result_log_dir == mock_output_dir

    @patch('runner_main.parse_arguments')
    @patch('runner_main.set_progress')
    @patch('runner_main.setup_paths')
    @patch('runner_main.setup_logger')
    @patch('AndroidRunner.ExperimentFactory.ExperimentFactory.from_json')
    def test_main_exception(self, from_json_mock, setup_logger_mock, setup_paths_mock, set_progress_mock,
                            parse_arguments_mock, tmpdir):
        setup_paths_mock.return_value = None
        temp_progress_file = op.join(str(tmpdir), 'fake_progress.xml')
        open(temp_progress_file, "w+")
        from_json_mock.side_effect = Exception()
        parse_arguments_mock.return_value = {'file': temp_progress_file}
        set_progress_mock.return_value = None, None
        mock_logger = Mock()
        setup_logger_mock.return_value = mock_logger

        main.main()

        from_json_mock.assert_called_once_with(temp_progress_file, None)
        assert mock_logger.error.call_count == 2
        assert mock_logger.error.mock_calls[1] == call('An error occurred, the experiment has been stopped. '
                                                       'To continue, add progress file argument to experiment startup: '
                                                       '--progress  No progress file created')

    @patch('runner_main.parse_arguments')
    @patch('runner_main.set_progress')
    @patch('runner_main.setup_paths')
    @patch('runner_main.setup_logger')
    @patch('AndroidRunner.ExperimentFactory.ExperimentFactory.from_json')
    def test_main_interrupt(self, from_json_mock, setup_logger_mock, setup_paths_mock, set_progress_mock,
                            parse_arguments_mock, tmpdir):
        setup_paths_mock.return_value = None
        temp_progress_file = op.join(str(tmpdir), 'fake_progress.xml')
        open(temp_progress_file, "w+")
        from_json_mock.side_effect = KeyboardInterrupt
        parse_arguments_mock.return_value = {'file': temp_progress_file}
        mock_progress = Mock()
        mock_progress.get_progress_xml_file.return_value = "path/to/progress.xml"
        set_progress_mock.return_value = mock_progress, None
        mock_logger = Mock()
        setup_logger_mock.return_value = mock_logger

        main.main()

        from_json_mock.assert_called_once_with(temp_progress_file, mock_progress)
        assert mock_logger.error.call_count == 1
        assert mock_logger.error.mock_calls[0] == call('Experiment stopped by user. To continue,'
                                                       ' add progress file argument to experiment startup: '
                                                       '--progress path/to/progress.xml')

    @patch('runner_main.parse_arguments')
    @patch('runner_main.set_progress')
    @patch('runner_main.setup_paths')
    @patch('runner_main.setup_logger')
    @patch('AndroidRunner.ExperimentFactory.ExperimentFactory.from_json')
    def test_main_succes(self, from_json_mock, setup_logger_mock, setup_paths_mock, set_progress_mock,
                         parse_arguments_mock, tmpdir):
        setup_paths_mock.return_value = None
        temp_progress_file = op.join(str(tmpdir), 'fake_progress.xml')
        open(temp_progress_file, "w+")
        mock_experiment = Mock()
        from_json_mock.return_value = mock_experiment
        parse_arguments_mock.return_value = {'file': temp_progress_file}
        set_progress_mock.return_value = None, None
        mock_logger = Mock()
        setup_logger_mock.return_value = mock_logger

        main.main()

        from_json_mock.assert_called_once_with(temp_progress_file, None)
        mock_experiment.start.assert_called_once_with()
        assert mock_logger.error.call_count == 0
