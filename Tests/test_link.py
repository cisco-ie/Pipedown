import unittest
import os
from mock import patch
from Monitor.link import Link
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient


def read_file(filepath):
    location = os.path.dirname(os.path.realpath(__file__))
    new_filepath = os.path.join(location, filepath)
    with open(new_filepath) as f:
        return f.read()

class LinkTestCase(unittest.TestCase, object):

    @classmethod
    def setUpClass(cls):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.link = Link('10.1.1.1', '10.1.1.2', cls.grpc_client)

    def link_object(self):
        lnk = Link('10.1.1.1', '10.1.1.2', self.grpc_client, 10, 20, 5, 5)
        self.assertIsInstance(lnk, Link)
        self.assertEqual(lnk.bw_thres, 10)
        self.assertEqual(lnk.jitter_thres, 20)
        self.assertEqual(lnk.pkt_loss, 5)
        self.assertEqual(lnk.interval, 5)

    @patch('Monitor.link.subprocess.Popen.communicate')
    def test_iperf(self, mock_communicate):
        out = read_file('Examples/iPerf/good.txt')
        mock_communicate.return_value = [out, '']
        self.assertFalse(self.link.run_iperf())

        out = read_file('Examples/iPerf/high-bandwidth.txt')
        mock_communicate.return_value = [out, '']
        self.assertTrue(self.link.run_iperf())

        err = 'read failed: Connection refused\n'
        mock_communicate.return_value = ['', err]
        self.assertTrue(self.link.run_iperf)

    @patch('Monitor.link.Link.check_routing')
    @patch('Monitor.link.Link.run_iperf')
    def test_health(self, mock_iperf, mock_routing):
        protocol = 'ISIS'
        mock_routing.return_value = False
        self.assertFalse(self.link.health(protocol))
        mock_iperf.assert_not_called()

        mock_routing.return_value = True
        mock_iperf.return_value = True
        self.assertTrue(self.link.health(protocol))

        mock_routing.return_value = True
        mock_iperf.return_value = False
        self.assertFalse(self.link.health(protocol))

    def test_check_protocol(self):
        self.assertFalse(self.link._check_protocol(''))
        self.assertFalse(self.link._check_protocol('\n'))
        self.assertFalse(self.link._check_protocol('bad'))
        self.assertTrue(self.link._check_protocol('bgp'))
        self.assertTrue(self.link._check_protocol('isis'))
        self.assertTrue(self.link._check_protocol('isis summary null'))

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_routing(self, mock_get):
        self.link.check_routing('bad')
        mock_get.assert_not_called()

        output_good = read_file('Examples/protocol-active.txt')
        mock_get.return_value = output_good
        self.assertFalse(self.link.check_routing('isis'))
        self.assertTrue(self.link.check_routing('bgp'))

        output_bad = read_file('Examples/non-active.txt')
        mock_get.return_value = output_bad
        self.assertTrue(self.link.check_routing('isis'))

        output_bad = read_file('Examples/bad-protocol.txt')
        mock_get.return_value = output_bad
        self.assertTrue(self.link.check_routing('isis'))





