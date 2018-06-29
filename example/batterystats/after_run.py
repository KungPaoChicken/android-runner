def main(device, *args, **kwargs):
    """ Prevent the device from sleeping """
    device.shell('input tap 600 1000')
    pass
