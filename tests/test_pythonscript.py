import unittest
import tempfile
from ExperimentRunner.PythonScript import PythonScript


class FakeDevice(object):
    def __init__(self, device_id):
        self.id = device_id

    def logcat_regex(self, regex):
        return


class TestPythonScript(unittest.TestCase):
    def setUp(self):
        self.device = FakeDevice('fake_id')
        self.current_activity = 'fake_activity'

    def test_timeout(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write('\n'.join(['from time import sleep',
                                  'def main(device_id, current_activity):\n',
                                  '    sleep(1)\n'])
                       )
            temp.flush()
            self.assertEqual(PythonScript(temp.name, timeout=100).run(self.device, self.current_activity), 'timeout')

    def test_logcat(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write('\n'.join(['from time import sleep',
                                  'def main(device_id, current_activity):\n',
                                  '    sleep(1)\n'])
                       )
            temp.flush()
            self.assertEqual(PythonScript(temp.name, logcat_regex='').run(self.device, self.current_activity), 'logcat')


if __name__ == '__main__':
    unittest.main()
