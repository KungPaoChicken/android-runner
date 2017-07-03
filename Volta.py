import Adb


class Measurement(object):
    def __init__(self):
        pass

    def start_measurement(self, device_id):
        print('Measurement started')

    def stop_measurement(self, device_id):
        print('Measurement stopped')

    def get_results(self, device_id):
        pass


class Volta(Measurement):
    def start_measurement(self, device_id):
        super(Volta, self).start_measurement(device_id)
        Adb.shell(device_id, 'dumpsys batterystats --reset')

    def stop_measurement(self, device_id):
        super(Volta, self).stop_measurement(device_id)

    def get_results(self, device_id):
        return Adb.shell(device_id, 'dumpsys batterystats')
