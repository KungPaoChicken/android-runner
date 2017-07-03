from Adb import Adb, AdbError
from pyand import ADB
import re

adb = ADB(adb_path='D:/Yoyo/Downloads/platform-tools/adb.exe')


class Devices:
    def __init__(self, name, device_id):
        self.name = name
        self.device_id = device_id
        self.adb = Adb({name: device_id})
        self.apps = self.adb.shell('pm list packages')

    def check_apps(self, apps):
        results = {}
        for name, dev in self._devices.items():
            adb.set_target_by_name(dev)
            app_list = adb.shell_command('pm list packages')
            results[name] = {app: re.search(app, app_list) for app in apps}
        return results

    def install_apps(self, apps):
        for app in apps:
            self.adb.install(app)
