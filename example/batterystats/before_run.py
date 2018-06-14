def main(device, *args, **kwargs):
    device.shell('dumpsys batterystats --reset')
    device.shell('logcat -c')
    print 'Batterystats cleared'
    print 'Logcat cleared'
