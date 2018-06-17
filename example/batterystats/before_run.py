def main(device, *args, **kwargs):
    device.shell('dumpsys batterystats --reset')
    print 'Batterystats cleared'
    device.shell('logcat -c')
    print 'Logcat cleared'
