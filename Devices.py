from Device import Device
from util import load_json, ConfigError


class Devices:
    def __init__(self, names):
        mapping_file = load_json('devices.json')
        self._device_map = {n: mapping_file.get(n, None) for n in names}
        for name, device_id in self._device_map:
            if not device_id:
                raise ConfigError(name)
        self._devices = [Device(name, device_id) for name, device_id in self._device_map.items()]

    def __iter__(self):
        return iter(self._devices)

    def names(self):
        return self._device_map.keys()

    def ids(self):
        return self._device_map.values()

    def get_id(self, name):
        return self._device_map[name]

    def get_name(self, device_id):
        return (k for k, v in self._device_map if v == device_id)
