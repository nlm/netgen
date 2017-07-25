from __future__ import print_function, unicode_literals
import unittest
import netgen
import netgen.engine
from ipaddress import IPv4Address, IPv4Network

class IPv4Host(unittest.TestCase):

    def setUp(self):
        self.host = netgen.IPv4Host('testhost', '192.168.2.34')

    def test_host_name(self):
        self.assertEqual(self.host.name, 'testhost')

    def test_host_address(self):
        self.assertEqual(str(self.host.address), '192.168.2.34')


class IPv6Host(unittest.TestCase):

    def setUp(self):
        self.host = netgen.IPv6Host('testhost', '2001:c001::1')

    def test_host_name(self):
        self.assertEqual(self.host.name, 'testhost')

    def test_host_address(self):
        self.assertEqual(str(self.host.address), '2001:c001::1')


class SimpleIPv4Subnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.IPv4Subnet('testsub', '192.168.10.0/24')

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.10.0/24')


class VlanIPv4Subnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.IPv4Subnet('testsub', '192.168.10.0/24', 12)

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.10.0/24')

    def test_vlan(self):
        self.assertEqual(self.subnet.vlan, 12)


class IPv4SubnetXX(object):

    def setUp(self):
        self.netname = None

    def test_name(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.name, self.netname)

    def test_network(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.network, IPv4Network(self.network))

    def test_vlan(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.vlan, None)

    def test_add_host(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        for name, addr in self.hosts:
            subnet.add_host(name)

        self.assertRaises(netgen.NetworkFull,
                          subnet.add_host,
                          'coolhost')

        self.assertEqual(str(subnet.hosts),
                         str([netgen.IPv4Host(name, addr) for name, addr in self.hosts]))

    def test_minmax_addr(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.min_addr, IPv4Address(self.hosts[0][1]))
        self.assertEqual(subnet.max_addr, IPv4Address(self.hosts[-1][1]))


class IPv4Subnet32(IPv4SubnetXX, unittest.TestCase):

    def setUp(self):
        self.netname = 'testsub'
        self.network = '192.168.23.2/32'
        self.netaddress = '192.168.23.2'
        self.hosts = (('testhost1', '192.168.23.2'),)

    def test_cur_addr(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.cur_addr, IPv4Address(self.netaddress))


class IPv4Subnet31(IPv4SubnetXX, unittest.TestCase):

    def setUp(self):
        self.netname = 'testsub'
        self.network = '192.168.23.0/31'
        self.netaddress = '192.168.23.0'
        self.hosts = (('testhost1', '192.168.23.0'),
                      ('testhost2', '192.168.23.1'))

    def test_cur_addr(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.cur_addr, IPv4Address(self.netaddress))


class IPv4Subnet30(IPv4SubnetXX, unittest.TestCase):

    def setUp(self):
        self.netname = 'testsub'
        self.network = '192.168.19.0/30'
        self.netaddress = '192.168.19.0'
        self.hosts = (('testhost1', '192.168.19.1'),
                      ('testhost2', '192.168.19.2'))

    def test_cur_addr(self):
        subnet = netgen.IPv4Subnet(self.netname, self.network)
        self.assertEqual(subnet.cur_addr, IPv4Address(self.netaddress) + 1)


class UnalignedIPv4Subnet(unittest.TestCase):

    def setUp(self):
        self.subnet = netgen.IPv4Subnet('testsub', '192.168.23.45/24')

    def test_name(self):
        self.assertEqual(self.subnet.name, 'testsub')

    def test_address(self):
        self.assertEqual(str(self.subnet.network), '192.168.23.0/24')


class SimpleIPv4Zone(unittest.TestCase):

    def setUp(self):
        self.zone = netgen.IPv4Zone('testzone', '192.168.20.0/23')

    def test_name(self):
        self.assertEqual(self.zone.name, 'testzone')

    def test_network(self):
        self.assertEqual(str(self.zone.network), '192.168.20.0/23')

    def test_curaddr(self):
        self.assertEqual(self.zone.cur_addr,
                         self.zone.network.network_address)

    def test_subnets(self):
        self.assertEqual(self.zone.subnets, [])

class UnalignedIPv4Zone(unittest.TestCase):

    def setUp(self):
        self.zone = netgen.IPv4Zone('testzone', '192.168.21.10/23')

    def test_name(self):
        self.assertEqual(self.zone.name, 'testzone')

    def test_network(self):
        self.assertEqual(str(self.zone.network), '192.168.20.0/23')

    def test_curaddr(self):
        self.assertEqual(self.zone.cur_addr,
                         self.zone.network.network_address)

    def test_subnets(self):
        self.assertEqual(self.zone.subnets, [])

class TemplateUtils(unittest.TestCase):

    def setUp(self):
        self.TemplateUtils = netgen.engine.TemplateUtils

    def test_orange(self):
        for count in range(10):
            self.assertEqual(self.TemplateUtils.orange(count), range(count))

    def test_xorange(self):
        for count in range(10):
            self.assertEqual([i for i in self.TemplateUtils.orange(count)],
                             [i for i in range(count)])

    def test_orange_offset(self):
        for count in range(10):
            for offset in range(10):
                self.assertEqual(self.TemplateUtils.orange(count, offset=offset),
                                 [i + offset for i in range(count)])

    def test_xorange_offset(self):
        for count in range(10):
            for offset in range(10):
                self.assertEqual([i for i in self.TemplateUtils.xorange(count, offset=offset)],
                                 [i + offset for i in range(count)])


