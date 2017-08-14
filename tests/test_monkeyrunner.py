import unittest
import tempfile
from ExperimentRunner.MonkeyRunner import MonkeyRunner
from ExperimentRunner.util import FileNotFoundError


class FakeDevice(object):
    def __init__(self, device_id):
        self.id = device_id

    def logcat_regex(self, regex):
        return


class TestMonkeyRunner(unittest.TestCase):
    def setUp(self):
        self.monkey = '/opt/platform-tools/bin/monkeyrunner'
        self.device = FakeDevice('fake_id')
        self.current_activity = 'fake_activity'
        self.file = tempfile.NamedTemporaryFile()
        self.file.write('\n'.join(['from time import sleep',
                                   'sleep(1)\n'])
                        )
        self.file.flush()

    def tearDown(self):
        self.file.close()

    def test_monkey(self):
        self.assertEqual(MonkeyRunner(self.file.name, '', monkeyrunner_path=self.monkey)
                         .run(self.device, self.current_activity), 'script')

    def test_timeout(self):
        self.assertEqual(MonkeyRunner(self.file.name, '', timeout=100, monkeyrunner_path=self.monkey)
                         .run(self.device, self.current_activity), 'timeout')

    def test_logcat(self):
        self.assertEqual(MonkeyRunner(self.file.name, '', logcat_regex='', monkeyrunner_path=self.monkey)
                         .run(self.device, self.current_activity), 'logcat')


if __name__ == '__main__':
    unittest.main()
