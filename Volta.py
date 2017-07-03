import Adb


class Measurement(object):
    def __init__(self):
        pass

    def start_measurement(self):
        print('Measurement started')

    def stop_measurement(self):
        print('Measurement stopped')

    def get_results(self):
        pass


class Volta(Measurement):
    def start_measurement(self):
        super(Volta, self).start_measurement()
        Adb.shell('dumpsys batterystats --reset')
        pass

    def stop_measurement(self):
        super(Volta, self).stop_measurement()
        pass

    def get_results(self):
        return Adb.shell('dumpsys batterystats')