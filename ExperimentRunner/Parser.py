from xml.dom import minidom
import csv
import os.path as op
import re

SECONDS_IN_MS = 1000.0
SECONDS_IN_M = 60.0
SECONDS_IN_H = 3600.0
SECONDS_IN_D = 86400.0


''' Power Profile '''


def parse_power_profile(power_profile, out_dir=''):
    """ Parse PP into a CSV file (Obsolete) """
    output_file = op.join(out_dir, 'power_profile.csv')
    xmlfile = minidom.parse(power_profile)
    itemlist = xmlfile.getElementsByTagName('item')
    arraylist = xmlfile.getElementsByTagName('array')
    for item in itemlist:
        rows = []
        itemname = item.attributes['name'].value
        itemvalue = item.childNodes[0].nodeValue
        rows.append(itemname)
        rows.append(itemvalue)
        with open(output_file, 'a') as f:
            writer = csv.writer(f, rows)
            writer.writerow(rows)
    for array in arraylist:
        rows = []
        arrayname = array.attributes['name'].value
        valuelist = array.getElementsByTagName('value')
        rows.append(arrayname)
        for value in valuelist:
            val = value.childNodes[0].nodeValue
            rows.append(val)
        with open(output_file, 'a') as f:
            writer = csv.writer(f, rows)
            writer.writerow(rows)


def get_consumption_value(power_profile, component, state=0):
    """ Retrieve mAh for component in power_profile.xml """
    xmlfile = minidom.parse(power_profile)
    itemlist = xmlfile.getElementsByTagName('item')
    arraylist = xmlfile.getElementsByTagName('array')
    value_index = 0
    for item in itemlist:
        itemname = item.attributes['name'].value
        milliamps = item.childNodes[0].nodeValue
        if component == itemname:
            return float(milliamps)
    for arrays in arraylist:
        arrayname = arrays.attributes['name'].value
        if arrayname == 'cpu.speeds':
            valuelist = arrays.getElementsByTagName('value')
            for i in range(valuelist.length):
                value = valuelist.item(i).childNodes[0].nodeValue
                if value == state:
                    value_index = i
        if arrayname == 'cpu.active':
            valuelist = arrays.getElementsByTagName('value')
            milliamps = valuelist.item(value_index).childNodes[0].nodeValue
            return float(milliamps)


''' Batterystats '''


