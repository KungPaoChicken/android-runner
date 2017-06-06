import os.path as op

from adb import adb_commands
from adb import sign_m2crypto
from adb import usb_exceptions


# KitKat+ devices require authentication
signer = sign_m2crypto.M2CryptoSigner(
    op.expanduser('~/.android/adbkey')
)


def connect(device_id):
    try:
        return adb_commands.AdbCommands.ConnectDevice(serial=device_id, rsa_keys=[signer])
    except usb_exceptions.DeviceNotFoundError:
        raise

# Now we can use Shell, Pull, Push, etc!
# for i in xrange(10):
#     print device.Shell('echo %d' % i)
