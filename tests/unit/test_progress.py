import os
import os.path as op
from shutil import copyfile

import lxml.etree as et
import pytest
from mock import Mock, call, patch

import paths
from AndroidRunner.Progress import Progress
from AndroidRunner.util import load_json


class TestProgressSetup(object):
    @pytest.fixture()
    def test_config(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, "test_config.json")

    @pytest.fixture()
    def test_progress(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, 'test_progress.xml')

    @patch('AndroidRunner.Progress.Progress.write_progress_to_file')
    @patch('AndroidRunner.Progress.Progress.build_progress_xml')
    def test_progress_init(self, build_progress_mock, write_to_file_mock, tmp_path, test_config, test_progress):
        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        paths.OUTPUT_DIR = tmp_path.as_posix()
        build_progress_mock.return_value = et.fromstring(expected_xml)
        mock_manager = Mock()
        mock_manager.attach_mock(build_progress_mock, 'managed_build_progress')
        mock_manager.attach_mock(write_to_file_mock, 'managed_write_to_file')

        progress = Progress(config_file=test_config, config=load_json(test_config))

        expected_calls = [call.managed_build_progress(load_json(test_config), test_config),
                          call.managed_write_to_file()]
        assert mock_manager.mock_calls == expected_calls
        expected_lxml = et.fromstring(expected_xml)
        current_lxml = progress.progress_xml_content
        assert self.elements_equal(current_lxml, expected_lxml)

    @patch('AndroidRunner.Progress.Progress.check_config_hash')
    def test_progress_init_resume(self, check_hash_mock, tmp_path, test_config, test_progress):
        check_hash_mock.return_value = None
        progress = Progress(config_file=test_config, progress_file=test_progress, load_progress=True)
        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        expected_lxml = et.fromstring(expected_xml)
        current_lxml = progress.progress_xml_content
        assert self.elements_equal(current_lxml, expected_lxml)

    def elements_equal(self, e1, e2):
        if e1.tag != e2.tag:
            return False
        if e1.text != e2.text:
            return False
        if e1.tail != e2.tail:
            return False
        if e1.attrib != e2.attrib:
            return False
        if len(e1) != len(e2):
            return False
        return all(self.elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


class TestProgressMethods(object):
    @pytest.fixture()
    def test_config(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, "test_config.json")

    @pytest.fixture()
    def test_progress(self):
        fixture_dir = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        return op.join(fixture_dir, 'test_progress.xml')

    @pytest.fixture()
    def current_progress(self, tmp_path, test_config, test_progress):
        paths.OUTPUT_DIR = tmp_path.as_posix()
        progress = Progress(config_file=test_config, progress_file=test_progress, load_progress=True)
        progress.progress_xml_file = op.join(paths.OUTPUT_DIR, "progress.xml")
        copyfile(test_progress, progress.progress_xml_file)
        return progress

    @pytest.fixture()
    def config_web_dict(self):
        return {'devices': ['device1'], 'paths': ['path1'], 'type': 'web', 'browsers': ['browser1'], 'replications': 1}

    @pytest.fixture()
    def config_native_dict(self):
        return {'devices': ['device1'], 'paths': ['path1'], 'type': 'native', 'replications': 1}

    def elements_equal(self, e1, e2):
        if e1.tag != e2.tag:
            return False
        if e1.text != e2.text:
            return False
        if e1.tail != e2.tail:
            return False
        if e1.attrib != e2.attrib:
            return False
        if len(e1) != len(e2):
            return False
        return all(self.elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    @patch('AndroidRunner.Progress.Progress.run_to_dict')
    def test_ordered_next(self, run_to_dict, current_progress):
        run_to_dict.return_value = 0
        for _ in range(50):
            current_progress.get_next_run()
        unique_values = len(set(str(run_to_dict.mock_calls).
                                replace('[', '').replace(']', '').replace('\n', '').split(', ')))
        assert unique_values == 1

    @patch('AndroidRunner.Progress.Progress.run_to_dict')
    def test_random_next(self, run_to_dict, current_progress):
        for _ in range(50):
            current_progress.get_random_run()
        unique_values = len(set(str(run_to_dict.mock_calls).
                                replace('[', '').replace(']', '').replace('\n', '').split(', ')))
        assert unique_values > 1

    def test_get_progress_xml_file(self, current_progress, test_progress):
        progress_file = current_progress.get_progress_xml_file()
        assert op.isfile(progress_file)
        assert progress_file[-3:] == "xml"

        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        with open(progress_file, 'r') as f:
            progress_xml = f.read()
        expected_stripped = expected_xml.split("<outputDir>")[0] + expected_xml.split("</outputDir>")[1]
        result_stripped = progress_xml.split("<outputDir>")[0] + progress_xml.split("</outputDir>")[1]

        assert expected_stripped == result_stripped

    def test_write_progress_to_file(self, current_progress, test_progress):
        os.remove(current_progress.progress_xml_file)

        assert not op.isfile(current_progress.progress_xml_file)
        current_progress.write_progress_to_file()
        assert op.isfile(current_progress.progress_xml_file)

        with open(test_progress, 'r') as f:
            expected_xml = f.read()
        with open(current_progress.progress_xml_file, 'r') as f:
            progress_xml = f.read()
        expected_stripped = expected_xml.split("<outputDir>")[0] + expected_xml.split("</outputDir>")[1]
        result_stripped = progress_xml.split("<outputDir>")[0] + progress_xml.split("</outputDir>")[1]

        assert expected_stripped == result_stripped

    def test_file_to_hash(self, current_progress, test_config):
        expected_hash = "c563cc8583486714e40cf74b1fb98577"
        current_hash = current_progress.file_to_hash(test_config)
        assert current_hash == expected_hash

    @patch('AndroidRunner.Progress.Progress.file_to_hash')
    def test_check_config_hash_fail(self, file_to_hash_mock, current_progress, capsys, test_config, test_progress):
        file_to_hash_mock.return_value = '0'
        with pytest.raises(SystemExit) as wrapper_result:
            current_progress.check_config_hash(test_progress)

        # Prevent output during testing
        capsys.readouterr()
        assert wrapper_result.type == SystemExit

    @patch('AndroidRunner.Progress.Progress.file_to_hash')
    def test_check_config_hash_succes(self, file_to_hash_mock, current_progress):
        file_to_hash_mock.return_value = current_progress.progress_xml_content.find('configHash').text
        current_progress.check_config_hash(current_progress.get_progress_xml_file())

    @patch('AndroidRunner.Progress.Progress.get_run_count')
    def test_run_to_dict(self, get_run_count, current_progress):
        get_run_count.return_value = 1459
        run_dict = current_progress.run_to_dict(et.fromstring('<run runId="0"><device>device</device><path>path</path>'
                                                              '<browser>browser</browser><runCount>1</runCount></run>'))
        expected_dict = {'runId': '0', 'device': 'device', 'path': 'path', 'browser': 'browser', 'runCount': 1459}
        assert run_dict == expected_dict

    def test_build_subject_xml_web(self, current_progress):
        device = 'device1'
        path = 'path1'
        browser = 'browser1'
        subject_xml = current_progress.build_subject_xml(device, path, browser)
        expected_xml = '<device>device1</device><path>path1</path><browser>browser1</browser>'
        assert subject_xml == expected_xml

    def test_build_subject_xml_native(self, current_progress):
        device = 'device1'
        path = 'path1'
        subject_xml = current_progress.build_subject_xml(device, path)
        expected_xml = '<device>device1</device><path>path1</path>'
        assert subject_xml == expected_xml

    @patch('AndroidRunner.Progress.Progress.build_runs_xml')
    @patch('AndroidRunner.Progress.Progress.file_to_hash')
    def test_build_progress_xml(self, file_to_hash_mock, build_runs_xml_mock, current_progress):
        mock_config = Mock()
        mock_config_file = Mock()
        paths.OUTPUT_DIR = "test/dir"
        file_to_hash_mock.return_value = 'hash123'
        build_runs_xml_mock.return_value = "runs_xml"
        expected_xml = "<experiment><configHash>hash123</configHash><outputDir>test/dir</outputDir>" \
                       "<runsToRun>runs_xml</runsToRun><runsDone></runsDone></experiment>"
        expected_lxml = et.fromstring(expected_xml)
        build_progress = current_progress.build_progress_xml(mock_config, mock_config_file)
        assert self.elements_equal(expected_lxml, build_progress)
        file_to_hash_mock.assert_called_once_with(mock_config_file)
        build_runs_xml_mock.assert_called_once_with(mock_config)

    @patch('AndroidRunner.Progress.Progress.build_subject_xml')
    def test_build_runs_xml_web(self, build_subject_xml_mock, current_progress, config_web_dict):
        build_subject_xml_mock.return_value = "<device>device1</device><path>path1</path><browser>browser1</browser>"
        runs_xml_web = current_progress.build_runs_xml(config_web_dict)
        expected_runs_web = '<run runId="0"><device>device1</device><path>path1</path><browser>browser1</browser>' \
                            '<runCount>1</runCount></run>'
        assert runs_xml_web == expected_runs_web

    @patch('AndroidRunner.Progress.Progress.build_subject_xml')
    def test_build_runs_xml_non_web(self, build_subject_xml_mock, current_progress, config_native_dict):
        build_subject_xml_mock.return_value = "<device>device1</device><path>path1</path>"
        runs_xml_native = current_progress.build_runs_xml(config_native_dict)
        expected_runs_native = '<run runId="0"><device>device1</device><path>path1</path><runCount>1</runCount></run>'
        assert runs_xml_native == expected_runs_native

    def test_get_output_dir(self, current_progress):
        assert current_progress.get_output_dir() == "test/output/dir"

    def test_subject_first_web_first(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = []
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_first('fake_device', 'fake_path', 'fake_browser')
        assert subject_first is True

    def test_subject_first_native_first(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = []
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_first('fake_device', 'fake_path')
        assert subject_first is True

    def test_subject_first_web_not_first(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = ['not_empty']
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_first('fake_device', 'fake_path', 'fake_browser')
        assert subject_first is False

    def test_subject_first_native_not_first(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = ['not_empty']
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_first('fake_device', 'fake_path')
        assert subject_first is False

    def test_subject_finished_web_finished(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = []
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_finished('fake_device', 'fake_path', 'fake_browser')
        assert subject_first is True

    def test_subject_finished_native_finished(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = []
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_finished('fake_device', 'fake_path')
        assert subject_first is True

    def test_subject_finished_web_not_finished(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = ['not_empty']
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_finished('fake_device', 'fake_path', 'fake_browser')
        assert subject_first is False

    def test_subject_finished_native_not_finished(self, current_progress):
        mock_find_return_value = Mock()
        mock_find_return_value.xpath.return_value = ['not_empty']
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = mock_find_return_value
        current_progress.progress_xml_content = mock_progress_xml
        subject_first = current_progress.subject_finished('fake_device', 'fake_path')
        assert subject_first is False

    def test_run_finished(self, current_progress):
        runs_to_run_mock = Mock()
        runs_to_run_mock.findall.return_value = ['fake_element']
        runs_done_mock = Mock()
        mock_progress_xml = Mock()
        mock_progress_xml.find.side_effect = [runs_to_run_mock, runs_done_mock]
        current_progress.progress_xml_content = mock_progress_xml

        current_progress.run_finished(0)

        runs_to_run_mock.remove.assert_called_once_with('fake_element')
        runs_done_mock.append.assert_called_once_with('fake_element')

    def test_experiment_finished_check_true(self, current_progress):
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = et.fromstring('<runsToRun></runsToRun>')
        current_progress.progress_xml_content = mock_progress_xml
        experiment_finished = current_progress.experiment_finished_check()
        assert experiment_finished is True

    def test_experiment_finished_check_false(self, current_progress):
        experiment_finished = current_progress.experiment_finished_check()
        assert experiment_finished is False

    def test_device_first_true(self, current_progress):
        device_first = current_progress.device_first('nexus6p')
        assert device_first is True

    def test_device_first_false(self, current_progress):
        mock_progress_xml = Mock()
        mock_progress_xml.find.return_value = et.fromstring('<runsDone><run><device>device1</device></run></runsDone>')
        current_progress.progress_xml_content = mock_progress_xml
        device_first = current_progress.device_first('device1')
        assert device_first is False

    def test_device_finished_false(self, current_progress):
        device_finished = current_progress.device_finished('nexus6p')
        assert device_finished is False

    def test_device_finished_true(self, current_progress):
        device_finished = current_progress.device_finished('device1')
        assert device_finished is True

    def test_get_run_count_web(self, current_progress):
        device = 'nexus6p'
        path = 'https://google.com/'
        run_xml = et.fromstring('<run runId="0"><device>nexus6p</device>'
                                '<path>https://google.com/</path>'
                                '<browser>firefox</browser></run>')
        assert current_progress.get_run_count(run_xml, device, path) == 1

        for _ in range(2):
            run = current_progress.get_next_run()
            current_progress.run_finished(run['runId'])

        assert current_progress.get_run_count(run_xml, device, path) == 3

    def test_get_run_count_native(self, current_progress):
        device = 'nexus6p'
        path = 'https://google.com/'
        run_xml = et.fromstring('<run runId="0"><device>nexus6p</device><path>https://google.com/</path></run>')
        assert current_progress.get_run_count(run_xml, device, path) == 1
        run = current_progress.get_next_run()
        current_progress.run_finished(run['runId'])
        assert current_progress.get_run_count(run_xml, device, path) == 2
