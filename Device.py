import Adb
from Adb import AdbError
import re


class Device:
    def __init__(self, name, device_id):
        self.name = name
        self.id = device_id
        self.apps = []
        Adb.connect(device_id)
        self.update_app_list()

    def is_installed(self, apps):
        return {name: app in self.apps for name, app in apps.items()}

    def update_app_list(self):
        self.apps = Adb.list_apps(self.id)

    def install_apps(self, apps):
        for app in apps:
            if Adb.install(self.id, app) == 'Success':
                self.apps.append(app)

    # https://github.com/appium/appium-adb/blob/e9234db1546411e495a7520e9d29d43d990c617a/lib/tools/apk-utils.js#L84
    def current_activity(self):
        windows = Adb.shell(self.id, 'dumpsys window windows')
        for line in windows.split('\n'):
            # https://regex101.com/r/xZ8vF7/1
            match = re.search(r'mFocusedApp.+Record{.*\s([^\s/\}]+)/([^\s/\},]+),?(\s[^\s/\}]+)*\}', line)
            if match:
                return match.group(1).strip()
            else:
                match = re.search(r'^mFocusedApp=null$', line)
                if match:
                    return 'null'
        raise AdbError('Could not parse activity from dumpsys')

    def __str__(self):
        return '%s (%s)' % (self.name, self.id)
