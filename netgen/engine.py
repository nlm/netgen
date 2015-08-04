from __future__ import print_function, unicode_literals
from six import u
import sys
import yaml
import re
from ipaddress import IPv4Network, IPv4Address
from jinja2 import Environment, FileSystemLoader
from voluptuous import Schema, Match, Required, Optional, MultipleInvalid

from .exception import NetworkFull, ConfigError


def dot_reverse(value):
    return ".".join(reversed(str(value).split(".")))


def add_custom_filters(environment):
    environment.filters['dotreverse'] = dot_reverse


class Topology(object):
    pass


class IPv4Topology(Topology):
    def __init__(self, zone, vrf, network, template, properties=None, loader=None):
        if loader is None:
            loader = FileSystemLoader('templates')
        env = Environment(loader=loader, extensions=['jinja2.ext.do'])
        add_custom_filters(env)
        self.template = env.get_template('{0}.yaml'.format(template))
        self.zone = zone
        self.vrf = vrf
        self.properties = 0
        self.network = IPv4Network(u(str(network)))
        self.properties = properties if properties is not None else {}
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
                network=self.network,
                properties=self.properties)
        return self._rendered


class IPv6Topology(Topology):
    pass


class NetworkGenerator(object):
    pass


class IPv4NetworkGenerator(NetworkGenerator):

    topology_schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9-]+$'),
        Required('network'): lambda x: str(IPv4Network(u(str(x)))),
        Required('vrf'): Match('^[A-Za-z0-9-]+$'),
        Required('subnets'): [{
            Required('name'): Match('^([A-Za-z0-9-]+|_)$'),
            Required('size'): int,
            Optional('vlan'): int,
            Optional('align'): int,
            Optional('mtu'): int,
            Optional('hosts'): [Match('^([A-Za-z0-9-]+|_(/\d+)?)$')],
        }]
    })

    def __init__(self, data):
        self.zones = []
        if isinstance(data, IPv4Topology):
            self.parse(data.data)
        else:
            self.parse(data)

    def add_zone(self, name, network, vrf=None):
        zone = IPv4Zone(name, network, vrf)
        self.zones.append(zone)
        return zone

    def parse(self, data):
        data = self.topology_schema(data)

        zone = self.add_zone(data['zone'], data['network'], data['vrf'])
        for elt in data.get('subnets', []):
            try:
                subnet = zone.add_subnet(elt['name'], elt['size'],
                                         vlan=elt.get('vlan'),
                                         align=elt.get('align'),
                                         mtu=elt.get('mtu'))
            except NetworkFull:
                raise NetworkFull('network full while adding subnet "{0}" ' \
                                  'to network {1} of zone "{2}"' \
                                  .format(elt['name'], data['network'],
                                          data['zone']))

            for hostname in elt.get('hosts', []):
                try:
                    subnet.add_host(hostname)
                except NetworkFull:
                    raise NetworkFull('network full while adding host "{0}" ' \
                                      'to subnet "{1}" in network "{2}" ' \
                                      'of zone "{3}"' \
                                      .format(hostname, elt['name'],
                                              data['network'], data['zone']))

    def render(self, template, loader, with_hosts=True):
        env = Environment(loader=loader, extensions=['jinja2.ext.do'])
        add_custom_filters(env)
        template = env.get_template('{0}.tpl'.format(template))
        return template.render(zones=self.zones, with_hosts=with_hosts)


class IPv6NetworkGenerator(NetworkGenerator):
    pass


