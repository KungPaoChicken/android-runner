from xml.dom import minidom
import re
import time as t
import datetime as dt


''' Power Profile '''


def get_amp_value(power_profile, component, state=0):
    """ Retrieve mAh for component in power_profile.xml and convert to Ah """
    xmlfile = minidom.parse(power_profile)
    itemlist = xmlfile.getElementsByTagName('item')
    arraylist = xmlfile.getElementsByTagName('array')
    value_index = 0
    for item in itemlist:
        itemname = item.attributes['name'].value
        milliamps = item.childNodes[0].nodeValue
        if component == itemname:
            return float(milliamps) / 1000.0
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
            return float(milliamps) / 1000.0


''' Batterystats '''


def parse_batterystats(app, batterystats_file, power_profile):
    """ Parse Batterystats history and calculate results """
    with open(batterystats_file, 'r') as bs_file:
        voltage_pattern = re.compile('(0|\+\d.*ms).*volt=(\d+)')
        app_pattern = re.compile('(0|\+\d.*ms).*( top|-top|\+top).*"{}"'.format(app))
        screen_pattern = re.compile('(0|\+\d.*ms).*([+-])screen')
        brightness_pattern = re.compile('(0|\+\d.*ms).*brightness=(dark|dim|medium|light|bright)')
        wifi_pattern = re.compile('(0|\+\d.*ms).*([+-])wifi_(on|running|scan)')
        camera_pattern = re.compile('(0|\+\d.*ms).*([+-])camera')
        time_pattern = re.compile('(0|\+\d.*ms).*')
        f = bs_file.read()

        app_start_time = convert_to_s(re.findall(app_pattern, f)[0][0])
        app_end_time = convert_to_s(re.findall(app_pattern, f)[-1][0])
        app_duration = app_end_time - app_start_time
        voltage = float(re.findall(voltage_pattern, f)[0][1]) / 1000.0
        # cam_start_time = convert_to_s(re.findall(camera_pattern, f)[0][1])
        # wifi_start_time = convert_to_s(re.findall(wifi_pattern, f)[0][0])
        screen_start_time = 0

        old_brightness = None
        wifi_activation = 0
        cam_activation = 0
        screen_activation = 0
        screen_results = []
        wifi_results = []
        cam_results = []
        all_results = []

        bs_file.seek(0)
        for line in bs_file:
            if voltage_pattern.search(line):
                voltage = get_voltage(line)

            if screen_pattern.search(line):
                screen_state = screen_pattern.search(line).group(2)
                if screen_state == '+':
                    screen_activation = 1
                    unknown_start = 1
                    old_brightness = 'dark'
                    screen_intensity = get_amp_value(power_profile, 'screen.on')
                    screen_start_time = convert_to_s(time_pattern.search(line).group(1))
            if screen_activation == 1 and brightness_pattern.search(line):
                screen_state_time = convert_to_s(brightness_pattern.search(line).group(1))
                brightness = brightness_pattern.search(line).group(2)
                intensity_range = get_amp_value(power_profile, 'screen.full') - get_amp_value(
                    power_profile, 'screen.on')
                if unknown_start == 1:
                    unknown_start = 0
                    screen_end_time = screen_state_time
                    duration = screen_end_time - screen_start_time
                    if duration == 0:
                        pass
                    else:
                        energy_consumption = calculate_energy_usage(screen_intensity, voltage, duration)
                        screen_results.append('{},{},{},{} screen,{}'.format
                                              (screen_start_time, screen_end_time, duration,
                                               old_brightness, energy_consumption))
                        screen_start_time = screen_state_time
                        old_brightness = None
                if screen_activation == 1 and unknown_start == 0 and old_brightness is None:
                    screen_start_time = screen_state_time
                    if brightness == 'dark':
                        screen_intensity = get_amp_value(power_profile, 'screen.on')
                    elif brightness == 'dim':
                        screen_intensity = get_amp_value(power_profile, 'screen.on') + (intensity_range * 0.25)
                    elif brightness == 'medium':
                        screen_intensity = get_amp_value(power_profile, 'screen.on') + (intensity_range * 0.50)
                    elif brightness == 'light':
                        screen_intensity = get_amp_value(power_profile, 'screen.on') + (intensity_range * 0.75)
                    elif brightness == 'bright':
                        screen_intensity = get_amp_value(power_profile, 'screen.full')
                    old_brightness = brightness
                elif screen_activation == 1 and unknown_start == 0 and old_brightness is not None:
                    screen_end_time = screen_state_time
                    duration = screen_end_time - screen_start_time
                    energy_consumption = calculate_energy_usage(screen_intensity, voltage, duration)
                    if screen_start_time == screen_end_time:
                        #old_brightness = brightness
                        pass
                    else:
                        screen_results.append('{},{},{},{} screen,{}'.format
                                              (screen_start_time, screen_end_time, duration,
                                               old_brightness, energy_consumption))
                    screen_start_time = screen_state_time
                    old_brightness = brightness
                elif screen_activation == 1 and screen_state == '-':
                    screen_activation = 0
                    if screen_state_time > app_end_time:
                        screen_end_time = app_end_time
                    if (screen_start_time < app_end_time) and (screen_state_time > app_end_time):
                        screen_end_time = app_end_time
                    else:
                        screen_end_time = screen_state_time
                    duration = screen_end_time - screen_start_time
                    energy_consumption = calculate_energy_usage(screen_intensity, voltage, duration)
                    screen_results.append('{},{},{},{} screen,{}'.format
                                          (screen_start_time, screen_end_time, duration,
                                           brightness, energy_consumption))

            if wifi_pattern.search(line):
                wifi_state = wifi_pattern.search(line).group(3)
                wifi_state_time = convert_to_s(wifi_pattern.search(line).group(1))
                if wifi_pattern.search(line).group(2) == '+' and wifi_state_time < app_end_time:
                    wifi_activation = 1
                    wifi_start_time = wifi_state_time
                    if wifi_state == 'on':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.on')
                    if wifi_state == 'running':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.active')
                    if wifi_state == 'scan':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.scan')
                elif wifi_pattern.search(line).group(2) == '-' and wifi_state_time < app_end_time:
                    wifi_activation = 0
                    wifi_end_time = wifi_state_time
                    duration = wifi_end_time - wifi_start_time
                    energy_consumption = calculate_energy_usage(wifi_intensity, voltage, duration)
                    wifi_results.append('{},{},{},wifi,{}'
                                        .format(wifi_start_time, wifi_end_time, duration, energy_consumption))

            if camera_pattern.search(line):
                cam_state = camera_pattern.search(line).group(2)
                cam_state_time = convert_to_s(camera_pattern.search(line).group(1))
                cam_intensity = get_amp_value(power_profile, 'camera.avg')
                if cam_state == '+' and cam_state_time < app_end_time:
                    cam_activation = 1
                    cam_start_time = cam_state_time
                elif cam_state == '-' and cam_state_time < app_end_time:
                    cam_activation = 0
                    if (cam_start_time < app_end_time) and (cam_state_time > app_end_time):
                        cam_end_time = app_end_time
                    else:
                        cam_end_time = convert_to_s(camera_pattern.search(line).group(1))
                    duration = cam_end_time - cam_start_time
                    energy_consumption = calculate_energy_usage(cam_intensity, voltage, duration)
                    cam_results.append('{},{},{},camera,{}'.format
                                       (cam_start_time, cam_end_time, duration, energy_consumption))

            """ Ignore batterystats entries after closing app """
            if convert_to_s(time_pattern.search(line).group(1)) >= app_end_time:
                if screen_activation == 1 and screen_start_time < app_end_time:
                    duration = app_duration - screen_start_time
                    energy_consumption = calculate_energy_usage(screen_intensity, voltage, duration)
                    screen_end_time = app_end_time
                    screen_activation = 0
                    screen_results.append('{},{},{},{} screen,{}'
                                          .format(screen_start_time, screen_end_time, duration,
                                                  old_brightness, energy_consumption))
                if wifi_activation == 1 and wifi_start_time < app_end_time:
                    duration = app_duration - wifi_start_time
                    energy_consumption = calculate_energy_usage(wifi_intensity, voltage, duration)
                    wifi_end_time = app_end_time
                    wifi_activation = 0

                    wifi_results.append('{},{},{},wifi,{}'.format(wifi_start_time, wifi_end_time, duration,
                                                                     energy_consumption))
                if cam_activation == 1 and cam_start_time < app_end_time:
                    duration = app_duration - cam_start_time
                    energy_consumption = calculate_energy_usage(cam_intensity, voltage, duration)
                    cam_end_time = app_end_time
                    cam_activation = 0
                    cam_results.append('{},{},{},camera,{}'.format(cam_start_time, cam_end_time, duration,
                                                                      energy_consumption))
                else:
                    continue
    all_results.extend(wifi_results + cam_results + screen_results)
    return all_results


