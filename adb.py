from pyand import ADB

adb = ADB(adb_path='/opt/platform-tools/adb')


def devices():
    return adb.get_devices()


def shell(device, cmd):
    # adb.set_target_by_name(device)
    return adb.shell_command(cmd)


def is_installed(device, name):
    # adb.set_target_by_name(device)
    return adb.shell_command('adb shell pm list packages | grep %s' % name)

