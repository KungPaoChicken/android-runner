from xml.dom import minidom
import re
import time as t
import datetime as dt


''' Power Profile '''


def get_amp_value(power_profile, component, state=''):
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
        wifi_pattern = re.compile('(0|\+\d.*ms).*([+-])wifi_(running|radio|scan)')
        camera_pattern = re.compile('(0|\+\d.*ms).*([+-])camera')
        flashlight_pattern = re.compile('(0|\+\d.*ms).*([+-])flashlight')
        gps_pattern = re.compile('(0|\+\d.*ms).*([+-])gps')
        audio_pattern = re.compile('(0|\+\d.*ms).*([+-])audio')
        video_pattern = re.compile('(0|\+\d.*ms).*([+-])video')
        bluetooth_pattern = re.compile('(0|\+\d.*ms).*([+-])ble_scan')
        phone_scanning_pattern = re.compile('(0|\+\d.*ms).*([+-])phone_scanning')
        time_pattern = re.compile('(0|\+\d.*ms).*')
        f = bs_file.read()

        app_start_time = convert_to_s(re.findall(app_pattern, f)[0][0])
        app_end_time = convert_to_s(re.findall(app_pattern, f)[-1][0])
        voltage = float(re.findall(voltage_pattern, f)[0][1]) / 1000.0

        brightness = None
        screen_start_time = 0
        screen_activation = 0
        wifi_activation = 0
        cam_activation = 0
        flashlight_activation = 0
        gps_activation = 0
        video_activation = 0
        audio_activation = 0
        bluetooth_activation = 0
        phone_scanning_activation = 0

        screen_results = []
        wifi_results = []
        cam_results = []
        flashlight_results = []
        gps_results = []
        audio_results = []
        video_results = []
        bluetooth_results = []
        phone_scanning_results = []
        all_results = []

        bs_file.seek(0)
        for line in bs_file:
            current_time = convert_to_s(time_pattern.search(line).group(1))

            if voltage_pattern.search(line):
                voltage = get_voltage(line)

            if screen_activation == 0 and screen_pattern.search(line) and brightness_pattern.search(line):
                screen_state = screen_pattern.search(line).group(2)
                if screen_state == '+' and brightness is None:
                    screen_activation = 1
                    screen_start_time = current_time
                    brightness = brightness_pattern.search(line).group(2)
            elif screen_activation == 0 and screen_pattern.search(line):
                screen_state = screen_pattern.search(line).group(2)
                if screen_state == '+' and brightness is None:
                    screen_activation = 1
                    screen_start_time = app_start_time
                    brightness = 'dark'
            elif screen_activation == 1 and brightness_pattern.search(line):
                if screen_start_time < app_start_time:
                    screen_start_time = app_start_time
                screen_end_time = current_time
                duration = screen_end_time - screen_start_time
                intensity = get_screen_intensity(brightness, power_profile)
                energy_consumption = calculate_energy_usage(intensity, voltage, duration)
                if screen_end_time >= app_start_time and duration != 0:
                    screen_results.append('{},{},{},screen {},{}'.format(
                        screen_start_time - app_start_time, screen_end_time - app_start_time,
                        duration, brightness, energy_consumption))
                brightness = brightness_pattern.search(line).group(2)
                screen_start_time = current_time
            elif screen_activation == 1 and current_time >= app_end_time:
                screen_activation = 0
                if screen_start_time < app_start_time:
                    screen_start_time = app_start_time
                screen_end_time = app_end_time
                duration = screen_end_time - screen_start_time
                intensity = get_screen_intensity(brightness, power_profile)
                energy_consumption = calculate_energy_usage(intensity, voltage, duration)
                if screen_end_time >= app_start_time and duration != 0:
                    screen_results.append('{},{},{},screen {},{}'.format(
                        screen_start_time - app_start_time, screen_end_time - app_start_time,
                        duration, brightness, energy_consumption))
            elif screen_activation == 1 and screen_pattern.search(line):
                screen_state = screen_pattern.search(line).group(2)
                if screen_state == '-':
                    screen_activation = 0
                    if screen_start_time < app_start_time:
                        screen_start_time = app_start_time - app_start_time
                    screen_end_time = current_time - app_start_time
                    duration = screen_end_time - screen_start_time
                    intensity = get_screen_intensity(brightness, power_profile)
                    energy_consumption = calculate_energy_usage(intensity, voltage, duration)
                    if screen_end_time >= app_start_time:
                        screen_results.append('{},{},{},screen {},{}'.format(
                            screen_start_time - app_start_time, screen_end_time - app_start_time,
                            duration, brightness, energy_consumption))

            if wifi_pattern.search(line):
                wifi_state = wifi_pattern.search(line).group(3)
                if wifi_activation == 0 and wifi_pattern.search(line).group(2) == '+' and current_time < app_end_time:
                    wifi_activation = 1
                    old_wifi_state = wifi_state
                    if current_time < app_start_time:
                        wifi_start_time = app_start_time
                    else:
                        wifi_start_time = current_time
                elif wifi_activation == 1 and wifi_state != old_wifi_state and wifi_pattern.search(line).group(2) == '+':
                    if old_wifi_state == 'running':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.on')
                    if old_wifi_state == 'radio':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.active')
                    if old_wifi_state == 'scan':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.scan')
                    wifi_end_time = current_time
                    duration = wifi_end_time - wifi_start_time
                    energy_consumption = calculate_energy_usage(wifi_intensity, voltage, duration)
                    wifi_results.append('{},{},{},wifi {},{}'.format(
                        wifi_start_time - app_start_time, wifi_end_time - app_start_time, duration,
                        old_wifi_state, energy_consumption))
                    wifi_start_time = current_time
                elif wifi_activation == 1 and wifi_pattern.search(line).group(2) == '-' and current_time < app_end_time:
                    if wifi_state == 'radio':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.active')
                    if wifi_state == 'scan':
                        wifi_intensity = get_amp_value(power_profile, 'wifi.scan')
                    wifi_end_time = current_time
                    duration = wifi_end_time - wifi_start_time
                    energy_consumption = calculate_energy_usage(wifi_intensity, voltage, duration)
                    wifi_results.append('{},{},{},wifi {},{}'.format(
                        wifi_start_time - app_start_time, wifi_end_time - app_start_time, duration,
                        wifi_state, energy_consumption))
                    wifi_start_time = current_time
                    wifi_state = 'running'
            if wifi_activation == 1 and current_time >= app_end_time:
                wifi_activation = 0
                wifi_end_time = app_end_time
                duration = wifi_end_time - wifi_start_time
                if wifi_state == 'running':
                    wifi_intensity = get_amp_value(power_profile, 'wifi.on')
                if wifi_state == 'radio':
                    wifi_intensity = get_amp_value(power_profile, 'wifi.active')
                if wifi_state == 'scan':
                    wifi_intensity = get_amp_value(power_profile, 'wifi.scan')
                energy_consumption = calculate_energy_usage(wifi_intensity, voltage, duration)
                wifi_results.append('{},{},{},wifi {},{}'.format(
                    wifi_start_time - app_start_time, wifi_end_time - app_start_time, duration,
                    wifi_state, energy_consumption))

            if camera_pattern.search(line):
                cam_state = camera_pattern.search(line).group(2)
                cam_state_time = convert_to_s(camera_pattern.search(line).group(1))
                cam_intensity = get_amp_value(power_profile, 'camera.avg')
                if cam_state == '+' and cam_state_time < app_end_time:
                    cam_activation = 1
                    if cam_state_time < app_start_time:
                        cam_start_time = app_start_time
                    else:
                        cam_start_time = cam_state_time
                elif cam_state == '-' and cam_state_time < app_end_time:
                    cam_activation = 0
                    if (cam_start_time < app_end_time) and (cam_state_time > app_end_time):
                        cam_end_time = app_end_time
                    else:
                        cam_end_time = convert_to_s(camera_pattern.search(line).group(1))
                    duration = cam_end_time - cam_start_time
                    energy_consumption = calculate_energy_usage(cam_intensity, voltage, duration)
                    cam_results.append('{},{},{},camera,{}'.format(
                        cam_start_time - app_start_time, cam_end_time - app_start_time, duration, energy_consumption))
            if cam_activation == 1 and current_time >= app_end_time:
                cam_end_time = app_end_time
                cam_activation = 0
                duration = cam_end_time - cam_start_time
                energy_consumption = calculate_energy_usage(cam_intensity, voltage, duration)
                cam_results.append('{},{},{},camera,{}'.format(
                    cam_start_time - app_start_time, cam_end_time - app_start_time, duration, energy_consumption))

            if flashlight_pattern.search(line):
                flashlight_state = flashlight_pattern.search(line).group(2)
                flashlight_state_time = convert_to_s(flashlight_pattern.search(line).group(1))
                flashlight_intensity = get_amp_value(power_profile, 'camera.flashlight')
                if flashlight_state == '+' and flashlight_state_time < app_end_time:
                    flashlight_activation = 1
                    if flashlight_state_time < app_start_time:
                        flashlight_start_time = app_start_time
                    else:
                        flashlight_start_time = flashlight_state_time
                elif flashlight_state == '-' and flashlight_state_time < app_end_time:
                    flashlight_activation = 0
                    if (flashlight_start_time < app_end_time) and (flashlight_state_time > app_end_time):
                        flashlight_end_time = app_end_time
                    else:
                        flashlight_end_time = convert_to_s(flashlight_pattern.search(line).group(1))
                    duration = flashlight_end_time - flashlight_start_time
                    energy_consumption = calculate_energy_usage(flashlight_intensity, voltage, duration)
                    flashlight_results.append('{},{},{},flashlight,{}'.format(
                        flashlight_start_time - app_start_time, flashlight_end_time - app_start_time,
                        duration, energy_consumption))
            if flashlight_activation == 1 and current_time >= app_end_time:
                flashlight_end_time = app_end_time
                flashlight_activation = 0
                duration = flashlight_end_time - flashlight_start_time
                energy_consumption = calculate_energy_usage(flashlight_intensity, voltage, duration)
                flashlight_results.append('{},{},{},flashlight,{}'.format(
                    flashlight_start_time - app_start_time, flashlight_end_time - app_start_time,
                    duration, energy_consumption))

            if gps_pattern.search(line):
                gps_state = gps_pattern.search(line).group(2)
                gps_state_time = convert_to_s(gps_pattern.search(line).group(1))
                gps_intensity = get_amp_value(power_profile, 'gps.on')
                if gps_state == '+' and gps_state_time < app_end_time:
                    gps_activation = 1
                    if gps_state_time < app_start_time:
                        gps_start_time = app_start_time
                    else:
                        gps_start_time = gps_state_time
                elif gps_state == '-' and gps_state_time < app_end_time:
                    gps_activation = 0
                    if (gps_start_time < app_end_time) and (gps_state_time > app_end_time):
                        gps_end_time = app_end_time
                    else:
                        gps_end_time = convert_to_s(gps_pattern.search(line).group(1))
                    duration = gps_end_time - gps_start_time
                    energy_consumption = calculate_energy_usage(gps_intensity, voltage, duration)
                    gps_results.append('{},{},{},gps,{}'.format(
                        gps_start_time - app_start_time, gps_end_time - app_start_time, duration, energy_consumption))
            if gps_activation == 1 and current_time >= app_end_time:
                gps_end_time = app_end_time
                gps_activation = 0
                duration = gps_end_time - gps_start_time
                energy_consumption = calculate_energy_usage(gps_intensity, voltage, duration)
                gps_results.append('{},{},{},gps,{}'.format(
                    gps_start_time - app_start_time, gps_end_time - app_start_time, duration, energy_consumption))

            if audio_pattern.search(line):
                audio_state = audio_pattern.search(line).group(2)
                audio_state_time = convert_to_s(audio_pattern.search(line).group(1))
                audio_intensity = get_amp_value(power_profile, 'dsp.audio')
                if audio_state == '+' and audio_state_time < app_end_time:
                    audio_activation = 1
                    if audio_state_time < app_start_time:
                        audio_start_time = app_start_time
                    else:
                        audio_start_time = audio_state_time
                elif audio_state == '-' and audio_state_time < app_end_time:
                    audio_activation = 0
                    if (audio_start_time < app_end_time) and (audio_state_time > app_end_time):
                        audio_end_time = app_end_time
                    else:
                        audio_end_time = convert_to_s(audio_pattern.search(line).group(1))
                    duration = audio_end_time - audio_start_time
                    energy_consumption = calculate_energy_usage(audio_intensity, voltage, duration)
                    audio_results.append('{},{},{},audio,{}'.format(
                        audio_start_time - app_start_time, audio_end_time - app_start_time,
                        duration, energy_consumption))
            if audio_activation == 1 and current_time >= app_end_time:
                audio_end_time = app_end_time
                audio_activation = 0
                duration = audio_end_time - audio_start_time
                energy_consumption = calculate_energy_usage(audio_intensity, voltage, duration)
                audio_results.append('{},{},{},audio,{}'.format(
                    audio_start_time - app_start_time, audio_end_time - app_start_time, duration, energy_consumption))

            if video_pattern.search(line):
                video_state = video_pattern.search(line).group(2)
                video_state_time = convert_to_s(video_pattern.search(line).group(1))
                video_intensity = get_amp_value(power_profile, 'dsp.video')
                if video_state == '+' and video_state_time < app_end_time:
                    video_activation = 1
                    if video_state_time < app_start_time:
                        video_start_time = app_start_time
                    else:
                        video_start_time = video_state_time
                elif video_state == '-' and video_state_time < app_end_time:
                    video_activation = 0
                    if (video_start_time < app_end_time) and (video_state_time > app_end_time):
                        video_end_time = app_end_time
                    else:
                        video_end_time = convert_to_s(video_pattern.search(line).group(1))
                    duration = video_end_time - video_start_time
                    energy_consumption = calculate_energy_usage(video_intensity, voltage, duration)
                    video_results.append('{},{},{},video,{}'.format(
                        video_start_time - app_start_time, video_end_time - app_start_time,
                        duration, energy_consumption))
            if video_activation == 1 and current_time >= app_end_time:
                video_end_time = app_end_time
                video_activation = 0
                duration = video_end_time - video_start_time
                energy_consumption = calculate_energy_usage(video_intensity, voltage, duration)
                video_results.append('{},{},{},video,{}'.format(
                    video_start_time - app_start_time, video_end_time - app_start_time, duration, energy_consumption))

            if bluetooth_pattern.search(line):
                bluetooth_state = bluetooth_pattern.search(line).group(2)
                bluetooth_state_time = convert_to_s(bluetooth_pattern.search(line).group(1))
                bluetooth_intensity = get_amp_value(power_profile, 'bluetooth.on')
                if bluetooth_state == '+' and bluetooth_state_time < app_end_time:
                    bluetooth_activation = 1
                    if bluetooth_state_time < app_start_time:
                        phone_scanning_start_time = app_start_time
                    else:
                        bluetooth_start_time = bluetooth_state_time
                elif bluetooth_state == '-' and bluetooth_state_time < app_end_time:
                    bluetooth_activation = 0
                    if (bluetooth_start_time < app_end_time) and (bluetooth_state_time > app_end_time):
                        bluetooth_end_time = app_end_time
                    else:
                        bluetooth_end_time = convert_to_s(bluetooth_pattern.search(line).group(1))
                    duration = bluetooth_end_time - bluetooth_start_time
                    energy_consumption = calculate_energy_usage(bluetooth_intensity, voltage, duration)
                    bluetooth_results.append('{},{},{},bluetooth,{}'.format(
                        bluetooth_start_time - app_start_time, bluetooth_end_time - app_start_time,
                        duration, energy_consumption))
            if bluetooth_activation == 1 and current_time >= app_end_time:
                bluetooth_end_time = app_end_time
                bluetooth_activation = 0
                duration = bluetooth_end_time - bluetooth_start_time
                energy_consumption = calculate_energy_usage(bluetooth_intensity, voltage, duration)
                bluetooth_results.append('{},{},{},bluetooth,{}'.format(
                    bluetooth_start_time - app_start_time, bluetooth_end_time - app_start_time,
                    duration, energy_consumption))

            if phone_scanning_pattern.search(line):
                phone_scanning_state = phone_scanning_pattern.search(line).group(2)
                phone_scanning_state_time = convert_to_s(phone_scanning_pattern.search(line).group(1))
                phone_scanning_intensity = get_amp_value(power_profile, 'radio.scanning')
                if phone_scanning_state == '+' and phone_scanning_state_time < app_end_time:
                    phone_scanning_activation = 1
                    if phone_scanning_state_time < app_start_time:
                        phone_scanning_start_time = app_start_time
                    else:
                        phone_scanning_start_time = phone_scanning_state_time
                elif phone_scanning_state == '-' and phone_scanning_state_time < app_end_time:
                    phone_scanning_activation = 0
                    if (phone_scanning_start_time < app_end_time) and (phone_scanning_state_time > app_end_time):
                        phone_scanning_end_time = app_end_time
                    else:
                        phone_scanning_end_time = convert_to_s(phone_scanning_pattern.search(line).group(1))
                    duration = phone_scanning_end_time - phone_scanning_start_time
                    energy_consumption = calculate_energy_usage(phone_scanning_intensity, voltage, duration)
                    phone_scanning_results.append('{},{},{},phone scanning,{}'.format(
                        phone_scanning_start_time - app_start_time, phone_scanning_end_time - app_start_time,
                        duration, energy_consumption))
            if phone_scanning_activation == 1 and current_time >= app_end_time:
                phone_scanning_end_time = app_end_time
                phone_scanning_activation = 0
                duration = phone_scanning_end_time - phone_scanning_start_time
                energy_consumption = calculate_energy_usage(phone_scanning_intensity, voltage, duration)
                phone_scanning_results.append('{},{},{},phone scanning,{}'.format(
                    phone_scanning_start_time - app_start_time, phone_scanning_end_time - app_start_time,
                    duration, energy_consumption))

    all_results.extend(screen_results + wifi_results + cam_results + flashlight_results +
                       gps_results + audio_results + video_results + bluetooth_results + phone_scanning_results)
    #for results in all_results:
        #print results
    return all_results


