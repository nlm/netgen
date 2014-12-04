import yaml
from ipaddress import IPv4Network, IPv4Address
from jinja2 import Environment, FileSystemLoader
from .schema import Validator
from .output import Output

class NetworkGenerator(object):
    def __init__(self, data):
        self.zones = []
        if isinstance(data, Topology):
            self.parse(data.data)
        else:
            self.parse(data)

    def add_zone(self, name, network, vrf=None):
        zone = Zone(name, network, vrf)
        self.zones.append(zone)
        return zone

    def parse(self, data):
        Validator().validate(data)
        zi = self.add_zone(data['zone'], data['network'], data['vrf'])
        for subnet in data['subnets']:
            si = zi.add_subnet(subnet['subnet'], subnet['size'])
            if 'hosts' in subnet:
                for host in subnet['hosts']:
                    si.add_host(host)

    def output(self, output_class, params=None):
        if not issubclass(output_class, Output):
            raise Exception('bad out class: {0}'.format(output_class))
        output_class().output(self, params)


class Zone(object):
    def __init__(self, name, network, vrf=None):
        self.name = name
        self.network = IPv4Network(network, strict=True)
        self.vrf = vrf
        self.cur_addr = self.network.network_address
        self.subnets = []

    def add_subnet(self, name, size, vlan=None):
        assert size <= 32
        net = Subnet(name, '{0}/{1}'.format(self.cur_addr, size), self, vlan)
        self.cur_addr += net.network.num_addresses
        self.subnets.append(net)
        return net

    def __repr__(self):
        return 'Zone({0}: {1}) [{2}]'.format(self.name, self.network, self.vrf)


class Subnet(object):
    def __init__(self, name, network, zone, vlan=None):
        self.name = name
        self.hosts = []
        self.zone = zone
        self.vlan = vlan
        try:
            self.network = IPv4Network(network, strict=True)
        except ValueError:
            net = IPv4Network(network, strict=False)
            addr = net.network_address
            net2 = '{0}/{1}'.format(addr + net.num_addresses, net.prefixlen)
            self.network = IPv4Network(net2)
            print('warning: subnet {0} is unaligned'.format(self.network))

    def __repr__(self):
        return 'Subnet({0}: {1})'.format(self.name, self.network)

    def add_host(self, name):
        addr = self.network.network_address + 1 + len(self.hosts)
        if addr not in self.network:
            raise Exception('subnet "{0}" full'.format(self.network))
        host = Host(name, addr, self)
        self.hosts.append(host)
        return host


class Host(object):
    def __init__(self, name, address, subnet):
        self.name = name
        self.address = IPv4Address(address)
        self.subnet = subnet

    def __repr__(self):
        return 'Host({0}: {1})'.format(self.name, self.address)


class Topology(object):
    def __init__(self, zone, vrf, network, template, templatesdir='templates'):
        self.env = Environment(loader=FileSystemLoader(templatesdir))
        self.template = self.env.get_template(template + '.yaml')
        self.zone = zone
        self.vrf = vrf
        self.network = IPv4Network(network)
        self._rendered = None
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = yaml.load(str(self))
        return self._data

    def __str__(self):
        if self._rendered is None:
            self._rendered = self.template.render(zone=self.zone,
                                                  vrf=self.vrf,
                                                  network=self.network)
        return self._rendered