def get_voltage(line):
    """ Obtain voltage value """
    pattern = re.compile('volt=(\d+)')
    match = pattern.search(line)
    return float(match.group(1)) / 1000.0


def calculate_energy_usage(intensity, voltage, duration):
    return intensity * voltage * duration


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

    SECONDS_IN_MS = 1000.0
    SECONDS_IN_M = 60.0
    SECONDS_IN_H = 3600.0
    SECONDS_IN_D = 86400.0

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


def parse_systrace(app, systrace_file, logcat, batterystats, power_profile):
    """ Parse systrace file and calculate results """
    with open(batterystats, 'r') as bs:
        voltage_pattern = re.compile('(0|\+\d.*ms).*volt=(\d+)')
        voltage = float(re.findall(voltage_pattern, bs.read())[0][1]) / 1000.0

    with open(systrace_file, 'r') as sys:
        f = sys.read()
        pattern = re.compile('(?:<.{3,4}>-\d{1,4}|kworker.+-\d{3}).*\s(\d+\.\d+): (cpu_.*): state=(.*) cpu_id=(\d)')
        matches = pattern.finditer(f)
        unix_time_pattern = re.compile('(\d+\.\d+):\stracing_mark_write:\strace_event_clock_sync:\srealtime_ts=(\d+)')
        logcat_time = parse_logcat(app, logcat)
        if unix_time_pattern.search(f):
            systrace_time = float(unix_time_pattern.search(f).group(2))
            start_time = (logcat_time[0] - systrace_time) / 1000 + float(unix_time_pattern.search(f).group(1))
            end_time = (logcat_time[1] - systrace_time) / 1000 + float(unix_time_pattern.search(f).group(1))
        else:
            start_time = float(pattern.search(f).group(1))
            end_time = float(re.findall(pattern, f)[-1][0])
        cpu_id_list = []
        results = []

        for match in matches:
            current_time = float(match.group(1))
            current_cpu_id = int(match.group(4))
            if current_time > end_time or current_time < start_time:
                pass
            else:
                if (current_cpu_id not in cpu_id_list) and (current_time <= end_time):
                    cpu_id_list.append(current_cpu_id)
                elif (current_cpu_id in cpu_id_list) and (current_time <= end_time):
                    continue
                elif current_time > end_time:
                    break
        for cpu_id in cpu_id_list:
            matches = pattern.finditer(f)
            found_first_match = 0
            for match in matches:
                current_time = float(match.group(1))
                current_category = str(match.group(2))
                current_state = int(match.group(3))
                current_cpu_id = int(match.group(4))
                if current_time > end_time or current_time < start_time:
                    pass
                else:
                    #current_time = float(match.group(1))
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
                                cpu_intensity = get_amp_value(power_profile, category, state)
                                energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                                results.append('{},{},{},core {} {},{}'.format
                                               (time - start_time, current_time - start_time, duration, cpu_id, category, energy_consumption))
                                time = current_time
                                category = current_category
                                state = current_state
                            elif current_category != category:
                                duration = current_time - time
                                #print current_time
                                cpu_intensity = get_amp_value(power_profile, category, state)
                                energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                                results.append('{},{},{},core {} {},{}'.format
                                               (time - start_time, current_time - start_time, duration, cpu_id, category, energy_consumption))
                                time = current_time
                                category = current_category
                                state = current_state
                    elif (current_time >= end_time) and (current_category == category) and (current_state == state):
                        duration = current_time - time
                        cpu_intensity = get_amp_value(power_profile, category, state)
                        energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                        results.append('{},{},{},core {} {},{}'.format
                                       (time - start_time, current_time - start_time, duration, cpu_id, category, energy_consumption))
                        #results.append(' ')
                        found_first_match = 0
                        break
    return results


