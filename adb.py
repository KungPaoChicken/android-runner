from pyand import ADB

adb = ADB(adb_path='/opt/platform-tools/adb')


def devices():
    return adb.get_devices()
