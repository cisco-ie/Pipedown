import unittest
import os
from shutil import copyfile, move
import sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import monitor_daemon

class DaemonTestCase(unittest.TestCase):
    def setUp(self):
        self.location = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile(os.path.join(self.location,'../monitor.config')):
            move(
                os.path.join(self.location,'../monitor.config'),
                os.path.join(self.location,'../monitortest.config')
            )

    def test_grab_sections_good(self):
        copyfile(
            os.path.join(self.location,'Config/monitor_good.config'),
            os.path.join(self.location,'../monitor.config')
        )
        sections = monitor_daemon.grab_sections()
        self.assertEqual(sections, ['BGP'])

    def test_grab_sections_multiplesections(self):
        copyfile(
            os.path.join(self.location,'Config/multiple_sections.config'),
            os.path.join(self.location,'../monitor.config')
        )
        sections = monitor_daemon.grab_sections()
        self.assertEqual(sections, ['BGP', 'IS-IS'])

    def test_grab_sections_no_section(self):
        copyfile(
            os.path.join(self.location,'Config/no_sections.config'),
            os.path.join(self.location,'../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            sections = monitor_daemon.grab_sections()
        self.assertEqual(cm.exception.code, 1)

    def tearDown(self):
        if os.path.isfile(os.path.join(self.location,'../monitortest.config')):
            move(
                os.path.join(self.location,'../monitortest.config'),
                os.path.join(self.location,'../monitor.config')
            )

if __name__ == '__main__':
    unittest.main()
