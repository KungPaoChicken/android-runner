import os
import pytest
import ExperimentRunner.Adb as Adb
from ExperimentRunner.Device import Device
from ExperimentRunner.Devices import Devices
from ExperimentRunner.util import ConfigError
from mock import patch, Mock, MagicMock


class TestDevice(object):

    @pytest.fixture()
    @patch('ExperimentRunner.Adb.connect')
    def device(self, adb_connect):
        name = 'fake_device'
        device_id = 123456789

        return Device(name, device_id)

    @patch('ExperimentRunner.Adb.connect')
    def test_init(self, adb_connect):
        name = 'fake_device'
        device_id = 123456789

        device = Device(name, device_id)

        assert device.name == name
        assert device.id == device_id
        adb_connect.assert_called_once_with(device_id)

    @patch('ExperimentRunner.Adb.shell')
    def test_get_version(self, adb_shell, device):
        adb_shell.return_value = 9
        version = device.get_version()

        assert version == 9
        adb_shell.assert_called_once_with(123456789, 'getprop ro.build.version.release')

    @patch('ExperimentRunner.Adb.shell')
    def test_get_api_level(self, adb_shell, device):
        adb_shell.return_value = 28
        level = device.get_api_level()

        assert level == 28
        adb_shell.assert_called_once_with(123456789, 'getprop ro.build.version.sdk')

    @patch('ExperimentRunner.Device.Device.get_app_list')
    def test_is_installed(self, get_app_list, device):
        get_app_list.return_value = ['app1', 'app2', 'installed_app']
        result_installed = device.is_installed(['app3', 'installed_app', 'app4'])
        assert len(result_installed) == 3
        assert 'app3' in result_installed and not result_installed['app3']
        assert 'app4' in result_installed and not result_installed['app4']
        assert 'installed_app' in result_installed and result_installed['installed_app']

    @patch('ExperimentRunner.Adb.list_apps')
    def test_get_app_list(self, adb_list_apps, device):
        adb_list_apps.return_value = ['app1', 'app2', 'app3']
        app_list = device.get_app_list()

        assert app_list == ['app1', 'app2', 'app3']

    @patch('ExperimentRunner.Adb.install')
    def test_install_file_not_exist(self, adb_install, device):
        with pytest.raises(Adb.AdbError):
            device.install('fake.apk')

        assert adb_install.call_count == 0

    @patch('os.path.isfile')
    @patch('ExperimentRunner.Adb.install')
    def test_install_file_exist(self, adb_install, os_isfile, device):
        os_isfile.return_value = True

        device.install('fake.apk')

        adb_install.assert_called_once_with(123456789, 'fake.apk')

    @patch('ExperimentRunner.Adb.uninstall')
    def test_uninstall(self, adb_uninstall, device):
        app_name = 'fake_app'

        device.uninstall(app_name)

        adb_uninstall.assert_called_once_with(123456789, app_name)

    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_lower_23(self, adb_shell, get_api_level, device):
        get_api_level.return_value = 22
        device.unplug()

        adb_shell.assert_called_once_with(123456789, 'dumpsys battery set usb 0')

    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_higher_equal_23(self, adb_shell, get_api_level, device):
        get_api_level.return_value = 23
        device.unplug()

        adb_shell.assert_called_once_with(123456789, 'dumpsys battery unplug')

    @patch('ExperimentRunner.Adb.shell')
    def test_plug(self, adb_shell, device):
        device.plug()

        adb_shell.assert_called_once_with(123456789, 'dumpsys battery reset')

    @patch('ExperimentRunner.Adb.shell')
    def test_current_activity_current_focus(self, adb_shell, device):
        adb_shell.return_value = 'mCurrentFocus=Window{28d47066 u0 com.android.chrome/org.chromium.chrome.browser.' \
                                 'ChromeTabbedActivity}\nmFocusedApp=Window{3078b3ad u0 com.sonyericsson.usbux/com.' \
                                 'sonyericsson.usbux.settings.ConnectivitySettingsActivity}'
        current_activity = device.current_activity()
        assert current_activity == 'com.android.chrome'

    @patch('ExperimentRunner.Adb.shell')
    def test_current_activity_focused_app(self, adb_shell, device):
        adb_shell.return_value = 'mFocusedApp=AppWindowToken{ce6dd8c token=Token{31892bf ActivityRecord{21e5e0de u0 ' \
                                 'com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity t25385}}}'
        current_activity = device.current_activity()
        assert current_activity == 'com.android.chrome'

    @patch('ExperimentRunner.Adb.shell')
    def test_current_activity_None(self, adb_shell, device):
        adb_shell.return_value = 'mFocusedApp=null'
        current_activity = device.current_activity()
        assert current_activity is None

    @patch('ExperimentRunner.Adb.shell')
    def test_current_activity_error(self, adb_shell, device):
        adb_shell.return_value = 'mFocusedApp=ajislvfhbljhglalkjasfdhdhg'
        with pytest.raises(Adb.AdbError):
            device.current_activity()

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_package_succes(self, adb_shell, device):
        package = 'fake.test.package'
        adb_shell.return_value = 'successsss'

        device.launch_package(package)

        adb_shell.assert_called_once_with(123456789, 'monkey -p {} 1'.format(package))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_package_failure(self, adb_shell, device):
        package = 'fake.test.package'
        adb_shell.return_value = 'error error error monkey aborted error'

        with pytest.raises(Adb.AdbError):
            device.launch_package(package)

        adb_shell.assert_called_once_with(123456789, 'monkey -p {} 1'.format(package))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_activity(self, adb_shell, device):
        package = 'fake.test.package'
        activity = 'main'

        device.launch_activity(package, activity)

        adb_shell.assert_called_once_with(123456789, 'am start -n {}/{}'.format(package, activity))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_activity_force_stop(self, adb_shell, device):
        package = 'fake.test.package'
        activity = 'main'

        device.launch_activity(package, activity, force_stop=True)

        adb_shell.assert_called_once_with(123456789, 'am start -S -n {}/{}'.format(package, activity))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_activity_action(self, adb_shell, device):
        package = 'fake.test.package'
        activity = 'main'

        device.launch_activity(package, activity, action='action')

        adb_shell.assert_called_once_with(123456789, 'am start -a {} -n {}/{}'.format('action', package, activity))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_activity_data_uri(self, adb_shell, device):
        package = 'fake.test.package'
        activity = 'main'

        device.launch_activity(package, activity, data_uri='data.uri')

        adb_shell.assert_called_once_with(123456789, 'am start -n {}/{} -d {}'.format(package, activity, 'data.uri'))

    @patch('ExperimentRunner.Adb.shell')
    def test_launch_activity_from_scratch(self, adb_shell, device):
        package = 'fake.test.package'
        activity = 'main'

        device.launch_activity(package, activity, from_scratch=True)

        adb_shell.assert_called_once_with(123456789, 'am start -n {}/{} --activity-clear-task'.format(package, activity))

    @patch('ExperimentRunner.Adb.shell')
    def test_force_stop(self, adb_shell, device):
        name = 'fake_app'

        device.force_stop(name)

        adb_shell.assert_called_once_with(123456789, 'am force-stop {}'.format(name))

    @patch('ExperimentRunner.Adb.clear_app_data')
    def test_clear_app_date(self, adb_clear_app_data, device):
        name = 'fake_app'

        device.clear_app_data(name)

        adb_clear_app_data.assert_called_once_with(123456789, name)

    @patch('ExperimentRunner.Adb.logcat')
    def test_logcat(self, adb_logcat, device, tmpdir):
        path = os.path.join(str(tmpdir), 'logcat')
        logcat_result = "test file content: 123dsfg564sdfhg"
        adb_logcat.return_value = logcat_result

        device.logcat_to_file(path)

        files_in_path = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        assert len(files_in_path) == 1
        with open(os.path.join(path, files_in_path[0]), 'r') as file:
            file_content = file.read()
            assert file_content == logcat_result
        adb_logcat.assert_called_once_with(123456789)

    @patch('ExperimentRunner.Adb.logcat')
    def test_logcat_regex(self, adb_logcat, device):
        logcat_result = "test result 123dsfg564sdfhg"
        adb_logcat.return_value = logcat_result
        fake_regex = 'auiashdfdfv'

        result = device.logcat_regex(fake_regex)

        adb_logcat.assert_called_once_with(123456789, regex=fake_regex)
        assert result == logcat_result

    @patch('ExperimentRunner.Adb.push')
    def test_push(self, adb_push, device):
        adb_push.return_value = 'pushpush'
        local_path = 'test/local/path'
        remote_path = 'test/remote/path'

        result = device.push(local_path, remote_path)

        adb_push.assert_called_once_with(123456789, local_path, remote_path)
        assert result == 'pushpush'

    @patch('ExperimentRunner.Adb.pull')
    def test_pull(self, adb_pull, device):
        adb_pull.return_value = 'pullpull'
        local_path = 'test/local/path'
        remote_path = 'test/remote/path'

        result = device.pull(local_path, remote_path)

        adb_pull.assert_called_once_with(123456789, local_path, remote_path)
        assert result == 'pullpull'

    @patch('ExperimentRunner.Adb.shell')
    def test_shell(self, adb_shell, device):
        adb_shell.return_value = 'shell return value'
        shell_command = 'dumpsys battery set usb 1'

        result = device.shell(shell_command)

        adb_shell.assert_called_once_with(123456789, shell_command)
        assert result == 'shell return value'

    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Device.Device.get_version')
    def test_str(self, get_version, get_api_level, device):
        get_version.return_value = 9
        get_api_level.return_value = 28

        device_string = str(device)

        assert device_string == 'fake_device (123456789, Android 9, API level 28)'

