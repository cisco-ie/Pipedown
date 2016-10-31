import unittest
import os
from shutil import copyfile, move
import mock
from pipedown import monitor_daemon


class DaemonTestCase(unittest.TestCase):
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

    def test_grab_sections_misssing_object(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/no_protocol.config'),
            os.path.join(self.location, '../monitor.config')
        )
        with self.assertRaises(SystemExit) as cm:
            monitor_daemon.daemon()
        with open(os.path.join(self.location, '../router_connected.log')) as debug_log:
            log = debug_log.readlines()[0]
            self.assertRegexpMatches(log, 'Config file error:')
        self.assertEqual(cm.exception.code, 1)

    @mock.patch('pipedown.monitor_daemon.Link.health', side_effect=[False, True])
    @mock.patch('pipedown.monitor_daemon.response')
    def test_link_good_log(self, mock_flush, mock_health):
        copyfile(
            os.path.join(self.location, 'Examples/Config/monitor_good.config'),
            os.path.join(self.location, '../monitor.config')
        )
        mock_flush.returnvalue = None
        mock_flush.get_bgp_neighbors.returnvalue = 'Testing'

        monitor_daemon.daemon()
        with open(os.path.join(self.location, '../router_connected.log')) as debug_log:
            log = debug_log.readlines()
            good_log = log[1]
            bad_log = log[3]
        self.assertRegexpMatches(good_log, 'Link is good')
        self.assertRegexpMatches(bad_log, 'Link is down')

    def tearDown(self):
        if os.path.isfile(os.path.join(self.location, '../monitortest.config')):
            move(
                os.path.join(self.location, '../monitortest.config'),
                os.path.join(self.location, '../monitor.config')
            )

if __name__ == '__main__':
    unittest.main()
