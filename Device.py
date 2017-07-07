from os.path import basename, splitext, isfile
import re
import Adb
from Adb import AdbError


class Device:
    def __init__(self, name, device_id):
        self.name = name
        self.id = device_id
        self.apps = []
        Adb.connect(device_id)
        self.update_app_list()

    def is_installed(self, apps):
        return {app: app in self.apps for app in apps}

    def update_app_list(self):
        self.apps = Adb.list_apps(self.id)

    def install_apks(self, apks):
        for apk in apks:
            if not isfile(apk):
                raise AdbError("%s is not found" % apk)
        for apk in apks:
            result = Adb.install(self.id, apk)
            if 'Success' in result:
                self.apps.append(splitext(basename(apk))[0])
            else:
                raise AdbError(result)

    def uninstall_apps(self, names):
        for name in names:
            if name not in self.apps:
                raise AdbError('%s does not exist in the list of apps' % name)
        for name in names:
            result = Adb.uninstall(self.id, name)
            if 'Success' in result:
                self.apps.remove(name)
            else:
                raise AdbError(result)

    def current_activity(self):
        # https://github.com/appium/appium-adb/blob/e9234db1546411e495a7520e9d29d43d990c617a/lib/tools/apk-utils.js#L84
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
