from Device import Device


class Devices:
    def __init__(self, devices):
        self._device_registry = devices
        self._devices = [Device(name, device) for name, device in devices.items()]

    def __iter__(self):
        return iter(self._devices)

    def names(self):
        return self._device_registry.keys()

    def ids(self):
        return self._device_registry.values()

    def get_id(self, name):
        return self._device_registry[name]

    def get_name(self, device_id):
        return (k for k, v in self._device_registry if v == device_id)
