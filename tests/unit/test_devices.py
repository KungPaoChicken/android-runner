import os

import pytest
from mock import MagicMock, Mock, call, patch

import ExperimentRunner.Adb as Adb
from ExperimentRunner.Device import Device
from ExperimentRunner.Devices import Devices
from ExperimentRunner.util import ConfigError


class TestDevice(object):

    @pytest.fixture()
    @patch('ExperimentRunner.Adb.connect')
    def device(self, adb_connect):
        name = 'fake_device'
        device_id = 123456789
        device_settings = {}

        return Device(name, device_id, device_settings)

    @pytest.fixture()
    @patch('ExperimentRunner.Adb.connect')
    def device_root(self, adb_connect):
        name = 'fake_device'
        device_id = 123456789
        device_settings = {'root_disable_charging': True,
                           'charging_disabled_value': '0', 'usb_charging_disabled_file': 'test/file'}

        return Device(name, device_id, device_settings)

    @patch('ExperimentRunner.Adb.connect')
    def test_init(self, adb_connect):
        name = 'fake_device'
        device_id = 123456789
        device_settings = {'root_disable_charging': True,
                           'charging_disabled_value': '0', 'usb_charging_disabled_file': 'test/file'}

        device = Device(name, device_id, device_settings)

        assert device.name == name
        assert device.id == device_id
        assert device.root_plug_value is None
        assert device.root_unplug_file == 'test/file'
        assert device.root_unplug_value == '0'
        assert device.root_unplug is True
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

    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_lower_23_no_root(self, adb_shell, get_api_level, su_unplug, device):
        get_api_level.return_value = 22
        device.unplug(False)

        assert su_unplug.call_count == 0
        adb_shell.assert_called_once_with(123456789, 'dumpsys battery set usb 0')


    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_higher_equal_23_no_root(self, adb_shell, get_api_level, su_unplug, device):
        get_api_level.return_value = 23
        device.unplug(False)

        assert su_unplug.call_count == 0
        adb_shell.assert_called_once_with(123456789, 'dumpsys battery unplug')

    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_lower_23_root(self, adb_shell, get_api_level, su_unplug, device_root):
        get_api_level.return_value = 22
        device_root.unplug(False)

        su_unplug.assert_called_once_with(False)
        assert adb_shell.call_count == 0

    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_lower_23_root_restart(self, adb_shell, get_api_level, su_unplug, device_root):
        get_api_level.return_value = 22
        device_root.unplug(True)

        su_unplug.assert_called_once_with(True)
        assert adb_shell.call_count == 0

    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_higher_equal_23_root(self, adb_shell, get_api_level, su_unplug, device_root):
        get_api_level.return_value = 23
        device_root.unplug(False)

        su_unplug.assert_called_once_with(False)
        assert adb_shell.call_count == 0

    @patch('ExperimentRunner.Device.Device.su_unplug')
    @patch('ExperimentRunner.Device.Device.get_api_level')
    @patch('ExperimentRunner.Adb.shell')
    def test_unplug_api_higher_equal_23_root_restart(self, adb_shell, get_api_level, su_unplug, device_root):
        get_api_level.return_value = 23
        device_root.unplug(True)

        su_unplug.assert_called_once_with(True)
        assert adb_shell.call_count == 0


    @patch('ExperimentRunner.Device.Device.check_plug_value')
    @patch('ExperimentRunner.Adb.shell_su')
    def test_su_unplug_no_error(self, shell_su, check_plug_value, device_root):
        shell_su.side_effect = ['default_return', '']

        device_root.su_unplug(False)

        expected_calls = [call(device_root.id, 'cat %s' % device_root.root_unplug_file),
                          call(device_root.id, 'echo %s > %s' %
                               (device_root.root_unplug_value, device_root.root_unplug_file))]
        assert shell_su.mock_calls == expected_calls
        assert device_root.root_plug_value == 'default_return'
        assert check_plug_value.call_count == 0

    @patch('ExperimentRunner.Device.Device.check_plug_value')
    @patch('ExperimentRunner.Adb.shell_su')
    def test_su_unplug_not_rooted(self, shell_su, check_plug_value, device_root):
        shell_su.side_effect = ['su: not found', 'default_return', 'No such file or directory']
        with pytest.raises(Adb.AdbError):
            device_root.su_unplug(False)

        expected_calls = [call(device_root.id, 'cat test/file')]
        assert shell_su.mock_calls == expected_calls
        assert device_root.root_plug_value == 'su: not found'
        assert check_plug_value.call_count == 0

    @patch('ExperimentRunner.Device.Device.check_plug_value')
    @patch('ExperimentRunner.Adb.shell_su')
    def test_su_unplug_invalid_root_unplug_file(self, adb_shell, check_plug_value, device_root):
        adb_shell.side_effect = ['No such file or directory', '']
        with pytest.raises(ConfigError):
            device_root.su_unplug(False)

        expected_calls = [call(device_root.id, 'cat %s' % device_root.root_unplug_file)]
        assert adb_shell.mock_calls == expected_calls
        assert device_root.root_plug_value == 'No such file or directory'
        assert check_plug_value.call_count == 0

    @patch('ExperimentRunner.Device.Device.check_plug_value')
    @patch('ExperimentRunner.Adb.shell_su')
    def test_su_unplug_restart(self, shell_su, check_plug_value, device_root):
        shell_su.side_effect = ['default_return', '']

        device_root.su_unplug(True)

        expected_calls = [call(device_root.id, 'cat %s' % device_root.root_unplug_file),
                          call(device_root.id, 'echo %s > %s' %
                               (device_root.root_unplug_value, device_root.root_unplug_file))]
        assert shell_su.mock_calls == expected_calls
        assert device_root.root_plug_value == 'default_return'
        check_plug_value.assert_called_once()

    def test_check_plug_value_no_action(self, device_root):
        device_root.root_plug_value = 'enabled'
        device_root.root_unplug_value = 'disabled'

        device_root.check_plug_value()

        assert device_root.root_plug_value == 'enabled'
        assert device_root.root_unplug_value == 'disabled'

    def test_check_plug_value_unplug_plug_int_no_match(self, device_root):
        device_root.root_plug_value = 1
        device_root.root_unplug_value = 0

        device_root.check_plug_value()

        assert device_root.root_plug_value == 1
        assert device_root.root_unplug_value == 0

    @patch('logging.Logger.info')
    def test_check_plug_value_unplug_int_plug_string_no_match(self, logger, device_root):
        device_root.root_plug_value = 'enabled'
        device_root.root_unplug_value = 0

        device_root.check_plug_value()

        assert device_root.root_plug_value == 'enabled'
        assert device_root.root_unplug_value == 0
        logger.assert_called_once_with('Error setting root plug value, check manually after experiment if charging is enabled')

    def test_check_plug_value_same_plug_unplug_int(self, device_root):
        device_root.root_plug_value = 0
        device_root.root_unplug_value = 0

        device_root.check_plug_value()

        assert device_root.root_plug_value == 1
        assert device_root.root_unplug_value == 0

    def test_check_plug_value_same_plug_unplug_string_set_enabled(self, device_root):
        device_root.root_plug_value = 'disabled'
        device_root.root_unplug_value = 'disabled'

        device_root.check_plug_value()

        assert device_root.root_plug_value == 'enabled'
        assert device_root.root_unplug_value == 'disabled'

    def test_check_plug_value_same_plug_unplug_string_set_disabled(self, device_root):
        device_root.root_plug_value = 'enabled'
        device_root.root_unplug_value = 'enabled'

        device_root.check_plug_value()

        assert device_root.root_plug_value == 'disabled'
        assert device_root.root_unplug_value == 'enabled'

    @patch('ExperimentRunner.Device.Device.su_plug')
    @patch('ExperimentRunner.Adb.shell')
    def test_plug_no_root(self, adb_shell, su_plug, device):
        device.plug()

        assert su_plug.call_count == 0
        adb_shell.assert_called_once_with(123456789, 'dumpsys battery reset')

    @patch('ExperimentRunner.Device.Device.su_plug')
    @patch('ExperimentRunner.Adb.shell')
    def test_plug_root(self, adb_shell, su_plug, device_root):
        device_root.plug()

        su_plug.assert_called_once()
        adb_shell.assert_called_once_with(123456789, 'dumpsys battery reset')

    @patch('ExperimentRunner.Adb.shell_su')
    def test_su_plug(self, adb_shell_su, device_root):
        device_root.root_plug_value = '123456'

        device_root.su_plug()

        adb_shell_su.assert_called_once_with(123456789, 'echo 123456 > test/file')

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
    def test_current_activity_none(self, adb_shell, device):
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

        adb_shell.assert_called_once_with(123456789,
                                          'am start -n {}/{} --activity-clear-task'.format(package, activity))

    @patch('ExperimentRunner.Adb.shell')
    def test_force_stop(self, adb_shell, device):
        name = 'fake_app'

        device.force_stop(name)

        adb_shell.assert_called_once_with(123456789, 'am force-stop {}'.format(name))

    @patch('ExperimentRunner.Adb.clear_app_data')
    def test_clear_app_data(self, adb_clear_app_data, device):
        name = 'fake_app'

        device.clear_app_data(name)

        adb_clear_app_data.assert_called_once_with(123456789, name)

    @patch('ExperimentRunner.Adb.logcat')
    def test_logcat_to_file(self, adb_logcat, device, tmpdir):
        path = os.path.join(str(tmpdir), 'logcat')
        logcat_result = "test file content: 123dsfg564sdfhg"
        adb_logcat.return_value = logcat_result

        device.logcat_to_file(path)

        files_in_path = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

        assert len(files_in_path) == 1
        with open(os.path.join(path, files_in_path[0]), 'r') as fl:
            file_content = fl.read()
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
        mock_device_settings = Mock()
        devices = Devices({'fake_device': mock_device_settings}, 'adb/path')

        adb_setup.assert_called_once_with('adb/path')
        device.assert_called_once_with('fake_device', 123456789, mock_device_settings)
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

        device_id = devices.get_id('c')

        assert device_id == 3

    def test_get_name(self, devices):
        device_names = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        devices._device_map = device_names

        name = devices.get_name(3)

        assert 'c' == name


