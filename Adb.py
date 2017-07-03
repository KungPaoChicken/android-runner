from pyand import ADB
import re

adb = ADB(adb_path='D:/Yoyo/Downloads/platform-tools/adb.exe')


class AdbError(Exception):
    """Raised when there's an error with ADB"""
    pass


class Adb:
    def __init__(self, devices):
        connect(devices)
        self.devices = {name: {'id': uid} for name, uid in devices.items()}

    def map_devices(self, func, *args, **kwargs):
        results = {}
        for name, dev in self.devices.items():
            try:
                adb.set_target_by_name(dev['id'])
                results[name] = func(*args, **kwargs)
            except AdbError as e:
                print(e.message)
        return results

    def check_apps(self, apps):
        results = {}
        for name, dev in self.devices.items():
            adb.set_target_by_name(dev['id'])
            app_list = adb.shell_command('pm list packages')
            results[name] = {app: re.search(app, app_list) for app in apps}
        return results

    def install_apps(self, apps):
        for app in apps:
            self.map_devices(install, app)

    def shell(self, cmd):
        self.map_devices(adb.shell_command, cmd)


def connect(devices):
    connected = adb.get_devices()
    if not connected:
        raise AdbError('No devices are connected')
    not_connected = filter(lambda (n, uid): uid not in connected.values(), devices.items())
    for name, i in not_connected:
        raise AdbError("Error: Device %s is not connected" % name)


def install(apk):
    return adb.install(apk)


def uninstall(apk):
    print(apk)
    return True
