# https://developer.android.com/studio/test/monkeyrunner/index.html#SampleProgram
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import sys
import os
import os.path as op
import errno
import time


def makedirs(path):
    # https://stackoverflow.com/a/5032238
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

if len(sys.argv) < 4:
    print('Not sufficient amount of arguments')
    print('Usage: monkey.py device_regex current_activity save_path')
    sys.exit(1)

print('monkeyrunner called with: %s' % sys.argv)

device_id = sys.argv[1]
current_activity = sys.argv[2]
config_path = sys.argv[3]

timeout = 10

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection(timeout, sys.argv[1])

# Installs the Android package. Notice that this method returns a boolean, so you can test
# to see if the installation worked.
# device.installPackage('myproject/bin/MyApplication.apk')

# sets a variable with the package's internal name
# package = 'com.example.android.myapplication'

# sets a variable with the name of an Activity in the package
# activity = 'com.example.android.myapplication.MainActivity'

# sets the name of the component to start
# runComponent = package + '/' + activity

# Runs the component
# device.startActivity(component=runComponent)

# Presses the Menu button
# device.press('KEYCODE_MENU', MonkeyDevice.DOWN_AND_UP)

output_dir = op.join(config_path, 'output/screenshots/')
makedirs(output_dir)
filename = '%s_%s.png' % (device_id, time.strftime('%Y.%m.%d_%H%M%S'))
# Takes a screenshot and writes the screenshot to a file
result = device.takeSnapshot()
result.writeToFile(op.join(output_dir, filename), 'png')
