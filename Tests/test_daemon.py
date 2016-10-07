import unittest
import os
from shutil import copyfile, move
import sys
sys.path.append("..")
import monitor_daemon

class DaemonTestCase(unittest.TestCase, object):
    def setUp(self):
        if os.path.isfile('../../monitor.config'):
            os.move(
                '../../monitor.config',
                '../../monitortest.config'
            )

    def test_grab_sections_good(self):
        copyfile(
            'Config/monitor_good.config',
            '../../monitor.config'
        )
        sections = monitor_daemon.grab_sections()
        self.assertEqual(sections, ['BGP'])

if __name__ == '__main__':
    unittest.main()