class IPv4Zone(object):
    def __init__(self, name, network, vrf=None):
        self.name = name
        self.network = IPv4Network(u(str(network)), strict=False)
        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)
        self.vrf = vrf
        self.cur_addr = self.network.network_address
        self.subnets = []

    def add_subnet(self, name, size, vlan=None, align=None, mtu=None):
        """
        Adds a subnet to this zone

        args:
            name: name of the subnet to be added
            size: size of the subnet
            vlan: optional vlan number
        returns:
            the created Subnet object
        """
        if not 0 <= size <= 32:
            raise ConfigError('subnet size must be between 0 and 32')

        # align if asked
        if align is not None:
            try:
                network = IPv4Network('{0}/{1}'.format(self.cur_addr, align), strict=True)
            except ValueError:
                network = IPv4Network('{0}/{1}'.format(self.cur_addr, align), strict=False)
                self.cur_addr = network.network_address + network.num_addresses

        # if size is 0, subnet is shadow
        if size == 0:
            if name == '_':
                return None
            raise ConfigError('zero-sized subnets must be named "_"')

        # looking for next subnet address
        try:
            network = IPv4Network('{0}/{1}'.format(self.cur_addr, size), strict=True)
        except ValueError:
            net1 = IPv4Network('{0}/{1}'.format(self.cur_addr, size), strict=False)
            addr = net1.network_address
            net2 = '{0}/{1}'.format(addr + net1.num_addresses, net1.prefixlen)
            network = IPv4Network(net2)
            print('warning: {0}: unaligned subnet, lost some ips'.format(network), file=sys.stderr)
            self.cur_addr = network.network_address
        # building the subnet
        subnet = IPv4Subnet(name, u(str(network)), vlan, mtu)
        # checking ownership
        if (subnet.network.network_address < self.network.network_address or
            subnet.network.broadcast_address > self.network.broadcast_address):
            raise NetworkFull
        self.cur_addr += subnet.network.num_addresses
        if name == '_':
            return None
        self.subnets.append(subnet)
        return subnet

    def __repr__(self):
        return 'Zone({0}: {1}) [{2}]'.format(self.name, self.network, self.vrf)


class Subnet(object):
    def __init__(self, name, network, vlan=None):
        raise NotImplementedError()

    def add_host(self, name):
        raise NotImplementedError()


class IPv4Subnet(Subnet):
    """
    Object representing a Subnet
    """
    def __init__(self, name, network, vlan=None, mtu=None):
        """
        Subject object initialization

        args:
            name: subnet name
            network: Network address of the subnet
            vlan: optional vlan
        """
        self.name = name
        self.hosts = []
        self.vlan = vlan
        self.mtu = mtu
        self.network = IPv4Network(network, strict=False)

        if self.network.prefixlen >= 31:
            self.min_addr = self.network.network_address
            self.max_addr = self.network.broadcast_address
        else:
            self.min_addr = self.network.network_address + 1
            self.max_addr = self.network.broadcast_address - 1

        self.cur_addr = self.min_addr

        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)

    def __repr__(self):
        if self.vlan is not None:
            return 'Subnet({0}: {1}) [{2}]'.format(self.name, self.network,
                                                   self.vlan)
        else:
            return 'Subnet({0}: {1})'.format(self.name, self.network)

    def nextip(self, prefixlen):
        if not 0 < prefixlen < 32:
            raise ConfigError('invalid padding prefixlen: {0}'.format(prefixlen))
        tmpnet = IPv4Network('{0}/{1}'.format(self.cur_addr, prefixlen),
                             strict=False)
        return tmpnet.network_address + tmpnet.num_addresses + 1

    def add_host(self, name):
        """
        Adds a host to this subnet

        args:
            name: name of the host to be added
        returns:
            the created Host object
        """
        addr = self.cur_addr
        if addr not in self.network or addr > self.max_addr:
            raise NetworkFull
        self.cur_addr += 1
        # check for special directives
        if name == '_':
            return None
        match = re.match(r'^_/(\d+)$', name)
        if match:
            self.cur_addr = self.nextip(int(match.group(1)))
            return None

        host = IPv4Host(name, addr)
        self.hosts.append(host)
        return host


class IPv6Subnet(Subnet):
    pass


class Host(object):
    pass


class IPv4Host(Host):
    """
    Object representing a Host
    """
    def __init__(self, name, address):
        """
        Host object initialization

        args:
            name: hostname
            address: IP address of the host
        """
        self.name = name
        self.address = IPv4Address(u(str(address)))

    def __repr__(self):
        return 'Host({0}: {1})'.format(self.name, self.address)


class IPv6Host(Host):
    pass
