import unittest
from log import log

class TestMixIn(unittest.TestCase, object):
    @classmethod
    def setUpClass(cls):
        #Silence stream logger.
        console_handler = log.logger.console_handler
        console_handler.close()
        log.logger.removeHandler(console_handler)