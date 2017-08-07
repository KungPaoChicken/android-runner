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

    def test_monkeynotfound(self):
        with self.assertRaises(FileNotFoundError):
            with tempfile.NamedTemporaryFile() as temp:
                MonkeyRunner(temp.name, '', monkeyrunner_path='fake_monkeyrunner')

    def test_timeout(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write('\n'.join(['from time import sleep',
                                  'sleep(1)\n'])
                       )
            temp.flush()
            self.assertEqual(MonkeyRunner(temp.name, '', timeout=100, monkeyrunner_path=self.monkey)
                             .run(self.device, self.current_activity), 'timeout')

    def test_logcat(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write('\n'.join(['from time import sleep',
                                  '    sleep(1)\n'])
                       )
            temp.flush()
            self.assertEqual(MonkeyRunner(temp.name, '', logcat_regex='', monkeyrunner_path=self.monkey)
                             .run(self.device, self.current_activity), 'logcat')


if __name__ == '__main__':
    unittest.main()
