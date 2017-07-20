import logging
import os.path as op
from pyand import ADB

logger = logging.getLogger(__name__)


class AdbError(Exception):
    """Raised when there's an error with ADB"""
    pass


class ConnectionError(Exception):
    """Raised when there's an connection error"""
    pass


adb = ADB(adb_path='/opt/platform-tools/adb')


def connect(device_id):
    device_list = adb.get_devices()
    if not device_list:
        raise ConnectionError('No devices are connected')
    if device_id not in device_list.values():
        raise ConnectionError('Error: Device %s is not connected' % device_id)


def shell(device_id, cmd):
    adb.set_target_by_name(device_id)
    result = adb.shell_command(cmd)
    logger.debug('%s: Result of "%s": \n%s' % (device_id, cmd, result))
    if 'error' in result:
        print(result)
        raise AdbError('Error in shell')
    return result


def list_apps(device_id):
    return shell(device_id, 'pm list packages').replace('package:', '').split()


def install(device_id, apk):
    filename = op.basename(apk)
    logger.info('%s: Installing "%s"' % (device_id, filename))
    adb.set_target_by_name(device_id)
    result = adb.install(apk)
    success_or_exception(result,
                         '%s: "%s" installed' % (device_id, filename),
                         '%s: Failed to install "%s"' % (device_id, filename)
                         )


def uninstall(device_id, name):
    logger.info('%s: Uninstalling "%s"' % (device_id, name))
    adb.set_target_by_name(device_id)
    result = adb.uninstall(package=name, keepdata=False)
    success_or_exception(result,
                         '%s: "%s" uninstalled' % (device_id, name),
                         '%s: Failed to uninstall "%s"' % (device_id, name)
                         )


def clear_app_data(device_id, name):
    adb.set_target_by_name(device_id)
    success_or_exception(adb.shell_command('pm clear %s' % name),
                         '%s: Data of "%s" cleared' % (device_id, name),
                         '%s: Failed to clear data for "%s"' % (device_id, name)
                         )


def success_or_exception(result, success_msg, fail_msg):
    if 'Success' in result:
        logger.info(success_msg)
    else:
        logger.info(fail_msg + '\nMessage returned:\n%s' % result)
        raise AdbError(result)


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


def logcat(device_id, regex=None):
    # https://developer.android.com/studio/command-line/logcat.html#Syntax
    # -d prints to screen and exits
    params = '-d'
    if regex is not None:
        params += ' -e %s' % regex
    adb.set_target_by_name(device_id)
    return adb.get_logcat(lcfilter=params)