''' Logcat '''


def parse_logcat(app, logcat_file):
    """ Obtain app start and end times from logcat """
    with open(logcat_file, 'r') as f:
        logcat = f.read()
        app_start_pattern = re.compile(
            '(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).(\d{3}).*ActivityManager:\sDisplayed\s(%s)' % app)
        app_start_date = re.findall(app_start_pattern, logcat)[0][0]
        year = dt.datetime.now().year
        time_tuple = t.strptime('{}-{}'.format(year, app_start_date), '%Y-%m-%d %H:%M:%S')
        unix_start_time = int(t.mktime(time_tuple)) * 1000 + int(app_start_pattern.search(logcat).group(2))

        app_stop_pattern = re.compile(
            '(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).(\d{3}).*ActivityManager:\sForce\sstopping\s(%s)' % app)
        app_stop_date = re.findall(app_stop_pattern, logcat)[-1][0]
        time_tuple = t.strptime('{}-{}'.format(year, app_stop_date), '%Y-%m-%d %H:%M:%S')
        unix_end_time = int(t.mktime(time_tuple)) * 1000 + int(app_stop_pattern.search(logcat).group(2))
        return unix_start_time, unix_end_time

# Test
# parse_systrace('net.sourceforge.opencamera', 'Test/systrace.html', 'Test/logcat.txt', 'Test/batterystats_history.txt', 'Test/power_profile.xml')
# parse_batterystats('net.sourceforge.opencamera', 'Test/batterystats_history.txt', 'Test/power_profile.xml')