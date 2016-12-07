import unittest
import os
from shutil import copyfile, move
from mock import patch
import monitor_daemon
from Tools.exceptions import GRPCError
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient


class MyConfigTestCase(unittest.TestCase, object):
    def setUp(self):
        self.location = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(self.location, '../monitor.config')
        if os.path.isfile(self.config_path):
            move(
                self.config_path,
                os.path.join(self.location, '../monitortest.config')
            )
        open(os.path.join(self.location, '../router_connected.log'), 'w').close()

    def test_grab_sections_good(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/monitor_good.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        self.assertEqual(config.__dict__.keys(), ['BGP'])

    def test_grab_sections_multiplesections(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/multiple_sections.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        self.assertItemsEqual(config.__dict__.keys(), ['BGP', 'ISIS'])

    def test_grab_sections_no_section(self):
        copyfile(
            os.path.join(self.location, 'Examples/Config/no_section.config'),
            self.config_path
        )
        with self.assertRaises(ValueError):
            monitor_daemon.MyConfig(self.config_path)

    def test_grab_sections_missing_object(self):
        open('router_connected.log', 'w').close()
        copyfile(
            os.path.join(self.location, 'Examples/Config/no_protocol.config'),
            self.config_path
        )
        with self.assertRaises(KeyError):
            monitor_daemon.MyConfig(self.config_path)

    def tearDown(self):
        if os.path.isfile(os.path.join(self.location, '../monitortest.config')):
            move(
                os.path.join(self.location, '../monitortest.config'),
                self.config_path
            )


class MonitorDaemonTestCase(unittest.TestCase, object):
    @classmethod
    def setUpClass(cls):
        cls.location = os.path.dirname(os.path.realpath(__file__))
        cls.config_path = os.path.join(cls.location, '../monitor.config')
        if os.path.isfile(cls.config_path):
            move(
                cls.config_path,
                os.path.join(cls.location, '../monitortest.config')
        )
        copyfile(
            os.path.join(cls.location, 'Examples/Config/monitor_good.config'),
            cls.config_path
        )
        cls.config = monitor_daemon.MyConfig(cls.config_path)
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.sec_config = cls.config.__dict__['BGP']

    @patch('monitor_daemon.LOGGER')
    @patch('monitor_daemon.link_check')
    def monitor_grpc_error(self, mock_check, mock_logger):
        import pdb
        pdb.set_trace()
        mock_check.side_effect = GRPCError(
            err="{'cisco-grpc': {'errors':{'error': {'error-message': 'There was an error'}}}}"
        )
        lock = False
        health_dict = {}
        monitor_daemon.monitor('BGP', lock, self.config, health_dict)
        self.assertTrue(mock_logger.critical.calledm)

    @patch('monitor_daemon.LOGGER')
    @patch('Response.response.model_selection')
    def test_grpc_merge_errors(self, mock_grpc, mock_logger):
        mock_grpc.side_effect = GRPCError(
            err="{'cisco-grpc': {'errors':{'error': {'error-message': 'There was an error'}}}}"
        )
        result = monitor_daemon.link_response(self.grpc_client, self.sec_config, True)
        self.assertFalse(result)
        mock_grpc.assert_called_with(
            self.sec_config.yang,
            self.grpc_client,
            self.sec_config.flush_bgp_as,
            self.sec_config.drop_policy_name
        )
        self.assertTrue(mock_logger.error.called)

        result = monitor_daemon.link_response(self.grpc_client, self.sec_config, False)
        mock_grpc.assert_called_with(
            self.sec_config.yang,
            self.grpc_client,
            self.sec_config.flush_bgp_as,
            self.sec_config.pass_policy_name
        )
        self.assertTrue(result)
        self.assertTrue(mock_logger.error.called)

    @patch('monitor_daemon.health')
    def test_link_check_grpc_errors(self, mock_grpc):
        mock_grpc.side_effect = GRPCError(
            err="{'cisco-grpc': {'errors':{'error': {'error-message': 'There was an error'}}}}"
        )
        with self.assertRaises(GRPCError):
             monitor_daemon.link_check(self.sec_config, self.grpc_client)

    @patch('monitor_daemon.Link')
    @patch('monitor_daemon.health')
    def test_link_check_link_error(self, mock_link, mock_response):
        mock_link.side_effect = TypeError()
        with self.assertRaises(TypeError):
            result = monitor_daemon.link_check(self.sec_config, self.grpc_client)
            self.assertFalse(result)
            mock_response.assert_not_called()

    @patch('monitor_daemon.response.email_alert')
    @patch('monitor_daemon.response.text_alert')
    def test_alert_response_email(self, mock_text, mock_email):
        #Check if hostname is missing from the file
        copyfile(
            os.path.join(self.location, 'Examples/Config/email_alert.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        sec_config = config.__dict__['BGP']
        result = monitor_daemon.alert_response(sec_config, 'BGP', 'up')
        self.assertTrue(result)
        mock_text.assert_not_called()
        mock_email.assert_called_with(
            'pipedown@cisco.com',
            "'BGP' link is up on 'rtr1'"
            )

    @patch('monitor_daemon.response.email_alert')
    @patch('monitor_daemon.response.text_alert')
    def test_alert_response_text(self, mock_text, mock_email):
        copyfile(
            os.path.join(self.location, 'Examples/Config/text_alert.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        sec_config = config.__dict__['BGP']
        result = monitor_daemon.alert_response(sec_config, 'BGP', 'up')
        self.assertTrue(result)
        mock_email.assert_not_called()
        mock_text.assert_called_with(
            '+14087784819',
            "'BGP' link is up on 'rtr1'"
        )

    @patch('monitor_daemon.response.email_alert')
    @patch('monitor_daemon.response.text_alert')
    def test_alert_response_miss_host(self, mock_text, mock_email):
        copyfile(
            os.path.join(self.location, 'Examples/Config/missing_hostname.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        sec_config = config.__dict__['BGP']
        result = monitor_daemon.alert_response(sec_config, 'BGP', 'up')
        self.assertTrue(result)
        mock_email.assert_called_with(
            'pipedown@cisco.com',
            "'BGP' link is up on '(missing hostname)'"
        )

    @patch('monitor_daemon.response.email_alert')
    @patch('monitor_daemon.response.text_alert')
    def test_alert_response_both(self, mock_text, mock_email):
        copyfile(
            os.path.join(self.location, 'Examples/Config/both_alert.config'),
            self.config_path
        )
        config = monitor_daemon.MyConfig(self.config_path)
        sec_config = config.__dict__['BGP']
        result = monitor_daemon.alert_response(sec_config, 'BGP', 'down')
        self.assertTrue(result)
        mock_text.assert_called_with(
            '+14087784819',
            "'BGP' link is down on 'rtr1'"
        )
        mock_email.assert_called_with(
            'pipedown@cisco.com',
            "'BGP' link is down on 'rtr1'"
            )

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(os.path.join(cls.location, '../monitortest.config')):
            move(
                os.path.join(cls.location, '../monitortest.config'),
                cls.config_path
            )


if __name__ == '__main__':
    unittest.main()
