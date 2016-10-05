
import unittest
import logging
import json
from mock import patch
from Tools.grpc_cisco_python.client.cisco_grpc_client import CiscoGRPCClient
from Flush.bgp_flush import Flush_BGP

logging.basicConfig(level=logging.DEBUG)

class FlushBGPTestCase(unittest.TestCase, object):
	@staticmethod
	def read_file(fp):
		with open(fp) as f:
			return f.read()

	def setUp(self):
		self.client = CiscoGRPCClient('10.85.138.39', 57400, 10, 'cisco', 'cisco')
	
	@patch('Flush.bgp_flush.Flush_BGP.get_bgp_neighbors')
	def test_bgp_flush(self, mock_get_bgp_neighbors):
		config_path = 'Flush/get-neighborsq.json'
		ext_as = [2235, 44444]
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




		


		
		