def parse_batterystats(app, batterystats_file, power_profile, filename):
    """ Parse Batterystats history and calculate results """
    with open(batterystats_file, 'r') as f:
        voltage_pattern = re.compile('(0|\+\d.*ms).*volt=(\d+)')
        app_pattern = re.compile('(0|\+\d.*ms).*( top|\-top|\+top).*"{}"'.format(app))
        wifi_pattern = re.compile('(0|\+\d.*ms).*(\+|\-)wifi_(on|running|scan)')
        camera_pattern = re.compile('(0|\+\d.*ms).*(\+|\-)camera')
        screen_pattern = re.compile('(0|\+\d.*ms).*(\+|\-)screen.*brightness=(dark|dim|medium|bright)')
        # phonescanning_pattern = re.compile('(0|\+\d.*ms).*\+phone_scanning')
        # time_pattern = re.compile('(0|\+\d.*ms).*')

        app_start_time = 0
        app_end_time = 0
        app_duration = 0
        voltage = 0
        cam_start_time = 0
        cam_end_time = 0
        wifi_start_time = 0
        wifi_end_time = 0
        screen_start_time = 0
        screen_end_time = 0

        wifi_activation = 0
        cam_activation = 0
        screen_activation = 0
        wifi_results = []
        cam_results = []
        screen_results = []

        for line in f:
            if voltage_pattern.search(line):
                voltage = voltage_pattern.search(line).group(2)
                #print 'voltage: {}'.format(voltage)
            if app_pattern.search(line):
                if app_pattern.search(line).group(2) == ' top' or app_pattern.search(line).group(2) == '+top':
                    app_start_time = convert_to_s(app_pattern.search(line).group(1))
                    #print 'app start {}'.format(app_start_time)
                if app_pattern.search(line).group(2) == '-top':
                    app_end_time = convert_to_s(app_pattern.search(line).group(1))
                    #print 'app end {}'.format(app_end_time)
                    app_duration = app_end_time - app_start_time

            if wifi_pattern.search(line):
                wifi_activation = 1
                wifi_state = wifi_pattern.search(line).group(3)
                wifi_state_time = convert_to_s(wifi_pattern.search(line).group(1))
                if wifi_pattern.search(line).group(2) == '+':
                    wifi_start_time = wifi_state_time
                    if wifi_state == 'on':  # may be obsolete, wifi seems to be always running or scanning when it is on
                        wifi_consumption = get_consumption_value(power_profile, 'wifi.on')
                    if wifi_state == 'running':
                        wifi_consumption = get_consumption_value(power_profile, 'wifi.active')
                    if wifi_state == 'scan':
                        wifi_consumption = get_consumption_value(power_profile, 'wifi.scan')
                elif wifi_pattern.search(line).group(2) == '-':
                    wifi_activation = 0
                    if (wifi_start_time < app_end_time) and (wifi_state_time > app_end_time):
                        wifi_end_time = app_end_time
                    else:
                        wifi_state_time = convert_to_s(wifi_pattern.search(line).group(1))
                        wifi_end_time = wifi_state_time
                    duration = wifi_end_time - wifi_start_time
                    intensity = (wifi_consumption * duration / SECONDS_IN_H)
                    wifi_results.append('{}-{} ({}s), wifi, {}'
                                        .format(wifi_start_time, wifi_end_time, duration, intensity))

            if camera_pattern.search(line):
                cam_state = camera_pattern.search(line).group(2)
                cam_state_time = convert_to_s(camera_pattern.search(line).group(1))
                cam_consumption = get_consumption_value(power_profile, 'camera.avg')
                #print cam_state_time
                #print app_end_time
                if cam_state == '+':
                    cam_activation = 1
                    cam_start_time = cam_state_time
                elif cam_state == '-':
                    cam_activation = 0
                    if (cam_start_time < app_end_time) and (cam_state_time > app_end_time):
                        cam_end_time = app_end_time
                    else:
                        cam_end_time = convert_to_s(camera_pattern.search(line).group(1))
                    duration = cam_end_time - cam_start_time
                    intensity = (cam_consumption * duration / SECONDS_IN_H)
                    # print '{}-{} ({}s), camera, {} mAh'.format(cam_start_time, cam_end_time, duration, intensity)
                    cam_results.append('{}-{} ({}s), camera, {}'.format(cam_start_time, cam_end_time, duration, intensity))

            if screen_pattern.search(line):
                screen_activation = 1
                screen_state_time = convert_to_s(screen_pattern.search(line).group(1))
                screen_state = screen_pattern.search(line).group(2)
                brightness = screen_pattern.search(line).group(3)
                consumption_range = get_consumption_value(power_profile, 'screen.full') - get_consumption_value(power_profile, 'screen.on')
                if screen_state == '+':
                    screen_start_time = screen_state_time
                    if brightness == 'dark':
                        screen_consumption = get_consumption_value(power_profile, 'screen.on')
                    elif brightness == 'dim':
                        screen_consumption = get_consumption_value(power_profile, 'screen.on') + (consumption_range * 0.25)
                    elif brightness == 'medium':
                        screen_consumption = get_consumption_value(power_profile, 'screen.on') + (consumption_range * 0.50)
                    elif brightness == 'light':
                        screen_consumption = get_consumption_value(power_profile, 'screen.on') + (consumption_range * 0.75)
                    elif brightness == 'bright':
                        screen_consumption = get_consumption_value(power_profile, 'screen.full')
                elif screen_state == '-':
                    screen_activation = 0
                    if screen_state_time > app_end_time:
                        screen_end_time = app_end_time
                        # print screen_end_time
                    if (screen_start_time < app_end_time) and (screen_state_time > app_end_time):
                        screen_end_time = app_end_time
                    else:
                        screen_end_time = screen_state_time
                    duration = screen_end_time - screen_start_time
                    intensity = (screen_consumption * duration / SECONDS_IN_H)
                    # print '{}-{} ({}s), screen, {} mAh'.format(screen_start_time, screen_end_time, duration, intensity)
                    screen_results.append('{}-{} ({}s), screen, {}'.format(screen_start_time, screen_end_time, duration, intensity))

            if wifi_activation == 1 and app_duration > 0 and wifi_start_time < app_end_time:
                duration = app_duration - wifi_start_time
                intensity = (wifi_consumption * duration / SECONDS_IN_H)
                wifi_end_time = app_end_time
                wifi_activation = 0
                wifi_results.append('{}-{} ({}s), wifi, {}'.format(wifi_start_time, wifi_end_time, duration, intensity))
            if cam_activation == 1 and app_duration > 0 and cam_start_time < app_end_time < cam_state_time:
                duration = app_duration - cam_start_time
                intensity = (cam_consumption * duration / SECONDS_IN_H)
                cam_end_time = app_end_time
                cam_activation = 0
                cam_results.append('{}-{} ({}s), cam, {}'.format(cam_start_time, cam_end_time, duration, intensity))
            if screen_activation == 1 and app_duration > 0 and screen_end_time < app_end_time:
                duration = app_duration - screen_start_time
                intensity = (screen_consumption * duration / SECONDS_IN_H)
                screen_end_time = app_end_time
                screen_activation = 0
                # print '{}-{} ({}s), screen, {} mAh'.format(screen_start_time, duration, duration, intensity)
                screen_results.append('{}-{} ({}s), screen, {}'
                                      .format(screen_start_time, screen_end_time, duration, intensity))


    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter="\n")
        writer.writerow(wifi_results)
        #writer.writerow(' ')
        writer.writerow(cam_results)
        #writer.writerow(' ')
        writer.writerow(screen_results)
        #writer.writerow(' ')

        # Bluetooth
        # dsp.audio
        # dsp.video
        # camera.flashlight
        # gps.on
        # radio.active
        # radio.scanning
        # radio.on


