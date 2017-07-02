from Adb import Adb, AdbError


class Devices:
    def __init__(self, devices):
        self._devices = devices
        try:
            self.adb = Adb(self._devices)
        except AdbError as e:
            print(e.message)
            exit(0)

    def names(self):
        return self._devices.keys()

    def ids(self):
        return self._devices.values()

    def get_id(self, name):
        return self._devices[name]

    def get_name(self, device_id):
        return (k for k, v in self._devices if v == device_id)

    def get_all(self):
        return self._devices

    def check_apps(self, apps):
        results = {}
        for name, dev in self._devices.items():
            adb.set_target_by_name(dev['id'])
            app_list = adb.shell_command('pm list packages')
            results[name] = {app: re.search(app, app_list) for app in apps}
        return results

    def install_apps(self, apps):
        for app in apps:
            self.map_devices(install, app)
