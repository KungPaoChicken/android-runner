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
            Adb.install(self.id, apk)
            self.apps.append(splitext(basename(apk))[0])

    def uninstall_apps(self, names):
        for name in names:
            if name not in self.apps:
                raise AdbError('%s does not exist in the list of apps' % name)
        for name in names:
            Adb.uninstall(self.id, name)
            self.apps.remove(name)

    def unplug(self):
        Adb.unplug(self.id)

    def plug(self):
        Adb.plug(self.id)

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

    def launch(self, name, activity, action='', data=''):
        # https://stackoverflow.com/a/3229077
        cmd = "am start"
        if action:
            cmd += " -a %s" % action
        cmd += " -n % s/%s" % (name, activity)
        if data:
            cmd += " -d %s" % data
        return Adb.shell(self.id, cmd)

    def force_stop(self, name):
        Adb.shell(self.id, 'am force-stop %s' % name)

    def clear_app_data(self, name):
        Adb.clear_app_data(self.id, name)

    def __str__(self):
        return '%s (%s)' % (self.name, self.id)
