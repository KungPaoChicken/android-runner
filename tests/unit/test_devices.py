import pytest
from ExperimentRunner.Adb import ADB, AdbError
from ExperimentRunner.Device import Device
from ExperimentRunner.Devices import Devices

class TestDevice(object):

    def empty_test(self):
        assert True
