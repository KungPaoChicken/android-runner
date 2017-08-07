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
        self.file = tempfile.NamedTemporaryFile()
        self.file.write('\n'.join(['from time import sleep',
                                   'def main(device_id, current_activity):\n',
                                   '    sleep(1)\n'])
                        )
        self.file.flush()

    def tearDown(self):
        self.file.close()

    def test_normal(self):
        self.assertEqual(
            PythonScript(self.file.name).run(self.device, self.current_activity),
            'script')

    def test_timeout(self):
        self.assertEqual(
            PythonScript(self.file.name, timeout=100).run(self.device, self.current_activity),
            'timeout')

    def test_logcat(self):
        self.assertEqual(
            PythonScript(self.file.name, logcat_regex='').run(self.device, self.current_activity),
            'logcat')


if __name__ == '__main__':
    unittest.main()