class TestDevices(object):
    @pytest.fixture()
    @patch('ExperimentRunner.Devices.load_json')
    @patch('ExperimentRunner.Adb.setup')
    def devices(self, adb_setup, load_json):
        return Devices([])

    @patch('ExperimentRunner.Devices.load_json')
    @patch('ExperimentRunner.Adb.setup')
    def test_init_error(self, adb_setup, load_json):
        load_json.return_value = {}
        with pytest.raises(ConfigError):
            Devices(['fake_device'])

        adb_setup.assert_called_once_with('adb')

    @patch('ExperimentRunner.Device.Device.__init__')
    @patch('ExperimentRunner.Devices.load_json')
    @patch('ExperimentRunner.Adb.setup')
    def test_init_succes(self, adb_setup, load_json, device):
        device.return_value = None
        load_json.return_value = {'fake_device': 123456789}
        devices = Devices(['fake_device'], 'adb/path')

        adb_setup.assert_called_once_with('adb/path')
        device.assert_called_once_with('fake_device', 123456789)
        assert len(devices.devices) == 1
        assert isinstance(devices.devices[0], Device)

    def test_iter(self, devices):
        test_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        devices.devices = test_list
        result_list = []
        for n in devices:
            result_list.append(n)

        assert result_list == test_list

    def test_get_device(self, devices):
        device_names = ['a', 'b', 'c', 'd']
        test_devices = []
        for name in device_names:
            mock_device = Mock()
            mock_device.name = name
            mock_device.id = name
            test_devices.append(mock_device)
        devices.devices = test_devices

        device = devices.get_device('c')
        assert device.name == 'c' and device.id == 'c'

    def test_names(self, devices):
        device_names = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        devices._device_map = device_names

        names = devices.names()

        assert len(names) == 4
        assert 'a' in names
        assert 'b' in names
        assert 'c' in names
        assert 'd' in names

    def test_ids(self, devices):
        device_names = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        devices._device_map = device_names

        ids = devices.ids()

        assert len(ids) == 4
        assert 1 in ids
        assert 2 in ids
        assert 3 in ids
        assert 4 in ids

    def test_get_id(self, devices):
        device_names = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        devices._device_map = device_names

        id = devices.get_id('c')

        assert id == 3

    def test_get_name(self, devices):
        device_names = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        devices._device_map = device_names

        name = devices.get_name(3)

        assert 'c' == name

