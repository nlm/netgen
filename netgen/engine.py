from __future__ import print_function, unicode_literals
from six import u
import sys
import yaml
import re
from ipaddress import IPv4Network, IPv4Address
from ipaddress import IPv6Network, IPv6Address
from ipaddress import AddressValueError
from jinja2 import Environment, FileSystemLoader
from voluptuous import Schema, Match, Required, Optional, MultipleInvalid, Any

from .exception import NetworkFull, ConfigError, UnalignedSubnet, ParameterError


def dot_reverse(value):
    return ".".join(reversed(str(value).split(".")))


def ipver(ipversion, valuev4, valuev6):
    if ipversion == 4:
        return valuev4
    elif ipversion == 6:
        return valuev6
    else:
        raise ParameterError('invalid value for ipversion: {0}'
                             .format(ipversion))


def add_custom_filters(environment):
    environment.filters['dotreverse'] = dot_reverse


def add_custom_functions(environment):
    environment.globals['ipv46'] = ipver


class Topology(object):

    def __init__(self, zone, vrf, network, template,
                 params=None, loader=None):
        if loader is None:
            loader = FileSystemLoader('templates')
        env = Environment(loader=loader,
                          extensions=['jinja2.ext.do',
                                      'jinja2.ext.loopcontrols'])
        add_custom_filters(env)
        add_custom_functions(env)
        self.template = env.get_template('{0}.yaml'.format(template))
        self.zone = zone
        self.vrf = vrf
        self.params = 0
        self.params = params if params is not None else {}
        self._rendered = None
        self._data = None

        try:
            self.network = IPv4Network(u(str(network)))
            self.ipversion = 4
        except AddressValueError:
            try:
                self.network = IPv6Network(u(str(network)))
                self.ipversion = 6
            except AddressValueError:
                raise ConfigError('invalid network: {}'.format(str(network)))


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
                params=self.params,
                ipv=self.ipversion)
        return self._rendered


class Host(object):
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
        self.address = self.Address(u(str(address)))

    def __repr__(self):
        return 'Host({0}: {1})'.format(self.name, self.address)


class IPv4Host(Host):

    Address = IPv4Address


class IPv6Host(Host):

    Address = IPv6Address


class Subnet(object):
    """
    Object representing a Subnet
    """
    def __init__(self, name, network, vlan=None, mtu=None):
        """
        Subnet object initialization

        args:
            name: subnet name
            network: Network address of the subnet
            vlan: optional vlan
        """
        self.name = name
        self.hosts = []
        self.vlan = vlan
        self.mtu = mtu
        self.network = self.Network(network, strict=False)

        if self.network.prefixlen >= self.net_max_prefixlen - 1:
            self.min_addr = self.network.network_address
            self.max_addr = self.network.broadcast_address
        else:
            self.min_addr = self.network.network_address + 1
            self.max_addr = self.network.broadcast_address - 1

        self.cur_addr = self.min_addr

        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)

    def nextip(self, prefixlen):
        if not self.net_min_prefixlen < prefixlen < self.net_max_prefixlen:
            raise ConfigError('invalid padding prefixlen: {0}'
                              .format(prefixlen))
        tmpnet = self.Network('{0}/{1}'.format(self.cur_addr, prefixlen),
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

        host = self.Host(name, addr)
        self.hosts.append(host)
        return host


    def __repr__(self):
        if self.vlan is not None:
            return 'Subnet({0}: {1}) [{2}]'.format(self.name, self.network,
                                                   self.vlan)
        else:
            return 'Subnet({0}: {1})'.format(self.name, self.network)


class IPv4Subnet(Subnet):

    Network = IPv4Network
    Host = IPv4Host
    net_min_prefixlen = 0
    net_max_prefixlen = 32


class IPv6Subnet(Subnet):

    Network = IPv6Network
    Host = IPv6Host
    net_min_prefixlen = 0
    net_max_prefixlen = 128


class Zone(object):

    def __init__(self, name, network, vrf=None, showfree=False):
        self.name = name
        self.network = self.Network(u(str(network)), strict=False)
        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)
        self.vrf = vrf
        self.showfree = showfree
        self.cur_addr = self.network.network_address
        self.subnets = []

    def get_next_network(self, prefixlen):
        """
        """
        try:
            network = self.Network('{0}/{1}'.format(self.cur_addr, prefixlen),
                                   strict=True)
        except ValueError:
            net1 = self.Network('{0}/{1}'.format(self.cur_addr, prefixlen),
                                strict=False)
            network = self.Network('{0}/{1}'.format(net1.network_address +
                                                    net1.num_addresses,
                                                    net1.prefixlen))
        return network

    def add_subnet(self, name, prefixlen, vlan=None, align=None, mtu=None):
        """
        Adds a subnet to this zone

        args:
            name: name of the subnet to be added
            prefixlen: prefix length of the subnet
            vlan: optional vlan number
        returns:
            the created Subnet object
        """
        if not self.net_min_prefixlen <= prefixlen <= self.net_max_prefixlen:
            raise ConfigError('subnet size must be between {0} and {1}'
                              .format(self.net_min_prefixlen, self.net_max_prefixlen))

        # align if asked
        if align is not None:
            network = self.get_next_network(align)
            self.cur_addr = network.network_address

        # if prefixlen is 0, subnet is shadow
        if prefixlen == 0:
            if name == '_':
                return None
            elif align is not None:
                network = self.get_next_network(align)
                subnet = self.Subnet(name, u(str(network)), vlan, mtu)
                self.subnets.append(subnet)
                return subnet
            else:
                raise ConfigError('zero-sized subnets must be named "_"')

        # looking for next subnet address
        network = self.get_next_network(prefixlen)

        # checking is subnet fits
        if (network.network_address < self.network.network_address or
            network.broadcast_address > self.network.broadcast_address):
                raise NetworkFull

        # checking for unaligned subnets
        if network.network_address > self.cur_addr:
            raise UnalignedSubnet('unaligned subnet "{0}" ({1}, '
                                  'should be {2})'
                                  .format(name, network, self.cur_addr))

        # shifting current address
        self.cur_addr = network.network_address + network.num_addresses

        if name == '_' and not self.showfree:
            return None

        # adding the subnet object
        subnet = self.Subnet(name, u(str(network)), vlan, mtu)
        self.subnets.append(subnet)
        return subnet

    def __repr__(self):
        return 'Zone({0}: {1}) [{2}]'.format(self.name, self.network, self.vrf)


