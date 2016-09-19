import unittest
from mock import MagicMock
from Monitor import link

class LinkTestCase(unittest.TestCase, object):

    @classmethod
    def setUpClass(cls):
        cls.test_link = link.Link('10.1.1.1', '10.1.1.2')

    def test_link_object(self):
        lnk = link.Link('10.1.1.1', '10.1.1.2', 10, 20, 5, 5)
        self.assertIsInstance(lnk, link.Link)
        self.assertEqual(lnk.bw_thres, 10)
        self.assertEqual(lnk.jitter_thres, 20)
        self.assertEqual(lnk.pkt_loss, 5)
        self.assertEqual(lnk.interval, 5)

    def test_health(self):
        protocol = 'ISIS'
        self.test_link.check_routing = MagicMock()
        self.test_link.run_iperf = MagicMock()


