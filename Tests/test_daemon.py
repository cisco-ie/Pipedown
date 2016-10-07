import unittest
import os
import mock
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
        open(os.path.join(self.location, '../router_connected.log'), 'w').close()

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
        self.assertItemsEqual(sections, ['BGP', 'IS-IS'])

    def test_grab_sections_no_section(self):
        copyfile(
            os.path.join(self.location,'Config/no_section.config'),
            os.path.join(self.location,'../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            sections = monitor_daemon.grab_sections()
        self.assertRaisesRegexp(cm.exception.code, 'File contains no section headers')

    def test_grab_sections_misssing_object(self):
        copyfile(
            os.path.join(self.location,'Config/no_protocol.config'),
            os.path.join(self.location,'../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            monitor_daemon.monitor('BGP')
        with open(os.path.join(self.location,'../router_connected.log')) as debug_log:
            log = debug_log.readlines()[0]
            self.assertRegexpMatches(log, 'Config file error:')
        self.assertEqual(cm.exception.code, 1)

    @mock.patch('monitor_daemon.Link.health', side_effect = [True])
    def test_bad_as_format(self, mock_health):
        copyfile(
            os.path.join(self.location,'Config/bad_as.config'),
            os.path.join(self.location,'../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            monitor_daemon.monitor('BGP')
        with open(os.path.join(self.location,'../router_connected.log')) as debug_log:
            log = debug_log.readlines()[2]
            self.assertRegexpMatches(log, 'Flush AS is in the wrong format for')
        self.assertEqual(cm.exception.code, 1)


    @mock.patch('monitor_daemon.Link.health', side_effect = [False, True])
    @mock.patch('monitor_daemon.Flush_BGP.get_bgp_neighbors', return_value = 'Testing')
    def test_link_good_log(self, mock_health, mock_flush):
        copyfile(
            os.path.join(self.location,'Config/monitor_good.config'),
            os.path.join(self.location,'../monitor.config')
        )
        monitor_daemon.monitor('BGP')
        with open(os.path.join(self.location,'../router_connected.log')) as debug_log:
            log = debug_log.readlines()
            good_log = log[1]
            bad_log = log[3]
        self.assertRegexpMatches(good_log, 'Link is good')
        self.assertRegexpMatches(bad_log, 'Link is down')

    def tearDown(self):
        if os.path.isfile(os.path.join(self.location,'../monitortest.config')):
            move(
                os.path.join(self.location,'../monitortest.config'),
                os.path.join(self.location,'../monitor.config')
            )

if __name__ == '__main__':
    unittest.main()
