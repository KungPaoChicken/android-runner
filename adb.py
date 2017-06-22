from pyand import ADB
import re

adb = ADB(adb_path='/opt/platform-tools/adb')


class AdbError(Exception):
    """Raised when there's an error with ADB"""
    pass


class Adb:
    def __init__(self, devices):
        # Connectivity check
        self.devices = devices
        connect(devices)

    def map_devices(self, func, *args, **kwargs):
        results = []
        for name, dev in self.devices.items():
            try:
                adb.set_target_by_name(dev)
                results.append((name, func(*args, **kwargs)))
            except AdbError as e:
                print(e.message)
        return results

    def install(self, apks):
        for apk in apks:
            self.map_devices(install, apk)

    def browser_check(self, browsers):
        browsers_list = {'chrome': 'com.android.chrome',
                         'opera': 'com.opera.browser',
                         'firefox': 'org.mozilla.firefox'
                         }
        browsers = map(browsers_list.get, browsers)
        results = self.map_devices(is_installed, browsers)
        error_msg = []
        for device, result in results:
            not_installed = [b for b, i in result if not i]
            error_msg = [b + " is not installed on %s" % device for b in not_installed]
        raise AdbError('\n'.join(error_msg))

    def shell(self, cmd):
        self.map_devices(shell, cmd)


def connect(devices):
    connected_devices = adb.get_devices()
    if not connected_devices:
        raise AdbError('No devices are connected')
    not_connected = filter(lambda (n, i): i not in connected_devices.values(), devices.items())
    for name, i in not_connected:
        raise AdbError("Error: Device %s is not connected" % name)


def shell(cmd):
    return adb.shell_command(cmd)


def is_installed(names):
    installed_apps = adb.shell_command('pm list packages')
    return map(lambda n: (n, re.search(n, installed_apps)), names)


def install(apk):
    return adb.install(apk)


def uninstall(apk):
    return True