def get_voltage(line):
    """ Obtain voltage value """
    pattern = re.compile('volt=(\d+)')
    match = pattern.search(line)
    return int(match.group(1))


def convert_to_s(line):
    """ Convert Batterystats timestamps to seconds """
    milliseconds_pattern = re.compile('\+(\d{3})ms')
    seconds_pattern = re.compile('\+(\d{1,2})s(\d{3})ms')
    minutes_pattern = re.compile('\+(\d{1,2})m(\d{2})s(\d{3})ms')
    hours_pattern = re.compile('\+(\d{1,2})h(\d{1,2})m(\d{2})s(\d{3})ms')
    days_pattern = re.compile('\+(\d)d(\d{1,2})h(\d{1,2})m(\d{2})s(\d{3})ms')

    milliseconds_matches = milliseconds_pattern.search(line)
    seconds_matches = seconds_pattern.search(line)
    minutes_matches = minutes_pattern.search(line)
    hours_matches = hours_pattern.search(line)
    days_matches = days_pattern.search(line)

    if milliseconds_matches:
        s = float(milliseconds_matches.group(1)) / SECONDS_IN_MS
        return s
    elif seconds_matches:
        s = float(seconds_matches.group(2)) / SECONDS_IN_MS
        s += float(seconds_matches.group(1))
        return s
    elif minutes_matches:
        s = float(minutes_matches.group(3)) / SECONDS_IN_MS
        s += float(minutes_matches.group(2))
        s += float(minutes_matches.group(1)) * SECONDS_IN_M
        return s
    elif hours_matches:
        s = float(hours_matches.group(4)) / SECONDS_IN_MS
        s += float(hours_matches.group(3))
        s += float(hours_matches.group(2)) * SECONDS_IN_M
        s += float(hours_matches.group(1)) * SECONDS_IN_H
        return s
    elif days_matches:
        s = float(days_matches.group(5)) / SECONDS_IN_MS
        s += float(days_matches.group(4))
        s += float(days_matches.group(3)) * SECONDS_IN_M
        s += float(days_matches.group(2)) * SECONDS_IN_H
        s += float(days_matches.group(1)) * SECONDS_IN_D
        return s
    else:
        return 0


