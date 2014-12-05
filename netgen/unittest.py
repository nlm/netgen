import unittest
import netgen

class Host(unittest.TestCase):

    def setUp(self):
        self.host = netgen.Host('test', '192.168.2.34')

    def test_host_name(self):
        self.assertEqual(self.host.name, 'test')

    def test_host_address(self):
        self.assertEqual(self.host.address, '192.168.2.34')
