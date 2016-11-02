import unittest
import os
from shutil import copyfile, move
import mock

import monitor_daemon
import testmixin


class DaemonTestCase(testmixin.TestMixIn, object):
    def setUp(self):
        self.location = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile(os.path.join(self.location, '../monitor.config')):
            move(
                os.path.join(self.location, '../monitor.config'),
                os.path.join(self.location, '../monitortest.config')
            )
        open(os.path.join(self.location, '../router_connected.log'), 'w').close()

    def test_grab_sections_good(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/monitor_good.config'),
            os.path.join(self.location, '../monitor.config')
        )
        sections = monitor_daemon.grab_sections()
        self.assertEqual(sections, ['BGP'])

    def test_grab_sections_multiplesections(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/multiple_sections.config'),
            os.path.join(self.location, '../monitor.config')
        )
        sections = monitor_daemon.grab_sections()
        self.assertItemsEqual(sections, ['BGP', 'IS-IS'])

    def test_grab_sections_no_section(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/no_section.config'),
            os.path.join(self.location, '../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            monitor_daemon.grab_sections()
        self.assertRaisesRegexp(cm.exception.code, 'File contains no section headers')

    def test_grab_sections_missing_object(self):
        open('router_connected.log', 'w').close()
        copyfile(
            os.path.join(self.location, 'Examples/Config/no_protocol.config'),
            os.path.join(self.location, '../monitor.config')
        )
        lock = None
        health = None
        with self.assertRaises(SystemExit) as cm:
            monitor_daemon.monitor('BGP', lock, health)
        with open('router_connected.log') as debug_log:
            log = debug_log.readlines()[0]
            self.assertRegexpMatches(log, 'Config file error:')
        self.assertEqual(cm.exception.code, 1)

    def tearDown(self):
        if os.path.isfile(os.path.join(self.location, '../monitortest.config')):
            move(
                os.path.join(self.location, '../monitortest.config'),
                os.path.join(self.location, '../monitor.config')
            )

if __name__ == '__main__':
    unittest.main()
