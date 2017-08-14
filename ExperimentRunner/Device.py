import logging
import os.path as op
import re
import time

import Adb
from Adb import AdbError
from util import makedirs


class Device:
    def __init__(self, name, device_id):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.id = device_id
        self.apps = []
        Adb.connect(device_id)
        self.update_app_list()

    def get_version(self):
        return Adb.shell(self.id, 'getprop ro.build.version.release')

    def get_api_level(self):
        return Adb.shell(self.id, 'getprop ro.build.version.sdk')

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
        if self.get_api_level() < 23:
            # API level < 23, 4.4.3+ tested, WARNING: hardcoding
            Adb.shell(self.id, 'dumpsys battery set usb 0')
            # Adb.shell(self.id, 'dumpsys battery set ac 0')
            # Adb.shell(self.id, 'dumpsys battery set wireless 0')
        else:
            # API level 23+ (Android 6.0+)
            Adb.shell(self.id, 'dumpsys battery unplug')

    def plug(self):
        if self.get_api_level() < 23:
            # API level < 23, 4.4.3+ tested, WARNING: hardcoding
            # reset only restarts auto-update
            Adb.shell(self.id, 'dumpsys battery set usb 1')
        # API level 23+ (Android 6.0+)
        Adb.shell(self.id, 'dumpsys battery reset')

    def current_activity(self):
        # https://github.com/aldonin/appium-adb/blob/7b4ed3e7e2b384333bb85f8a2952a3083873a90e/lib/adb.js#L1278
        windows = Adb.shell(self.id, 'dumpsys window windows')
        null_re = r'mFocusedApp=null'
        # https://regex101.com/r/xZ8vF7/1
        current_focus_re = r'mCurrentFocus.+\s([^\s\/\}]+)\/[^\s\/\}]+(\.[^\s\/\}]+)}'
        focused_app_re = r'mFocusedApp.+Record\{.*\s([^\s\/\}]+)\/([^\s\/\}\,]+)(\s[^\s\/\}]+)*\}'
        match = None
        found_null = False
        for line in windows.split('\n'):
            current_focus = re.search(current_focus_re, line)
            focused_app = re.search(focused_app_re, line)
            if current_focus:
                match = current_focus
            elif focused_app and match is None:
                match = focused_app
            elif re.search(null_re, line):
                found_null = True
        if match:
            result = match.group(1).strip()
            self.logger.debug('Current activity: %s' % result)
            return result
        elif found_null:
            self.logger.debug('Current activity: null')
            return None
        else:
            self.logger.error('Results from dumpsys window windows: \n%s' % windows)
            raise AdbError('Could not parse activity from dumpsys')

    def launch(self, package, activity, action='', data_uri='', from_scratch=False, force_stop=False):
        # https://developer.android.com/studio/command-line/adb.html#am
        # https://developer.android.com/studio/command-line/adb.html#IntentSpec
        # https://stackoverflow.com/a/3229077
        cmd = 'am start'
        if force_stop:
            cmd += ' -S'
        if action:
            cmd += ' -a %s' % action
        cmd += ' -n %s/%s' % (package, activity)
        if data_uri:
            cmd += ' -d %s' % data_uri
        # https://android.stackexchange.com/a/113919
        if from_scratch:
            cmd += ' --activity-clear-task'
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

    def push(self, local, remote):
        return Adb.push(self.id, local, remote)

    def pull(self, remote, local):
        return Adb.pull(self.id, remote, local)

    def shell(self, cmd):
        return Adb.shell(self.id, cmd)

    def __str__(self):
        return '%s (%s, Android %s, API level %s)' % (self.name, self.id, self.get_version(), self.get_api_level())
