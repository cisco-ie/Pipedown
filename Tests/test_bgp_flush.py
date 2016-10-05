
import unittest
import logging
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
		path = '{"Cisco-IOS-XR-ip-static-cfg:router-static": [null]}'
		self._res = self.client.getconfig(path)
	
	
	def test_bgp_flush(self):
		config = self.read_file('Flush/get-neighborsq.json')
		client = CiscoGRPCClient('10.85.138.39', 57400, 10, 'cisco', 'cisco')
		self._res = client.getconfig(config)
		logging.debug(self._res)

		ext_as = [2235, 44444]

		
		