class TestAdb(object):

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_succes_custom_path(self, adb):
        adb_instance = MagicMock()
        adb_instance._ADB__error = None
        adb.return_value = adb_instance

        Adb.setup('adb/path')

        assert isinstance(Adb.adb, MagicMock)
        adb.assert_called_once_with(adb_path='adb/path')

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_succes_default_path(self, adb):
        adb_instance = MagicMock()
        adb_instance._ADB__error = None
        adb.return_value = adb_instance

        Adb.setup()

        assert isinstance(Adb.adb, MagicMock)
        adb.assert_called_once_with(adb_path='adb')

    @patch('ExperimentRunner.Adb.ADB')
    def test_setup_error(self, adb):
        adb_instance = MagicMock()
        adb_instance._ADB__error = True
        adb.return_value = adb_instance
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

        expected_calls = [call.set_target_by_name(123), call.shell_command('test_command')]
        assert mock_adb.mock_calls == expected_calls
        assert result == 'succes'

    def test_shell_error(self):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = "error"
        Adb.adb = mock_adb

        with pytest.raises(Adb.AdbError):
            Adb.shell(123, "test_command")

        expected_calls = [call.set_target_by_name(123), call.shell_command('test_command')]
        assert mock_adb.mock_calls == expected_calls

    def test_shell_su_succes(self):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = "su_succes         "
        Adb.adb = mock_adb
        result = Adb.shell_su(123, "test_command_su")

        expected_calls = [call.set_target_by_name(123), call.shell_command('su -c \'test_command_su\'')]
        assert mock_adb.mock_calls == expected_calls
        assert result == 'su_succes'

    def test_shell_su_error(self):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = "su_error"
        Adb.adb = mock_adb

        with pytest.raises(Adb.AdbError):
            Adb.shell_su(123, "test_command_su")

        expected_calls = [call.set_target_by_name(123), call.shell_command('su -c \'test_command_su\'')]
        assert mock_adb.mock_calls == expected_calls

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

        assert result == 'succes'
        expected_calls = [call.set_target_by_name(device_id), call.run_cmd('install -r -g {}'.format(apk))]
        assert mock_adb.mock_calls == expected_calls

    def test_install_no_replace(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        apk = 'test_apk.apk'

        result = Adb.install(device_id, apk, replace=False)

        assert result == 'succes'
        expected_calls = [call.set_target_by_name(device_id), call.run_cmd('install -g {}'.format(apk))]
        assert mock_adb.mock_calls == expected_calls

    def test_install_not_all_permissions(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        apk = 'test_apk.apk'

        result = Adb.install(device_id, apk, all_permissions=False)

        assert result == 'succes'
        expected_calls = [call.set_target_by_name(device_id), call.run_cmd('install -r {}'.format(apk))]
        assert mock_adb.mock_calls == expected_calls

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_uninstall_delete_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.uninstall.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        manager = Mock()
        manager.attach_mock(s_or_e, "s_or_e_mock")
        manager.mock_adb = mock_adb

        Adb.uninstall(device_id, name)

        expected_calls = [call.mock_adb.set_target_by_name(123),
                          call.mock_adb.uninstall(package=name, keepdata=True),
                          call.s_or_e_mock('succes', '{}: "{}" uninstalled'.format(device_id, name),
                                           '{}: Failed to uninstall "{}"'.format(device_id, name))]
        assert manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_uninstall_keep_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.uninstall.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        manager = Mock()
        manager.attach_mock(s_or_e, "s_or_e_mock")
        manager.mock_adb = mock_adb

        Adb.uninstall(device_id, name, True)

        expected_calls = [call.mock_adb.set_target_by_name(123),
                          call.mock_adb.uninstall(package=name, keepdata=False),
                          call.s_or_e_mock('succes', '{}: "{}" uninstalled'.format(device_id, name),
                                           '{}: Failed to uninstall "{}"'.format(device_id, name))]
        assert manager.mock_calls == expected_calls

    @patch('ExperimentRunner.Adb.success_or_exception')
    def test_clear_app_data(self, s_or_e):
        mock_adb = Mock()
        mock_adb.shell_command.return_value = 'succes'
        Adb.adb = mock_adb
        device_id = 123
        name = 'app_name'

        manager = Mock()
        manager.attach_mock(s_or_e, "s_or_e_mock")
        manager.mock_adb = mock_adb

        Adb.clear_app_data(device_id, name)

        expected_calls = [call.mock_adb.set_target_by_name(123),
                          call.mock_adb.shell_command('pm clear app_name'),
                          call.s_or_e_mock('succes', '{}: Data of "{}" cleared'.format(device_id, name),
                                           '{}: Failed to clear data for "{}"'.format(device_id, name))]
        assert manager.mock_calls == expected_calls

    @patch('logging.Logger.info')
    def test_success_or_exception_succes(self, logger):
        input_string = 'Success'
        succes_msg = 'action succes'
        fail_msg = 'action fail'

        Adb.success_or_exception(input_string, succes_msg, fail_msg)

        logger.assert_called_once_with(succes_msg)

    @patch('logging.Logger.info')
    def test_success_or_exception_exception(self, logger):
        input_string = 'fail'
        succes_msg = 'action succes'
        fail_msg = 'action fail'

        with pytest.raises(Adb.AdbError):
            Adb.success_or_exception(input_string, succes_msg, fail_msg)

        logger.assert_called_once_with(fail_msg + '\nMessage returned:\n{}'.format(input_string))

    def test_push(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'push output'
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.push(device_id, local_path, remote_path)

        assert result == 'push output'
        expected_calls = [call.set_target_by_name(device_id),
                          call.run_cmd('push {} {}'.format(local_path, remote_path))]
        assert mock_adb.mock_calls == expected_calls

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
        expected_calls = [call.set_target_by_name(device_id),
                          call.run_cmd('pull {} {}'.format(remote_path, local_path))]
        assert mock_adb.mock_calls == expected_calls

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
        expected_calls = [call.set_target_by_name(device_id),
                          call.run_cmd('pull {} {}'.format(remote_path, local_path))]
        assert mock_adb.mock_calls == expected_calls

    def test_pull_error_with_bytes_in(self):
        mock_adb = Mock()
        mock_adb._ADB__output = 'pull output'
        mock_adb._ADB__error = 'bytes in error'
        Adb.adb = mock_adb

        device_id = 123
        local_path = 'local/path'
        remote_path = 'remote/path'

        result = Adb.pull(device_id, remote_path, local_path)

        assert result == 'bytes in error'
        expected_calls = [call.set_target_by_name(device_id),
                          call.run_cmd('pull {} {}'.format(remote_path, local_path))]
        assert mock_adb.mock_calls == expected_calls

    def test_logcat_no_regex(self):
        mock_adb = Mock()
        mock_adb.get_logcat.return_value = 'get_logcat output'
        Adb.adb = mock_adb

        device_id = 123

        result = Adb.logcat(device_id)

        assert result == 'get_logcat output'
        expected_calls = [call.set_target_by_name(device_id),
                          call.get_logcat(lcfilter='-d')]
        assert mock_adb.mock_calls == expected_calls

    def test_logcat_with_regex(self):
        mock_adb = Mock()
        mock_adb.get_logcat.return_value = 'get_logcat output'
        Adb.adb = mock_adb

        test_regex = '[a-zA-Z]+'
        device_id = 123

        result = Adb.logcat(device_id, test_regex)

        assert result == 'get_logcat output'
        expected_calls = [call.set_target_by_name(device_id),
                          call.get_logcat(lcfilter='-d -e {}'.format(test_regex))]
        assert mock_adb.mock_calls == expected_calls
