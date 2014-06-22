import yaml
from ipaddress import IPv4Network,IPv4Address
from jinja2 import Environment,PackageLoader
from .schema import Validator
from .output import Output

class NetworkGenerator(object):
    def __init__(self, data):
        self.zones = []
        if isinstance(data, Topology):
            self.parse(data.data)
        else:
            self.parse(data)

    def add_zone(self, name, network):
        zi = Zone(name, network)
        self.zones.append(zi)
        return zi

    def parse(self, data):
        Validator().validate(data)
        zi = self.add_zone(data['zone'], data['network'])
        for subnet in data['subnets']:
            si = zi.add_subnet(subnet['subnet'], subnet['size'])
            if 'hosts' in subnet:
                for host in subnet['hosts']:
                    si.add_host(host)

    def output(self, output_class, params=None):
        if not issubclass(output_class, Output):
            raise "bad out class"
        output_class().output(self, params)


class Zone(object):
    def __init__(self, name, network):
        self.name = name
        self.network = IPv4Network(unicode(network), strict=True)
        self.cur_addr = self.network.network_address
        self.subnets = []

    def __repr__(self):
        return u'Zone({}: {})'.format(self.name, self.network)

    def add_subnet(self, name, size, vlan=None):
        assert size <= 32
        net = Subnet(name, u'{}/{}'.format(self.cur_addr, size), self)
        self.cur_addr += net.network.num_addresses
        self.subnets.append(net)
        return net


class Subnet(object):
    def __init__(self, name, network, zone):
        self.name = name
        self.hosts = []
        self.zone = zone
        try:
            self.network = IPv4Network(unicode(network), strict=True)
        except ValueError:
            net = IPv4Network(unicode(network), strict=False)
            addr = net.network_address
            net2 = u'{}/{}'.format(addr + net.num_addresses, net.prefixlen)
            self.network = IPv4Network(net2)
            print "Warning: {}: unaligned subnet, lost some ips".format(self.network)

    def __repr__(self):
        return u'Subnet({}: {})'.format(self.name, self.network)

    def add_host(self, name):
        addr = self.network.network_address + 1 + len(self.hosts)
        if addr not in self.network:
            raise Exception("subnet full")
        host = Host(name, addr, self)
        self.hosts.append(host)
        return host


class Host(object):
    def __init__(self, name, address, subnet):
        self.name = name
        self.address = IPv4Address(address)
        self.subnet = subnet

    def __repr__(self):
        return u'Host({}: {})'.format(self.name, self.address)

class Topology(object):
    def __init__(self, zone, vrf, network, template):
        self.env = Environment(loader=PackageLoader('netgen', 'templates'))
        self.template = self.env.get_template(template + '.yaml')
        self.zone = zone
        self.vrf = vrf
        self.network = IPv4Network(unicode(network))
        self._rendered = None
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = yaml.load(str(self))
        return self._data

    def __str__(self):
        if self._rendered is None:
            self._rendered = self.template.render(
                                zone=self.zone,
                                vrf=self.vrf,
                                network=self.network)
        return self._rendered