def get_voltage(line):
    """ Obtain voltage value """
    pattern = re.compile('volt=(\d+)')
    match = pattern.search(line)
    return float(match.group(1)) / 1000.0


def get_screen_intensity(brightness, power_profile):
    intensity_range = get_amp_value(power_profile, 'screen.full') - get_amp_value(power_profile, 'screen.on')
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
    return screen_intensity


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


def parse_systrace(app, systrace_file, logcat, batterystats, power_profile, core_amount):
    """ Parse systrace file and calculate results """
    with open(batterystats, 'r') as bs:
        voltage_pattern = re.compile('(0|\+\d.*ms).*volt=(\d+)')
        voltage = float(re.findall(voltage_pattern, bs.read())[0][1]) / 1000.0

    with open(systrace_file, 'r') as sys:
        f = sys.read()
        pattern = re.compile('(?:<.{3,4}>-\d{1,4}|kworker.+-\d{3}).*\s(\d+\.\d+): (cpu_.*): state=(.*) cpu_id=(\d)')
        #matches = pattern.finditer(f)
        unix_time_pattern = re.compile('(\d+\.\d+):\stracing_mark_write:\strace_event_clock_sync:\srealtime_ts=(\d+)')
        logcat_time = parse_logcat(app, logcat)
        systrace_time = float(unix_time_pattern.search(f).group(2))
        start_time = (logcat_time[0] - systrace_time) / 1000 + float(unix_time_pattern.search(f).group(1))
        end_time = (logcat_time[1] - systrace_time) / 1000 + float(unix_time_pattern.search(f).group(1))
        cpu_id_list = []
        results = []

        """
        for match in matches:
            current_time = float(match.group(1))
            current_cpu_id = int(match.group(4))
            if current_time > end_time or current_time < start_time:
                pass
            else:
                if (current_cpu_id not in cpu_id_list) and (current_time <= end_time):
                    cpu_id_list.append(int(current_cpu_id))
                elif (current_cpu_id in cpu_id_list) and (current_time <= end_time):
                    continue
                elif current_time > end_time:
                    break
        """
        for i in range(0, core_amount):
            cpu_id_list.append(i)

        cpu_id_list.sort()
        for cpu_id in cpu_id_list:
            matches = pattern.finditer(f)
            found_first_match = 0
            for match in matches:
                current_time = float(match.group(1))
                current_category = str(match.group(2))
                current_state = str(match.group(3))
                current_cpu_id = int(match.group(4))
                if current_time > end_time or current_time < start_time:
                    pass
                else:
                    if (found_first_match == 0) and (current_cpu_id == cpu_id):
                        if current_time > start_time:
                            time = start_time
                            duration = current_time - time
                            category = 'cpu_idle'
                            cpu_intensity = get_amp_value(power_profile, 'cpu.idle')
                            energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                            results.append('{},{},{},core {} {} start,{}'.format
                                           (time - start_time, current_time - start_time,
                                            duration, cpu_id, category, energy_consumption))
                        else:
                            pass
                        time = current_time
                        category = current_category
                        state = current_state
                        cpu_id = current_cpu_id
                        found_first_match = 1
                    elif found_first_match == 1 and (current_cpu_id == cpu_id):
                        if (current_category == category) and (current_state == state):
                            pass
                        elif current_category == category == 'cpu_idle':
                            pass
                        elif category == 'cpu_idle' and current_category == 'cpu_frequency':
                            duration = current_time - time
                            cpu_intensity = get_amp_value(power_profile, 'cpu.idle')
                            energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                            results.append('{},{},{},core {} {},{}'.format
                                           (time - start_time, current_time - start_time,
                                            duration, cpu_id, category, energy_consumption))
                            time = current_time
                            category = current_category
                            state = current_state
                        elif (current_category == category == 'cpu_frequency') and (current_state == state):
                            pass
                        elif (current_category == category == 'cpu_frequency') and (current_state != state):
                            duration = current_time - time
                            cpu_intensity = get_amp_value(power_profile, category, state)
                            energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                            results.append('{},{},{},core {} {},{}'.format
                                           (time - start_time, current_time - start_time,
                                            duration, cpu_id, category, energy_consumption))
                            time = current_time
                            category = current_category
                            state = current_state
                        elif current_category != category:
                            duration = current_time - time
                            cpu_intensity = get_amp_value(power_profile, category, state)
                            energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                            results.append('{},{},{},core {} {},{}'.format
                                           (time - start_time, current_time - start_time,
                                            duration, cpu_id, category, energy_consumption))
                            time = current_time
                            category = current_category
                            state = current_state
                if current_time >= end_time and current_category == category \
                        and current_state == state and current_cpu_id == cpu_id:
                    duration = end_time - time
                    if current_category == 'cpu_idle':
                        cpu_intensity = get_amp_value(power_profile, 'cpu.idle')
                    else:
                        cpu_intensity = get_amp_value(power_profile, category, state)
                    energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                    results.append('{},{},{},core {} {},{}'.format
                                   (time - start_time, end_time - start_time,
                                    duration, cpu_id, category, energy_consumption))
                    break
                if found_first_match == 0 and current_time >= end_time:
                    duration = end_time - start_time
                    category = 'cpu_idle'
                    cpu_intensity = get_amp_value(power_profile, 'cpu.idle')
                    energy_consumption = calculate_energy_usage(cpu_intensity, voltage, duration)
                    results.append('{},{},{},core {} {},{}'.format
                                   (start_time - start_time, end_time - start_time,
                                    duration, cpu_id, category, energy_consumption))
                    break


    return results
    """
    import csv
    with open('results.csv', 'w') as f:
        writer = csv.writer(f, delimiter="\n")
        writer.writerow(['Start time,End time,Duration (seconds),Component,Energy Consumption (Joule)'])
        writer.writerow(results)
    """
''' Logcat '''


def parse_logcat(app, logcat_file):
    """ Obtain app start and end times from logcat """
    with open(logcat_file, 'r') as f:
        logcat = f.read()
        app_start_pattern = re.compile(
            '(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).(\d{3}).*ActivityManager:\sSTART\s.*(%s)' % app)
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

# Test  net.sourceforge.opencamera   test.blackscreen
#parse_systrace('test.blackscreen', 'Test/systrace.html', 'Test/logcat.txt', 'Test/batterystats_history.txt', 'Test/power_profile.xml', 4)
#parse_batterystats('net.sourceforge.opencamera', 'Test/batterystats_history.txt', 'Test/power_profile.xml')