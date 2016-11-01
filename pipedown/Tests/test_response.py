import unittest
import logging
import os
from mock import patch
import json

from Response import response
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Tools.exceptions import GRPCError

logging.basicConfig(level=logging.DEBUG)

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
    @patch('Monitor.link.logging.getLogger')
    def setUpClass(cls, mock_logging):
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
        correct_neigh = json.dumps(
            [
                ['11.1.1.20', 'ipv4-unicast', 'pass'],
                ['11.1.1.20', 'ipv6-unicast', 'pass']
            ]
        )
        correct_neigh = 'Updated neighbors and policy: %s' % correct_neigh
        self.assertEqual(updated_neigh, correct_neigh)
        get_mock.assert_called_with(
            self.grpc_client,
            self.cisco_template
            )
        cisco_new = read_file('Examples/BGP/cisco-new.txt')
        apply_mock.assert_called_with(self.grpc_client, json.loads(cisco_new))

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        apply_mock.side_effect = GRPCError(error_tag)
        updated_neigh = response.cisco_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Merge Error.'
            )
        get_mock.side_effect = GRPCError(error_msg)
        updated_neigh = response.cisco_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Get Error.'
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
        correct_neigh = json.dumps(
            [
                ['11.1.1.20', 'ipv4-unicast', 'pass'],
                ['11.1.1.20', 'ipv6-unicast', 'pass']
            ]
        )
        correct_neigh = 'Updated neighbors and policy: %s' % correct_neigh
        self.assertEqual(updated_neigh, correct_neigh)

        error_tag = read_file('Examples/Errors/grpc-tag.txt')
        error_msg = read_file('Examples/Errors/grpc-message.txt')
        # Test when GRPC throws an error on merge.
        apply_mock.side_effect = GRPCError(error_msg)
        updated_neigh = response.open_config_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Merge Error.'
            )
        get_mock.side_effect = GRPCError(error_tag)
        updated_neigh = response.open_config_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Get Error.'
            )

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.getconfig')
    def test_get_bgp_config(self, get_mock):
        get_mock.return_value = '', self.cisco_config
        value = response.get_bgp_config(self.grpc_client, self.cisco_template)
        self.assertTrue(value, self.cisco_config)
        get_mock.assert_called_with(self.cisco_template)

        with self.assertRaises(GRPCError):
            err = read_file('Examples/Errors/grpc-tag.txt')
            get_mock.return_value = err, ''
            response.get_bgp_config(self.grpc_client, self.cisco_template)

    @patch('Tools.grpc_cisco_python.client.cisco_grpc_client.CiscoGRPCClient.mergeconfig')
    def test_apply_policy(self, merge_mock):
        class A():
            def __init__(self, err, other):
                self.errors = err
                self.other = other

        merge_mock.return_value = A('', 'No error here!')
        response.apply_policy(self.grpc_client, self.cisco_config)
        merge_mock.assert_called_with(json.dumps(self.cisco_config))

        with self.assertRaises(GRPCError):
            err = read_file('Examples/Errors/grpc-tag.txt')
            merge_mock.return_value = A(err, '')
            response.apply_policy(self.grpc_client, self.cisco_config)


if __name__ == '__main__':
    unittest.main()















