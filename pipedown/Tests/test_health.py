import unittest
import os
from mock import patch, Mock

import log
from Monitor.link import Link
from Monitor import health
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient

def read_file(filename):
    """Takes a filename and concatenates it with the location of this file.

    Args:
        filename (str): The filename
  
    Returns:
        str: Read file.
    """
    location = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(location, filename)) as f:
        return f.read()

class HealthTestCase(unittest.TestCase, object):
    @staticmethod
    def read_file(filepath):
        location = os.path.dirname(os.path.realpath(__file__))
        new_filepath = os.path.join(location, filepath)
        with open(new_filepath) as f:
            return f.read()

    @classmethod
    @patch('Monitor.health.logging.getLogger')
    def setUpClass(cls, mock_logging):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.ipv4_link = Link('10.1.1.1', '10.1.1.2', ['BGP', 'ISIS'])
        cls.ipv6_link = Link('10:1:1::1', '10:1:1::2', ['BGP', 'OSPF'])

    @patch('Monitor.health.subprocess.Popen.communicate')
    def test_iperf_v4(self, mock_communicate):
        err = 'read failed: Connection refused\n'
        mock_communicate.return_value = ['', err]
        response = health.run_iperf(self.ipv4_link, 10, 20, 5, 5)
        self.assertTrue(response)

        out = self.read_file('Examples/iPerf/good.txt')
        mock_communicate.return_value = [out, '']
        self.assertFalse(health.run_iperf(self.ipv4_link))

        out = self.read_file('Examples/iPerf/high-bandwidth.txt')
        mock_communicate.return_value = [out, '']
        self.assertTrue(health.run_iperf(self.ipv4_link))

    @patch('Monitor.health.subprocess.Popen.communicate')
    def test_iperf_v6(self, mock_communicate):
        err = 'read failed: Connection refused\n'
        mock_communicate.return_value = ['', err]
        response = health.run_iperf(self.ipv6_link)
        self.assertTrue(response)

        out = self.read_file('Examples/iPerf/good.txt')
        mock_communicate.return_value = [out, '']
        self.assertFalse(health.run_iperf(self.ipv6_link))

        out = self.read_file('Examples/iPerf/high-bandwidth.txt')
        mock_communicate.return_value = [out, '']
        self.assertTrue(health.run_iperf(self.ipv6_link))

    @patch('Monitor.health.check_rib')
    @patch('Monitor.health.run_iperf')
    def test_health_v4(self, mock_iperf, mock_routing):
        #Problem with the link.
        mock_routing.return_value = True
        self.assertTrue(health.health(self.ipv4_link, self.grpc_client))
        mock_iperf.assert_not_called()
        #No problems!
        mock_routing.return_value = False
        mock_iperf.return_value = False
        self.assertFalse(health.health(self.ipv4_link, self.grpc_client))
        #Problem with iPerf.
        mock_routing.return_value = False
        mock_iperf.return_value = True
        self.assertTrue(health.health(self.ipv4_link, self.grpc_client))

    @patch('Monitor.health.check_rib')
    @patch('Monitor.health.run_iperf')
    def test_health_v6(self, mock_iperf, mock_routing):
        #Problem with the link.
        mock_routing.return_value = True
        self.assertTrue(health.health(self.ipv6_link, self.grpc_client))
        mock_iperf.assert_not_called()
        #No problems!
        mock_routing.return_value = False
        mock_iperf.return_value = False
        self.assertFalse(health.health(self.ipv6_link, self.grpc_client))
        #Problem with iPerf.
        mock_routing.return_value = False
        mock_iperf.return_value = True
        self.assertTrue(health.health(self.ipv6_link, self.grpc_client))

    def test_check_protocol(self):
        from Tools.exceptions import ProtocolError
        with self.assertRaises(ProtocolError):
            self.ipv4_link._check_protocol('')
            self.ipv4_link._check_protocol('bad')
            self.ipv4_link._check_protocol('\n')
        self.assertIsNone(self.ipv4_link._check_protocol('bgp'))
        self.assertIsNone(self.ipv4_link._check_protocol('isis'))

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_rib_v4(self, mock_get):
        output_good = self.read_file('Examples/RIB/protocol-active.txt')
        mock_get.return_value = '', output_good
        self.assertTrue(health.check_rib(self.ipv4_link, self.grpc_client))

        output_bad = self.read_file('Examples/RIB/bad-protocol.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(health.check_rib(self.ipv4_link, self.grpc_client))

        output_bad = self.read_file('Examples/RIB/non-active.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(health.check_rib(self.ipv4_link, self.grpc_client))

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        from Tools.exceptions import GRPCError
        with self.assertRaises(GRPCError):
            err = Mock(message='error string')
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv4_link, self.grpc_client)

            err = Mock(message=error_tag)
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv4_link, self.grpc_client)

            err = Mock(message=error_msg)
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv4_link, self.grpc_client)

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getoper')
    def test_check_rib_v6(self, mock_get):
        output_good = self.read_file('Examples/RIB/protocol-active.txt')
        mock_get.return_value = '', output_good
        self.assertTrue(health.check_rib(self.ipv6_link, self.grpc_client))

        output_bad = self.read_file('Examples/RIB/bad-protocol.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(health.check_rib(self.ipv6_link, self.grpc_client))

        output_bad = self.read_file('Examples/RIB/non-active.txt')
        mock_get.return_value = '', output_bad
        self.assertTrue(health.check_rib(self.ipv6_link, self.grpc_client))

        from Tools.exceptions import GRPCError
        with self.assertRaises(GRPCError):
            err = Mock(message='error string')
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv6_link, self.grpc_client)

            err = Mock(message='{"cisco-grpc:errors": {"error": [{"error-type": "protocol","error-tag": "unknown-element","error-severity": "error","error-path": "Cisco-IOS-XR-ip-rib-ipv4-oper:ns1:rib/ns1:vrf"}]}}')
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv6_link, self.grpc_client)

            err = Mock(message='{"cisco-grpc:errors": {"error": [{"error-type": "application","error-tag": "operation-failed","error-severity": "error","error-message": "The instance name is used already: asn 0.1 inst-name default"}]}}')
            mock_get.return_value = err, output_bad
            health.check_rib(self.ipv6_link, self.grpc_client)

if __name__ == '__main__':
    unittest.main()
