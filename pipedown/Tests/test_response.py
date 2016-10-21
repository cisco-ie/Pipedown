import unittest
import logging
import json
from mock import patch
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Flush.bgp_flush import Flush_BGP

logging.basicConfig(level=logging.DEBUG)

class FlushBGPTestCase(unittest.TestCase, object):
    @classmethod
    @patch('pipedown.Monitor.link.logging.getLogger')
    def setUpClass(cls, mock_logging):
        cls.grpc_client = CiscoGRPCClient('10.1.1.1', 57777, 10, 'test', 'test')
        cls.neighbor_as = 44444
        cls.policy_name = 'drop'
        location = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(location, '../Examples/bgp-good.txt')) as f:
            cls.bgp_config = f.read()
    @patch('Flush.bgp_flush.Flush_BGP.get_bgp_neighbors')
    def test_bgp_flush(self, mock_get_bgp_neighbors):
        config_path = 'Flush/get-neighborsq.json'
        
        flush = Flush_BGP(self.client, ext_as, 'drop', config_path)

        # make the mock call to the get_bgp_neighbors
        mock_get_bgp_neighbors.return_value = [('2.2.3.7', 'pass'), ('4.4.4.1', 'pass')]
        rm_neighbors = list(zip(*mock_get_bgp_neighbors.return_value)[0])

        
        # get the new BGP config after the mock call
        new_bgp_config = self.client.getconfig(self.read_file(config_path))
        new_bgp_config = json.loads(new_bgp_config)
        
        res = new_bgp_config["Cisco-IOS-XR-ipv4-bgp-cfg:bgp"]["instance"][0]["instance-as"][0]["four-byte-as"][0]
        res = res["default-vrf"]["bgp-entity"]["neighbors"]["neighbor"]
        
        for line in res:
            ip = line["neighbor-address"]
            if ip in rm_neighbors:
                # check if the new policy is drop
                new_policy = line['neighbor-afs']['neighbor-af'][0]['route-policy-out']
                self.assertTrue(new_policy, 'drop')

    @patch('pipedown.Response.get_bgp_config')
    @patch('pipedown.Response.apply_policy')
    def test_cisco_update_connection(self, apply_mock, get_mock):







if __name__ == '__main__':
    unittest.main()















