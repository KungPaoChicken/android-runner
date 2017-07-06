import Adb


class Measurement(object):
    @staticmethod
    def get_dependencies():
        return []

    def __init__(self, basedir, config):
        self.basedir = basedir

    def load(self, device_id):
        pass

    def start_measurement(self, device_id):
        # print('Measurement started')
        pass

    def stop_measurement(self, device_id):
        # print('Measurement stopped')
        pass

    def get_results(self, device_id):
        pass

    def unload(self, device_id):
        pass


class Volta(Measurement):
    def __init__(self, basedir, config):
        super(Volta, self).__init__(basedir, config)
        # print('Volta initialized')

    def start_measurement(self, device_id):
        super(Volta, self).start_measurement(device_id)
        Adb.shell(device_id, 'dumpsys batterystats --reset')
        Adb.unplug(device_id)  # reset plugs the device back in

    def stop_measurement(self, device_id):
        super(Volta, self).stop_measurement(device_id)

    def get_results(self, device_id):
        return Adb.shell(device_id, 'dumpsys batterystats')
