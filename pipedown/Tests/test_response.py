import unittest
import logging
import os
from mock import patch
import json
from pipedown.Response import response
from pipedown.Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from pipedown.Tools.exceptions import GRPCError

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
    @patch('pipedown.Monitor.link.logging.getLogger')
    def setUpClass(cls, mock_logging):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.neighbor_as = [65000]
        cls.policy_name = 'drop'
        cls.cisco_config = read_file('Examples/BGP/cisco-orig.txt')
        cls.open_config = read_file('Examples/BGP/openconfig.txt')


    @patch('pipedown.Response.response.get_bgp_config')
    @patch('pipedown.Response.response.apply_policy')
    def test_cisco_update(self, apply_mock, get_mock):
        # Test when everything is working correctly.
        get_mock.return_value = self.cisco_config
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
            '{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": {"instance": [{"instance-name": "default","instance-as": [{"four-byte-as": [{"default-vrf": {"bgp-entity": {"neighbors": {"neighbor": [{"neighbor-afs": {"neighbor-af": []},"remote-as": {}}]}}}}]}]}]}}'
            )
        cisco_new = read_file('Examples/BGP/cisco-new.txt')
        apply_mock.assert_called_with(self.grpc_client, json.loads(cisco_new))

        # Test when GRPC throws an error on merge.
        error = read_file('Examples/Errors/grpc-message.txt')
        apply_mock.side_effect = GRPCError(error)
        updated_neigh = response.cisco_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Merge Error.'
            )

        # Test when GRPC throws an error on get.
        error = read_file('Examples/Errors/grpc-tag.txt')
        get_mock.side_effect = GRPCError(error)
        updated_neigh = response.cisco_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Get Error.'
            )

    @patch('pipedown.Response.response.get_bgp_config')
    @patch('pipedown.Response.response.apply_policy')
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

        # Test when GRPC throws an error on merge.
        error = read_file('Examples/Errors/grpc-message.txt')
        apply_mock.side_effect = GRPCError(error)
        updated_neigh = response.open_config_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Merge Error.'
            )

        # Test when GRPC throws an error on get.
        error = read_file('Examples/Errors/grpc-tag.txt')
        get_mock.side_effect = GRPCError(error)
        updated_neigh = response.open_config_update(
            self.grpc_client,
            self.neighbor_as,
            self.policy_name
            )
        self.assertEqual(
            updated_neigh,
            'No neighbors updated due to GRPC Get Error.'
            )

    @patch('pipedown.Tools.grpc_cisco_python.client.cisco_grpc_client.getconfig')
    def test_bgp_config(self, mock_get):
        pass

    def test_apply_policy(self):
        pass
        #mock_get_bgp_neighbors.return_value = [('2.2.3.7', 'pass'), ('4.4.4.1', 'pass')]

if __name__ == '__main__':
    unittest.main()