''' Systrace '''


def parse_systrace(systrace_file, power_profile, filename):
    """ Parse systrace file and calculate results """
    file = open(systrace_file, 'r').read()
    pattern = re.compile('(?:<.{3,4}>-\d{1,4}|kworker.+\-\d{3}).*\s(\d+\.\d+): (cpu_.*): state=(.*) cpu_id=(\d)')
    matches = pattern.finditer(file)
    end_time = re.findall(pattern, file)[-1][0]
    cpu_id_list = []
    results = []

    for match in matches:
        current_time = float(match.group(1))
        current_cpu_id = int(match.group(4))

        if (current_cpu_id not in cpu_id_list) and (current_time <= end_time):
            cpu_id_list.append(current_cpu_id)
        elif (current_cpu_id in cpu_id_list) and (current_time <= end_time):
            continue
        elif current_time > end_time:
            break
    for cpu_id in cpu_id_list:
        matches = pattern.finditer(file)
        found_first_match = 0
        for match in matches:
            current_time = float(match.group(1))
            current_category = str(match.group(2))
            current_state = int(match.group(3))
            current_cpu_id = int(match.group(4))
            if (found_first_match == 0) and (current_cpu_id == cpu_id):
                time = float(match.group(1))
                category = str(match.group(2))
                state = int(match.group(3))
                cpu_id = int(match.group(4))
                found_first_match = 1
            if found_first_match == 1:
                if (current_time <= end_time) and (current_cpu_id == cpu_id):
                    if (current_category == category) and (current_state == state):
                        pass
                    elif current_category == category == 'cpu_idle':
                        pass
                    elif (current_category == category == 'cpu_frequency') and (current_state == state):
                        pass
                    elif (current_category == category == 'cpu_frequency') and (current_state != state):
                        duration = current_time - time
                        intensity = get_consumption_value(power_profile, category, state) * duration
                        results.append('{}-{} ({}s), core {} {}, {}'
                                       .format(time, current_time, duration, cpu_id, category, intensity))
                        time = current_time
                        category = current_category
                        state = current_state
                    elif current_category != category:
                        duration = (current_time - time) / SECONDS_IN_H
                        intensity = get_consumption_value(power_profile, category, state) * duration
                        results.append('{}-{} ({}s), core {} {}, {}'
                                       .format(time, current_time, duration, cpu_id, category, intensity))
                        time = current_time
                        category = current_category
                        state = current_state
                elif (current_time >= end_time) and (current_category == category) and (current_state == state):
                    duration = (current_time - time) / SECONDS_IN_H
                    intensity = get_consumption_value(power_profile, category, state) * duration
                    results.append('{}-{} ({}s), core {} {}, {}'
                                   .format(time, current_time, duration, cpu_id, category, intensity))
                    results.append(' ')
                    found_first_match = 0
                    break
    with open(filename, 'a') as f:
        writer = csv.writer(f, delimiter="\n")
        writer.writerow(results)


parse_batterystats('test.androidrunner', 'batterystats_test.txt', 'power_profile_nexus7.xml', 'result.csv')
#parse_systrace('systrace.html', 'power_profile_nexus7.xml', 'result.csv')

#get_consumption_value('power_profile_nexus7.xml', 'cpu.speeds', '1026000')