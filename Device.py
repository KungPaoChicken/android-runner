import os.path as op
import re
import subprocess
from Profiler import makedirs
import time
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
            if not op.isfile(apk):
                raise AdbError("%s is not found" % apk)
        for apk in apks:
            Adb.install(self.id, apk)
            self.apps.append(op.splitext(op.basename(apk))[0])

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

    def launch(self, package, activity, action='', data_uri='', from_scratch=False):
        # https://developer.android.com/studio/command-line/adb.html#IntentSpec
        # https://stackoverflow.com/a/3229077
        cmd = "am start"
        if action:
            cmd += " -a %s" % action
        cmd += " -n %s/%s" % (package, activity)
        if data_uri:
            cmd += " -d %s" % data_uri
        # https://android.stackexchange.com/a/113919
        if from_scratch:
            cmd += " --activity-clear-task"
        return Adb.shell(self.id, cmd)

    def force_stop(self, name):
        Adb.shell(self.id, 'am force-stop %s' % name)

    def clear_app_data(self, name):
        Adb.clear_app_data(self.id, name)

    def logcat_to_file(self, path):
        makedirs(path)
        with open(op.join(path, '%s_%s.txt' % (self.id, time.strftime('%Y.%m.%d_%H%M%S'))), 'w+') as f:
            f.write(Adb.logcat(self.id))

    def logcat_regex(self, regex):
        return Adb.logcat(self.id, regex=regex)

    def __str__(self):
        return '%s (%s)' % (self.name, self.id)
