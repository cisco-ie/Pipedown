import unittest
import os
import json
from mock import patch

from Response import response
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Tools.exceptions import GRPCError

def read_file(filename):
    """Takes a filename and concatenates it with the location of this file.
    :param filename: The filename
    :param type: str
    """
    location = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(location, filename)) as f:
        return f.read()

class ResponseTestCase(unittest.TestCase, object):
    @classmethod
    def setUpClass(cls):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.neighbor_as = [65000]
        cls.policy_name = 'drop'
        cls.cisco_config = json.loads(read_file('Examples/BGP/cisco-orig.txt'))
        cls.open_config = read_file('Examples/BGP/openconfig.txt')
        cls.cisco_template ='{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {"instance": [{"instance-name": "default","instance-as": [{"four-byte-as": [{"default-vrf": {"bgp-entity": {"neighbors": {"neighbor": [{"neighbor-afs": {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}'

    @patch('Response.response.get_bgp_config')
    @patch('Response.response.apply_policy')
    def test_cisco_update(self, apply_mock, get_mock):
        # Test when everything is working correctly.
        get_mock.return_value = json.dumps(self.cisco_config)
        apply_mock.return_value = None
        updated_neigh = response.cisco_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        correct_neigh = [
            (u'11.1.1.20', u'ipv4-unicast', u'pass', 'drop'),
            (u'11.1.1.20', u'ipv6-unicast', u'pass', 'drop')
        ]
        self.assertEqual(updated_neigh, correct_neigh)
        get_mock.assert_called_with(self.grpc_client, self.cisco_template)
        cisco_new = read_file('Examples/BGP/cisco-new.txt')
        apply_mock.assert_called_with(self.grpc_client, json.loads(cisco_new))

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        apply_mock.side_effect = GRPCError(error_tag)
        with self.assertRaises(GRPCError):
            updated_neigh = response.cisco_update(
                self.grpc_client,
                self.neighbor_as,
                self.policy_name
                )
        get_mock.side_effect = GRPCError(error_msg)
        with self.assertRaises(GRPCError):
            updated_neigh = response.cisco_update(
                self.grpc_client,
                self.neighbor_as,
                self.policy_name
                )

    @patch('Response.response.get_bgp_config')
    @patch('Response.response.apply_policy')
    def test_open_config_update(self, apply_mock, get_mock):
        # Test when everything is working correctly.
        get_mock.return_value = self.open_config
        apply_mock.return_value = None
        updated_neigh = response.open_config_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        correct_neigh = [
            (u'11.1.1.20', u'ipv4-unicast', u'pass', 'drop'),
            (u'11.1.1.20', u'ipv6-unicast', u'pass', 'drop')
        ]
        self.assertEqual(updated_neigh, correct_neigh)

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        # Test when GRPC throws an error on merge.
        apply_mock.side_effect = GRPCError(error_msg)
        with self.assertRaises(GRPCError):
            updated_neigh = response.open_config_update(
                self.grpc_client,
                self.neighbor_as,
                self.policy_name
                )
        get_mock.side_effect = GRPCError(error_tag)
        with self.assertRaises(GRPCError):
            updated_neigh = response.open_config_update(
                self.grpc_client,
                self.neighbor_as,
                self.policy_name
                )

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getconfig')
    @patch('Response.response.LOGGER')
    def test_get_bgp_config(self, mock_logger, mock_get):
        mock_get.return_value = '', self.cisco_config
        value = response.get_bgp_config(self.grpc_client, self.cisco_template)
        self.assertTrue(value, self.cisco_config)
        mock_get.assert_called_with(self.cisco_template)

        with self.assertRaises(GRPCError):
            err = read_file('Examples/Errors/grpc-tag.txt')
            mock_get.return_value = err, ''
            response.get_bgp_config(self.grpc_client, self.cisco_template)
            self.assertTrue(mock_logger.error.called)

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.mergeconfig')
    @patch('Response.response.LOGGER')
    def test_apply_policy(self, mock_logger, mock_merge):
        class A():
            def __init__(self, err, other):
                self.errors = err
                self.other = other

        mock_merge.return_value = A('', 'No error here!')
        response.apply_policy(self.grpc_client, self.cisco_config)
        self.assertTrue(mock_logger.info.called)
        mock_merge.assert_called_with(json.dumps(self.cisco_config))

        with self.assertRaises(GRPCError):
            err = read_file('Examples/Errors/grpc-tag.txt')
            mock_merge.return_value = A(err, '')
            response.apply_policy(self.grpc_client, self.cisco_config)
            self.assertTrue(mock_logger.error.called)

if __name__ == '__main__':
    unittest.main()















