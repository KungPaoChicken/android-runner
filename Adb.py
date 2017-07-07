from pyand import ADB


class AdbError(Exception):
    """Raised when there's an error with ADB"""
    pass


class ConnectionError(Exception):
    """Raised when there's an connection error"""
    pass


adb = ADB(adb_path='/opt/platform-tools/adb')


def connect(dev_id):
    device_list = adb.get_devices()
    if not device_list:
        raise ConnectionError('No devices are connected')
    if dev_id not in device_list.values():
        raise ConnectionError('Error: Device %s is not connected' % dev_id)


def shell(device_id, cmd):
    adb.set_target_by_name(device_id)
    result = adb.shell_command(cmd)
    if 'error' in result:
        print(result)
        raise AdbError('Error in shell')
    return result


def list_apps(device_id):
    return shell(device_id, 'pm list packages')


def install(device_id, apk):
    adb.set_target_by_name(device_id)
    return adb.install(apk)


def uninstall(device_id, name):
    adb.set_target_by_name(device_id)
    print('Uninstall stub: ' + name)
    return shell(device_id, 'uninstall %s' % name)


def push(device_id, local, remote):
    adb.set_target_by_name(device_id)
    return adb.push_local_file(local, remote)


def pull(device_id, remote, local):
    adb.set_target_by_name(device_id)
    return adb.get_remote_file(remote, local)


def unplug(device_id):
    return shell(device_id, 'dumpsys battery unplug')


def plug(device_id):
    return shell(device_id, 'dumpsys battery reset')


def logcat(device_id, param=""):
    adb.set_target_by_name(device_id)
    return adb.get_logcat(lcfilter=param)