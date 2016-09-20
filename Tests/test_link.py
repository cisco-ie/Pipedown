import unittest
import os
from mock import MagicMock, patch
from Monitor.link import Link
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient


class LinkTestCase(unittest.TestCase, object):

    @classmethod
    def setUpClass(cls):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.test_link = Link('10.1.1.1', '10.1.1.2', cls.grpc_client)

    def test_link_object(self):
        lnk = Link('10.1.1.1', '10.1.1.2', self.grpc_client, 10, 20, 5, 5)
        self.assertIsInstance(lnk, Link)
        self.assertEqual(lnk.bw_thres, 10)
        self.assertEqual(lnk.jitter_thres, 20)
        self.assertEqual(lnk.pkt_loss, 5)
        self.assertEqual(lnk.interval, 5)

    def test_health(self):
        protocol = 'ISIS'
        self.test_link.check_routing = MagicMock(return_value=True)
        self.test_link.run_iperf = MagicMock(return_value=True)
        result = self.test_link.health(protocol)
        self.assertTrue(result)

        self.test_link.check_routing = MagicMock(return_value=False)
        self.test_link.run_iperf = MagicMock(return_value=True)
        result = self.test_link.health(protocol)
        self.assertFalse(result)
        self.test_link.run_iperf.assert_not_called()

        self.test_link.check_routing = MagicMock(return_value=True)
        self.test_link.run_iperf = MagicMock(return_value=False)
        result = self.test_link.health(protocol)
        self.assertFalse(result)

        self.test_link.check_routing = MagicMock(return_value=False)
        self.test_link.run_iperf = MagicMock(return_value=False)
        result = self.test_link.health(protocol)
        self.assertFalse(result)

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_routing(self, mock_get):
        location = os.path.dirname(os.path.realpath(__file__))
        new_filepath = os.path.join(location, 'Examples/protocol-active.txt')
        with open(new_filepath) as f:
            output_good = f.read()
        mock_get.return_value = output_good
        result = self.test_link.check_routing('isis')
        self.assertFalse(result)
        result = self.test_link.check_routing('bgp')
        self.assertTrue(result)
