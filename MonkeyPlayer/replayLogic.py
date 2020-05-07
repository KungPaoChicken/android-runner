import sys
# import os
import time

from com.android.monkeyrunner import MonkeyDevice, MonkeyRunner
from com.xhaus.jyson import JysonCodec as json


def run_input(action, newdevice, test):
    action_complete = True
    if action['type'] == 'touch':
        if 'x' in action and 'y' in action and 'up' in action and 'down' in action:
            counter = (float(action['up']) - float(action['down'])) / 1000
            if test:
                print('touch at (' + str(action['x']) + ", " + str(action['y']) + ") for " + str(counter) + " seconds")
            else:
                if str(action['x']).isdigit() and str(action['y']).isdigit():
                    newdevice.touch(action['x'], action['y'], 'DOWN_AND_UP')
                    MonkeyRunner.sleep(counter)
                    # newdevice.touch(action['x'], action['y'], 'UP')
                else:
                    action_complete = False
        else:
            action_complete = False

    elif action['type'] == 'drag':
        counter = float(action['up']) - float(action['down'])
        str_tuple = (action['points'][0]['x'], action['points'][0]['y'])
        end_tuple = (action['points'][1]['x'], action['points'][1]['y'])
        if test:
            print('drag from ' + str(str_tuple) + ' to ' + str(end_tuple) + ' for ' + str(counter))
        else:
            newdevice.drag(str_tuple, end_tuple, counter, 10)
    elif action['type'] == 'press':
        counter = float(action['up']) - float(action['down'])
        times = len(action['keys'])
        # print str(times) + 'keys to press'
        if test:
            for i in range(times):
                print('pressed %s key for %d' % (action['keys'][i]['key'], counter))
        else:
            for i in range(times):
                newdevice.press(action['keys'][i]['key'], MonkeyDevice.DOWN)
            MonkeyRunner.sleep(counter)
            for i in range(times):
                newdevice.press(action['keys'][i]['key'], MonkeyDevice.UP)
    else:
        action_complete = False
    return action_complete


def get_time_difference(curr_line, prev_line):
    if "'" not in curr_line and "'" not in prev_line:
        curr_event = json.loads(curr_line)
        prev_event = json.loads(prev_line)
        difference = (float(curr_event['down']) - float(prev_event['up'])) / 1000
        return difference
    else:
        return 0


def run_jblock(filename, newdevice):
    f = open(filename, 'r')
    '''
    except IOError: 
        print 'problem reading:' + filename
    '''
    print("opened file")
    total_completed = 0
    total_actions = 0
    '''
    if not os.path.exists('./images'):
        os.mkdir('./images')
    newdevice.wake()
    pathName = os.path.abspath('./images')
    #print pathName
    startShot = os.path.join(pathName, 'start.png')
    screenshot = newdevice.takeSnapshot()
    screenshot.writeToFile(startShot)
    '''
    prev_line = None
    for line in f:
        if prev_line is not None:
            time_diff = get_time_difference(line, prev_line)
            time.sleep(time_diff)
        prev_line = line
        total_actions += 1
        single_quotes = line.find("\'")
        if single_quotes == -1:
            device_input = json.loads(line)
            complete = run_input(device_input, newdevice, False)  # change to True to
            if complete:
                total_completed += 1
            else:
                action = str(device_input).replace(': u', ': ')
                print('could not replay action ' + str(action))
        else:
            print('could not replay action ' + line)
    print(str(total_completed) + '/' + str(total_actions) + ' actions completed')
    f.close()
    '''
    time.sleep(5)
    screenshotFinal = newdevice.takeSnapshot()
    finishShot = os.path.join(pathName, 'finish.png')
    screenshotFinal.writeToFile(finishShot)
    same = screenshot.sameAs(screenshotFinal, 0.999)
    print 'The images are the same: ' + str(same)
    '''


def main():
    if len(sys.argv) == 1:
        filename = 'testLogicLog.txt'
    else:
        filename = sys.argv[1]
    newdevice = MonkeyRunner.waitForConnection(5.0)
    run_jblock(filename, newdevice)
    print('done')


# optparse
if __name__ == '__main__':
    main()