class IPv4Zone(Zone):

    Network = IPv4Network
    Subnet = IPv4Subnet
    net_min_prefixlen = 0
    net_max_prefixlen = 32


class IPv6Zone(Zone):

    Network = IPv6Network
    Subnet = IPv6Subnet
    net_min_prefixlen = 0
    net_max_prefixlen = 128


class NetworkGenerator(object):

    topology_schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9-]+$'),
        Required('network'): Any(lambda x: str(IPv4Network(u(str(x)))),
                                 lambda x: str(IPv6Network(u(str(x))))),
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

    def __init__(self, data, showfree=False):
        self.showfree = showfree
        self.zones = []
        if isinstance(data, Topology):
            self.parse(data.data)
        else:
            self.parse(data)

    def parse(self, data):
        data = self.topology_schema(data)

        zone = self.add_zone(data['zone'], data['network'], data['vrf'],
                             showfree=self.showfree)

        for elt in data.get('subnets', []):
            try:
                subnet = zone.add_subnet(elt['name'], elt['size'],
                                         vlan=elt.get('vlan'),
                                         align=elt.get('align'),
                                         mtu=elt.get('mtu'))
                # catch UnalignedSubnet here for padding
                # fill for addfreesubnets
            except NetworkFull:
                raise NetworkFull('network full while adding subnet "{0}" '
                                  'to network {1} of zone "{2}"'
                                  .format(elt['name'], data['network'],
                                          data['zone']))

            for hostname in elt.get('hosts', []):
                try:
                    subnet.add_host(hostname)
                except NetworkFull:
                    raise NetworkFull('network full while adding host "{0}" '
                                      'to subnet "{1}" in network "{2}" '
                                      'of zone "{3}"'
                                      .format(hostname, elt['name'],
                                              data['network'], data['zone']))

        # fill the rest of the zone with empty networks
#        if self.showfree:
#            while zone.cur_addr < zone.network.broadcast_address:
#                for size in range(zone.network.prefixlen, 32):
#                    try:
#                        zone.add_subnet('_', size, 0, None, None)
#                        break
#                    except NetworkFull:
#                        pass
#                    except UnalignedSubnet:
#                        pass

    def add_zone(self, name, network, vrf=None, showfree=False):
        zone = self.Zone(name, network, vrf, showfree=showfree)
        self.zones.append(zone)
        return zone

    def render(self, template, loader, with_hosts=True):
        env = Environment(loader=loader, extensions=['jinja2.ext.do'])
        add_custom_filters(env)
        add_custom_functions(env)
        template = env.get_template('{0}.tpl'.format(template))
        return template.render(zones=self.zones,
                               ipv=self.ipversion,
                               with_hosts=with_hosts)


class IPv4NetworkGenerator(NetworkGenerator):

    Zone = IPv4Zone
    ipversion = 4


class IPv6NetworkGenerator(NetworkGenerator):

    Zone = IPv6Zone
    ipversion = 6


