import os
import os.path as op

import pytest
from mock import Mock, patch

import AndroidRunner.Tests as Tests
import AndroidRunner.util as util
import paths
import csv


class TestUtilClass(object):
    @pytest.fixture()
    def tmp_file(self, tmpdir):
        tmp_file = tmpdir.join('tmp.txt')
        tmp_file.write("test content")
        return str(tmp_file)
    @pytest.fixture()
    def fixture_dir(self):
        return op.join(op.dirname(op.abspath(__file__)), 'fixtures')

    def test_load_json_succes(self, tmp_file):
        fixtures = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        config = util.load_json(op.join(fixtures, 'test_config.json'))
        assert config['type'] == 'web'
        assert config['devices'] == ['nexus6p']
        assert config['randomization'] == 'False'
        assert config['replications'] == 3

    def test_load_json_file_format_error(self, tmp_file):
        fixtures = op.join(op.dirname(op.realpath(__file__)), "fixtures")
        with pytest.raises(util.FileFormatError) as except_result:
            util.load_json(op.join(fixtures, 'test_progress.xml'))
        assert op.join(fixtures, 'test_progress.xml') in str(except_result.value)

    def test_load_json_file_file_not_found(self, tmp_file):
        fixtures = op.join(op.dirname(op.realpath(__file__)), "fixtures")

        with pytest.raises(util.FileNotFoundError) as except_result:
            util.load_json(op.join(fixtures, 'fake_file.json'))
        assert "FileNotFoundError" in str(except_result.typename)

    def test_load_json_file_permission_denied(self, tmp_file):
        os.chmod(tmp_file, 0o222)
        with pytest.raises(IOError) as except_result:
            util.load_json(tmp_file)
        assert "Permission denied" in str(except_result.value)

    def test_makedirs_succes(self, tmpdir):
        dir_path = op.join(str(tmpdir), 'test1')
        assert op.isdir(dir_path) is False
        util.makedirs(dir_path)
        assert op.isdir(dir_path) is True

    def test_makedirs_fail_already_exist(self, tmpdir):
        dir_path = op.join(str(tmpdir), 'test1')
        assert op.isdir(dir_path) is False
        util.makedirs(dir_path)
        util.makedirs(dir_path)
        assert op.isdir(dir_path) is True
        files_in_path = [f for f in os.listdir(str(tmpdir)) if os.path.isdir(os.path.join(str(tmpdir), f))]

        assert len(files_in_path) == 1

    def test_makedirs_fail(self, tmpdir):
        os.chmod(str(tmpdir), 0o444)
        dir_path = op.join(str(tmpdir), 'test2')
        assert op.isdir(dir_path) is False
        with pytest.raises(OSError) as except_result:
            util.makedirs(dir_path)
        assert "Permission denied" in str(except_result.value)
        assert op.isdir(dir_path) is False

    def test_slugify(self):
        string1 = "asdfghjkl.test"
        assert util.slugify_dir(string1) == string1.replace(".", "-")

        string2 = "ASDFGHJKL"
        assert util.slugify_dir(string2) == string2.lower()

        string3 = "@#$%^&*"
        assert util.slugify_dir(string3) == ""

        string4 = "a b c d e f"
        assert util.slugify_dir(string4) == string4.replace(" ", "-")

    def test_write_to_file(self, tmpdir):
        tmp_file = op.join(str(tmpdir), 'test_output.csv')
        test_rows = [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value3', 'key2': 'value4'}]
        util.write_to_file(tmp_file, test_rows)

        assert op.isfile(tmp_file)
        assert self.csv_reader_to_table(tmp_file) == list(
            [['key1', 'key2'], ['value1', 'value2'], ['value3', 'value4']])

    def test_list_subdir(self, fixture_dir):
        test_dir = op.join(fixture_dir, 'test_dir_struct')

        result_subdirs = util.list_subdir(test_dir)

        assert len(result_subdirs) == 2
        assert 'data_native' in result_subdirs
        assert 'data_web' in result_subdirs

    @staticmethod
    def csv_reader_to_table(filename):
        result = []
        with open(filename, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                result.append(row)
        return result

class TestPathsClass(object):
    def test_paths_dict(self):
        string_config = 'test/dir/1'
        string_output = 'test/dir/2'
        string_base = 'test/dir/3'
        string_original = 'test/dir/4'
        paths.CONFIG_DIR = string_config
        paths.OUTPUT_DIR = string_output
        paths.BASE_OUTPUT_DIR = string_base
        paths.ORIGINAL_CONFIG_DIR = string_original

        paths_dict = paths.paths_dict()
        assert paths_dict['ROOT_DIR'] == op.dirname(op.abspath(paths.__file__))
        assert paths_dict['CONFIG_DIR'] == string_config
        assert paths_dict['OUTPUT_DIR'] == string_output
        assert paths_dict['BASE_OUTPUT_DIR'] == string_base
        assert paths_dict['ORIGINAL_CONFIG_DIR'] == string_original



class TestTestsClass(object):
    def test_is_integer_not_int(self):
        with pytest.raises(util.ConfigError) as except_result:
            Tests.is_integer("error")
        assert 'error is not an integer' in str(except_result.value)

    def test_is_integer_too_small(self):
        with pytest.raises(util.ConfigError) as except_result:
            Tests.is_integer(-1)
        assert '-1 should be equal or larger than 0' in str(except_result.value)

    def test_is_integer_succes(self):
        assert Tests.is_integer(10) == 10

    def test_is_string_fail(self):
        with pytest.raises(util.ConfigError) as except_result:
            Tests.is_string(list())
        assert "String expected, got <class 'list'>" in str(except_result.value)

    def test_is_string_succes(self):
        test_string = 'This is a string'
        assert Tests.is_string(test_string) == test_string

    @patch('logging.Logger.error')
    def test_check_dependencies_fail(self, mock_log):
        mock_device = Mock()
        mock_device.id = 'Fake_device'
        mock_device.is_installed.return_value = {'NotInstalled': False, 'installed': True}
        mocked_devices = [mock_device, mock_device]

        with pytest.raises(util.ConfigError) as except_result:
            Tests.check_dependencies(mocked_devices, "")
        assert "Required packages ['NotInstalled'] are not installed on device Fake_device" in str(except_result.value)
        mock_log.assert_called_once_with('Fake_device: Required package NotInstalled is not installed')

    @patch('logging.Logger.error')
    def test_check_dependencies_succes(self, mock_log):
        mock_dependencies = Mock()
        mock_device = Mock()
        mock_device.id = 'Fake_device'
        mock_device.is_installed.return_value = {'Installed2': True, 'installed': True}
        mocked_devices = [mock_device, mock_device]
        Tests.check_dependencies(mocked_devices, mock_dependencies)
        assert mock_device.is_installed.call_count == 2
        assert mock_log.call_count == 0