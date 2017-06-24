from pyand import ADB
import re

adb = ADB(adb_path='/opt/platform-tools/adb')


class AdbError(Exception):
    """Raised when there's an error with ADB"""
    pass


class Adb:
    def __init__(self, devices):
        try:
            connect(devices)
            self.devices = {name: {'id': uid} for name, uid in devices.items()}
        except AdbError as e:
            raise e
        self.update_app_list()

    def map_devices(self, func, *args, **kwargs):
        results = {}
        for name, dev in self.devices.items():
            try:
                adb.set_target_by_name(dev['id'])
                results[name] = func(*args, **kwargs)
            except AdbError as e:
                print(e.message)
        return results

    def is_installed(self, apps):
        results = {}
        for name, dev in self.devices.items():
            results[name] = {app: re.search(app, dev['apps']) for app in apps}
        return results

    def install(self, apks):
        for apk in apks:
            self.map_devices(install, apk)
        self.update_app_list()

    def shell(self, cmd):
        self.map_devices(shell, cmd)

    def update_app_list(self):
        for name, dev in self.devices.items():
            adb.set_target_by_name(dev['id'])
            self.devices[name]['apps'] = adb.shell_command('pm list packages')


def connect(devices):
    connected = adb.get_devices()
    if not connected:
        raise AdbError('No devices are connected')
    not_connected = filter(lambda (n, uid): uid not in connected.values(), devices.items())
    for name, i in not_connected:
        raise AdbError("Error: Device %s is not connected" % name)


def shell(cmd):
    return adb.shell_command(cmd)


def install(apk):
    return adb.install(apk)


def uninstall(apk):
    print(apk)
    return True
