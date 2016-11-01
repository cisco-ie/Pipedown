import unittest
import os
from mock import patch, Mock
from Monitor.link import Link
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient


def read_file(filename):
    """Takes a filename and concatenates it with the location of this file.
    :param filename: The filename
    :param type: str
    """
    location = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(location, filename)) as f:
        return f.read()

class LinkTestCase(unittest.TestCase, object):
    @staticmethod
    def read_file(filepath):
        location = os.path.dirname(os.path.realpath(__file__))
        new_filepath = os.path.join(location, filepath)
        with open(new_filepath) as f:
            return f.read()

    @classmethod
    @patch('Monitor.link.logging.getLogger')
    def setUpClass(cls, mock_logging):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.ipv4_link = Link('10.1.1.1', '10.1.1.2', cls.grpc_client)
        cls.ipv6_link = Link('10:1:1::1', '10:1:1::2', cls.grpc_client)

    def link_object(self):
        lnk = Link('10.1.1.1', '10.1.1.2', self.grpc_client, 10, 20, 5, 5)
        self.assertIsInstance(lnk, Link)
        self.assertEqual(lnk.bw_thres, 10)
        self.assertEqual(lnk.jitter_thres, 20)
        self.assertEqual(lnk.pkt_loss, 5)
        self.assertEqual(lnk.interval, 5)

    @patch('Monitor.link.subprocess.Popen.communicate')
    def test_iperf_v4(self, mock_communicate):
        err = 'read failed: Connection refused\n'
        mock_communicate.return_value = ['', err]
        response = self.ipv4_link.run_iperf()
        self.assertTrue(response)

        out = self.read_file('Examples/iPerf/good.txt')
        mock_communicate.return_value = [out, '']
        self.assertFalse(self.ipv4_link.run_iperf())

        out = self.read_file('Examples/iPerf/high-bandwidth.txt')
        mock_communicate.return_value = [out, '']
        self.assertTrue(self.ipv4_link.run_iperf())

    @patch('Monitor.link.subprocess.Popen.communicate')
    def test_iperf_v6(self, mock_communicate):
        err = 'read failed: Connection refused\n'
        mock_communicate.return_value = ['', err]
        response = self.ipv6_link.run_iperf()
        self.assertTrue(response)

        out = self.read_file('Examples/iPerf/good.txt')
        mock_communicate.return_value = [out, '']
        self.assertFalse(self.ipv6_link.run_iperf())

        out = self.read_file('Examples/iPerf/high-bandwidth.txt')
        mock_communicate.return_value = [out, '']
        self.assertTrue(self.ipv6_link.run_iperf())

    @patch('Monitor.link.Link.check_routing')
    @patch('Monitor.link.Link.run_iperf')
    def test_health_v4(self, mock_iperf, mock_routing):
        protocol = 'ISIS'
        #Problem with the link.
        mock_routing.return_value = True
        self.assertTrue(self.ipv4_link.health(protocol))
        mock_iperf.assert_not_called()
        #No problems!
        mock_routing.return_value = False
        mock_iperf.return_value = False
        self.assertFalse(self.ipv4_link.health(protocol))
        #Problem with iPerf.
        mock_routing.return_value = False
        mock_iperf.return_value = True
        self.assertTrue(self.ipv4_link.health(protocol))

    @patch('Monitor.link.Link.check_routing')
    @patch('Monitor.link.Link.run_iperf')
    def test_health_v6(self, mock_iperf, mock_routing):
        protocol = 'ISIS'
        #Problem with the link.
        mock_routing.return_value = True
        self.assertTrue(self.ipv6_link.health(protocol))
        mock_iperf.assert_not_called()
        #No problems!
        mock_routing.return_value = False
        mock_iperf.return_value = False
        self.assertFalse(self.ipv6_link.health(protocol))
        #Problem with iPerf.
        mock_routing.return_value = False
        mock_iperf.return_value = True
        self.assertTrue(self.ipv6_link.health(protocol))

    def test_check_protocol(self):
        from Tools.exceptions import ProtocolError
        with self.assertRaises(ProtocolError):
            self.ipv4_link._check_protocol('')
            self.ipv4_link._check_protocol('bad')
            self.ipv4_link._check_protocol('\n')
        self.assertIsNone(self.ipv4_link._check_protocol('bgp'))
        self.assertIsNone(self.ipv4_link._check_protocol('isis'))

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_routing_v4(self, mock_get):
        from Tools.exceptions import ProtocolError
        with self.assertRaises(ProtocolError):
            result = self.ipv4_link.check_routing('bad')
            mock_get.assert_not_called()
            self.assertFalse(result)

        output_good = self.read_file('Examples/RIB/protocol-active.txt')
        mock_get.return_value = '', output_good
        self.assertFalse(self.ipv4_link.check_routing('isis'))
        self.assertTrue(self.ipv4_link.check_routing('bgp'))

        output_bad = self.read_file('Examples/RIB/bad-protocol.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(self.ipv4_link.check_routing('isis'))

        output_bad = self.read_file('Examples/RIB/non-active.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(self.ipv4_link.check_routing('isis'))

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        from Tools.exceptions import GRPCError
        with self.assertRaises(GRPCError):
            err = Mock(message='error string')
            mock_get.return_value = err, output_bad
            self.ipv4_link.check_routing('isis')
            
            err = Mock(message=error_tag)
            mock_get.return_value = err, output_bad
            self.ipv4_link.check_routing('isis')

            err = Mock(message=error_msg)
            mock_get.return_value = err, output_bad
            self.ipv4_link.check_routing('isis')

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_routing_v6(self, mock_get):
        from Tools.exceptions import ProtocolError
        with self.assertRaises(ProtocolError):
            result = self.ipv6_link.check_routing('bad')
            mock_get.assert_not_called()
            self.assertFalse(result)

        output_good = self.read_file('Examples/RIB/protocol-active.txt')
        mock_get.return_value = '', output_good
        self.assertFalse(self.ipv6_link.check_routing('isis'))
        self.assertTrue(self.ipv6_link.check_routing('bgp'))

        output_bad = self.read_file('Examples/RIB/bad-protocol.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(self.ipv6_link.check_routing('isis'))

        output_bad = self.read_file('Examples/RIB/non-active.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(self.ipv6_link.check_routing('isis'))

        from Tools.exceptions import GRPCError
        with self.assertRaises(GRPCError):
            err = Mock(message='error string')
            mock_get.return_value = err, output_bad
            self.ipv6_link.check_routing('isis')

            err = Mock(message='{"cisco-grpc:errors": {"error": [{"error-type": "protocol","error-tag": "unknown-element","error-severity": "error","error-path": "Cisco-IOS-XR-ip-rib-ipv4-oper:ns1:rib/ns1:vrf"}]}}')
            mock_get.return_value = err, output_bad
            self.ipv6_link.check_routing('isis')

            err = Mock(message='{"cisco-grpc:errors": {"error": [{"error-type": "application","error-tag": "operation-failed","error-severity": "error","error-message": "The instance name is used already: asn 0.1 inst-name default"}]}}')
            mock_get.return_value = err, output_bad
            self.ipv6_link.check_routing('isis')

if __name__ == '__main__':
    unittest.main()