class TestAdb(object):

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_succes_custom_path(self, ADB):
        ADB_instance = MagicMock()
        ADB_instance._ADB__error = None
        ADB.return_value = ADB_instance

        Adb.setup('adb/path')

        assert isinstance(Adb.adb, MagicMock)
        ADB.assert_called_once_with(adb_path='adb/path')

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_succes_default_path(self, ADB):
        ADB_instance = MagicMock()
        ADB_instance._ADB__error = None
        ADB.return_value = ADB_instance

        Adb.setup()

        assert isinstance(Adb.adb, MagicMock)
        ADB.assert_called_once_with(adb_path='adb')

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_error(self, ADB):
        ADB_instance = MagicMock()
        ADB_instance._ADB__error = True
        ADB.return_value = ADB_instance
        with pytest.raises(Adb.AdbError):
            Adb.setup()

    def test_connect_no_devices(self):
        mock_adb = Mock()
        mock_adb.get_devices.return_value = {}
        Adb.adb = mock_adb

        with pytest.raises(Adb.ConnectionError):
            Adb.connect('123')

        mock_adb.get_devices.assert_called_once()

    def test_connect_device_missing(self):
        mock_adb = Mock()
        mock_adb.get_devices.return_value = {'a': 12, 'b': 13}
        Adb.adb = mock_adb

        with pytest.raises(Adb.ConnectionError):
            Adb.connect(123)

        mock_adb.get_devices.assert_called_once()

    def test_connect_succes(self):
        mock_adb = Mock()
        mock_adb.get_devices.return_value = {'a': 12, 'b': 13, 'c': 123}
        Adb.adb = mock_adb

        Adb.connect(123)

        mock_adb.get_devices.assert_called_once()

    def test_shell_succes(self):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = "succes         "
        Adb.adb = mock_adb

        result = Adb.shell(123, "test_command")

        assert result == 'succes'
        mock_adb.set_target_by_name.assert_called_once_with(123)
        mock_adb.shell_command('test_command')

    def test_shell_error(self):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = "error"
        Adb.adb = mock_adb

        with pytest.raises(Adb.AdbError):
            Adb.shell(123, "test_command")

        mock_adb.set_target_by_name.assert_called_once_with(123)
        mock_adb.shell_command('test_command')

    @patch('ExperimentRunner.Adb.shell')
    def test_list_apps(self, adb_shell):
        adb_shell.return_value = 'package:com.app.1\npackage:com.app.2\npackage:com.app.3'

        result = Adb.list_apps(123)

        adb_shell.assert_called_once_with(123, 'pm list packages')
        assert len(result) == 3
        assert 'com.app.1' in result
        assert 'com.app.2' in result
        assert 'com.app.3' in result

    def test_install_default(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        apk = 'test_apk.apk'

        result = Adb.install(device_id, apk)

        result = 'succes'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('install -r -g {}'.format(apk))

    def test_install_no_replace(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        apk = 'test_apk.apk'

        result = Adb.install(device_id, apk, replace=False)

        result = 'succes'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('install -g {}'.format(apk))

    def test_install_not_all_permissions(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        apk = 'test_apk.apk'

        result = Adb.install(device_id, apk, all_permissions=False)

        result = 'succes'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('install -r {}'.format(apk))

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_uninstall_delete_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.uninstall.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        Adb.uninstall(device_id, name)

        mock_adb.uninstall.assert_called_once_with(package=name, keepdata=True)
        s_or_e.assert_called_once_with('succes', '{}: "{}" uninstalled'.format(device_id, name),
                                       '{}: Failed to uninstall "{}"'.format(device_id, name))

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_uninstall_keep_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.uninstall.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        Adb.uninstall(device_id, name, True)

        mock_adb.uninstall.assert_called_once_with(package=name, keepdata=False)
        s_or_e.assert_called_once_with('succes', '{}: "{}" uninstalled'.format(device_id, name),
                                       '{}: Failed to uninstall "{}"'.format(device_id, name))

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_clear_app_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        Adb.clear_app_data(device_id, name)

        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.shell_command.assert_called_once_with('pm clear {}'.format(name))
        s_or_e.assert_called_once_with('succes', '{}: Data of "{}" cleared'.format(device_id, name),
                                       '{}: Failed to clear data for "{}"'.format(device_id, name))

    @patch('logging.Logger.info')
    def test_success_or_exception_succes(self, logger):
        input = 'Success'
        succes_msg = 'action succes'
        fail_msg = 'action fail'

        Adb.success_or_exception(input, succes_msg, fail_msg)

        logger.assert_called_once_with(succes_msg)

    @patch('logging.Logger.info')
    def test_success_or_exception_exception(self, logger):
        input = 'fail'
        succes_msg = 'action succes'
        fail_msg = 'action fail'

        with pytest.raises(Adb.AdbError):
            Adb.success_or_exception(input, succes_msg, fail_msg)

        logger.assert_called_once_with(fail_msg + '\nMessage returned:\n{}'.format(input))

    def test_push(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'push output'
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.push(device_id, local_path, remote_path)

        assert result == 'push output'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('push {} {}'.format(local_path, remote_path))

    def test_pull_no_error(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'pull output'
        mock_adb._ADB__error = None
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.pull(device_id, remote_path, local_path)

        assert result == 'pull output'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('pull {} {}'.format(remote_path, local_path))

    def test_pull_error_no_bytes_in(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'pull output'
        mock_adb._ADB__error = 'error error'
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.pull(device_id, remote_path, local_path)

        assert result == 'pull output'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('pull {} {}'.format(remote_path, local_path))

    def test_pull_error_no_bytes_in(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'pull output'
        mock_adb._ADB__error = 'bytes in error'
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.pull(device_id, remote_path, local_path)

        assert result == 'bytes in error'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.run_cmd.assert_called_once_with('pull {} {}'.format(remote_path, local_path))

    def test_logcat_no_regex(self):
        mock_adb = Mock()
        mock_adb.get_logcat.return_value = 'get_logcat output'
        Adb.adb = mock_adb

        device_id = 123

        result = Adb.logcat(device_id)

        assert result == 'get_logcat output'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.get_logcat.assert_called_once_with(lcfilter='-d')

    def test_logcat_with_regex(self):
        mock_adb = Mock()
        mock_adb.get_logcat.return_value = 'get_logcat output'
        Adb.adb = mock_adb

        test_regex = '[a-zA-Z]+'
        device_id = 123

        result = Adb.logcat(device_id, test_regex)

        assert result == 'get_logcat output'
        mock_adb.set_target_by_name.assert_called_once_with(device_id)
        mock_adb.get_logcat.assert_called_once_with(lcfilter='-d -e {}'.format(test_regex))