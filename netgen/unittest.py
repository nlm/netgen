import unittest
import netgen

class Host(unittest.TestCase):

    def setUp(self):
        self.host = netgen.Host('testhost', '192.168.2.34')

    def test_host_name(self):
        self.assertEqual(self.host.name, 'testhost')

    def test_host_address(self):
        self.assertEqual(str(self.host.address), '192.168.2.34')


class SimpleSubnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.Subnet('testsub', '192.168.10.0/24')

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.10.0/24')


class VlanSubnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.Subnet('testsub', '192.168.10.0/24', 12)

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.10.0/24')

    def test_vlan(self):
        self.assertEqual(self.subnet.vlan, 12)


class UnalignedSubnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.Subnet('testsub', '192.168.23.45/24')

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.23.0/24')


class SimpleZone(unittest.TestCase):

    def setUp(self):
        self.zone = netgen.Zone('testzone', '192.168.20.0/23')

    def test_name(self):
        self.assertEqual(self.zone.name, 'testzone')

    def test_network(self):
        self.assertEqual(str(self.zone.network), '192.168.20.0/23')

    def test_curaddr(self):
        self.assertEqual(self.zone.cur_addr,
                         self.zone.network.network_address)

    def test_subnets(self):
        self.assertEqual(self.zone.subnets, [])

class UnalignedZone(unittest.TestCase):

    def setUp(self):
        self.zone = netgen.Zone('testzone', '192.168.21.10/23')

    def test_name(self):
        self.assertEqual(self.zone.name, 'testzone')

    def test_network(self):
        self.assertEqual(str(self.zone.network), '192.168.20.0/23')

    def test_curaddr(self):
        self.assertEqual(self.zone.cur_addr,
                         self.zone.network.network_address)

    def test_subnets(self):
        self.assertEqual(self.zone.subnets, [])
