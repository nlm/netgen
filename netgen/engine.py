from __future__ import print_function
from ipaddress import IPv4Network, IPv4Address
from ipaddress import IPv6Network, IPv6Address
from ipaddress import AddressValueError
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import re
from six import u
import sys
from voluptuous import Schema, Match, Required, Optional, MultipleInvalid, Any
import yaml
try:
    from yaml import CSafeLoader as YAMLLoader, CSafeDumper as YAMLDumper
except ImportError:
    from yaml import SafeLoader as YAMLLoader, SafeDumper as YAMLDumper

from .exception import NetworkFull, ConfigError, UnalignedSubnet
from .templateutils import TemplateUtils


class Topology(object):

    def __init__(self, zone, vrf, network, template,
                 params=None, loader=None):

        try:
            self.network = IPv4Network(u(str(network)))
            self.ipversion = 4
        except AddressValueError:
            try:
                self.network = IPv6Network(u(str(network)))
                self.ipversion = 6
            except AddressValueError:
                raise ConfigError('invalid network: {}'.format(str(network)))

        if loader is None:
            loader = FileSystemLoader('templates')
        env = Environment(loader=loader,
                          undefined=StrictUndefined,
                          extensions=['jinja2.ext.do',
                                      'jinja2.ext.loopcontrols'])
        TemplateUtils(self.ipversion).setup_environment(env)

        self.template = env.get_template('{0}.yaml'.format(template))
        self.zone = zone
        self.vrf = vrf
        self.params = params if params is not None else {}
        self._rendered = None
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = yaml.load(self.rendered, Loader=YAMLLoader)
        return self._data

    @property
    def rendered(self):
        if self._rendered is None:
            self._rendered = self.template.render(zone=self.zone,
                                                  vrf=self.vrf,
                                                  network=self.network,
                                                  params=self.params,
                                                  ipv=self.ipversion)
        return self._rendered

    def __str__(self):
        return self.rendered


class Host(object):
    """
    Object representing a Host
    """
    valid_statuses = ('reserved', 'active', 'deprecated')

    def __init__(self, name, address, status='active', hostvars=None):
        """
        Host object initialization

        args:
            name: hostname
            address: IP address of the host
        """
        self.name = name
        self.address = self.Address(u(str(address)))
        if status not in self.valid_statuses:
            raise ValueError('{0} is not a valid status'.format(status))
        self.status = status
        self.vars = hostvars or dict()

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
    valid_statuses = ('reserved', 'active', 'deprecated')

    def __init__(self, name, network, vlan=None, mtu=None, shadow=False,
                 status='active'):
        """
        Subnet object initialization

        args:
            name: subnet name
            network: Network address of the subnet
            vlan: optional vlan
        """
        self.name = name
        if status not in self.valid_statuses:
            raise ValueError('{0} is not a valid status'.format(status))
        self.status = status
        self.hosts = []
        self.vlan = vlan
        self.mtu = mtu
        self.shadow = shadow
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

#        if (self.ip_version == 6 and not shadow
#            and 127 > self.network.prefixlen > 64):
#            print('warning: use of ipv6 prefix length '
#                  'larger than 64 ({0}: {1}) is discouraged '
#                  '(except 127,128)'.format(name, self.network.prefixlen),
#                  file=sys.stderr)

    def get_next_ip(self, prefixlen):
        if not self.net_min_prefixlen < prefixlen < self.net_max_prefixlen:
            raise ConfigError('invalid padding prefixlen: {0}'
                              .format(prefixlen))
        tmpnet = self.Network(u('{0}/{1}'.format(self.cur_addr, prefixlen)),
                             strict=False)
        return tmpnet.network_address + tmpnet.num_addresses + 1


    def add_host(self, name, hostvars=None):
        """
        Adds a host to this subnet

        Uses prefixes to determine the status of the host
        none = active
        ? = reserved
        ! = deprecated

        args:
            name: name of the host to be added
        returns:
            the created Host object
        """
        if self.shadow is True:
            raise ConfigError('cannot add host "{0}" to zero-sized subnet "{1}"'
                              .format(name, self.name))
        addr = self.cur_addr
        if addr not in self.network or addr > self.max_addr:
            raise NetworkFull
        self.cur_addr += 1
        # check for special directives
        if name == '_':
            return None
        match = re.match(r'^_/(\d+)$', name)
        if match:
            self.cur_addr = self.get_next_ip(int(match.group(1)))
            return None

        if name.startswith('?'):
            status = 'reserved'
            name = name[1:]
        elif name.startswith('!'):
            status = 'deprecated'
            name = name[1:]
        else:
            status = 'active'

        host = self.Host(name, addr, status=status, hostvars=hostvars)
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
    ip_version = 4


class IPv6Subnet(Subnet):

    Network = IPv6Network
    Host = IPv6Host
    net_min_prefixlen = 0
    net_max_prefixlen = 128
    ip_version = 6


class Zone(object):
    """
    Object representing a Zone
    A Zone is associated to a VRF and contains subnets
    derived from a network address
    """

    def __init__(self, name, network, vrf=None):
        self.name = name
        self.network = self.Network(u(str(network)), strict=False)
        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)
        self.vrf = vrf
        self.cur_addr = self.network.network_address
        self.subnets = []

    def get_next_subnet(self, prefixlen):
        """
        Calculates the next subnet address according to the prefixlen

        args:
            prefixlen: prefix length of the subnet
        returns:
            a Network object
        """
        try:
            network = self.Network(u('{0}/{1}'.format(self.cur_addr, prefixlen)),
                                   strict=True)
        except ValueError:
            net1 = self.Network(u('{0}/{1}'.format(self.cur_addr, prefixlen)),
                                strict=False)
            network = self.Network(u('{0}/{1}'.format(net1.network_address +
                                                    net1.num_addresses,
                                                    net1.prefixlen)))
        return network

    def add_subnet(self, name, prefixlen, vlan=None, align=None, mtu=None):
        """
        Adds a subnet to this zone

        Uses prefixes to determine the status of the host
        none = active
        ? = reserved
        ! = deprecated

        args:
            name: name of the subnet to be added
            prefixlen: prefix length of the subnet
            vlan: optional vlan number
        returns:
            the created Subnet object
        """
        if not self.net_min_prefixlen <= prefixlen <= self.net_max_prefixlen:
            raise ConfigError('subnet size must be between {0} and {1}'
                              .format(self.net_min_prefixlen,
                                      self.net_max_prefixlen))

        # align if asked
        if align is not None:
            network = self.get_next_subnet(align)
            self.cur_addr = network.network_address

        # define status
        if name.startswith('?'):
            status = 'reserved'
            name = name[1:]
        elif name.startswith('!'):
            status = 'deprecated'
            name = name[1:]
        else:
            status = 'active'

        # if prefixlen is 0, subnet is shadow
        if prefixlen == 0:
            if name == '_':
                return None
            elif align is not None:
                network = self.get_next_subnet(align)
                subnet = self.Subnet(name, u(str(network)), vlan,
                                     mtu, shadow=True, status=status)
                self.subnets.append(subnet)
                return subnet
            else:
                raise ConfigError('zero-sized subnets must be named "_"')

        # looking for next subnet address
        network = self.get_next_subnet(prefixlen)

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

        if name == '_':
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
            Required('name'): Match('^([!?]?[A-Za-z0-9-]+|_)$'),
            Required('size'): int,
            Optional('vlan'): int,
            Optional('align'): int,
            Optional('mtu'): int,
            Optional('hosts'): [
                Or(Match('^([!?]?[A-Za-z0-9-]+|_(/\d+)?)$'),
                   Match({'name': '^([!?]?[A-Za-z0-9-]+|_(/\d+)?)$',
                          'vars': {str: Or(int, str, bool)}})
            )],
        }]
    })

    def __init__(self, data, with_hosts=True):
        self.zones = []
        self.with_hosts = with_hosts
        if isinstance(data, Topology):
            self.parse(data.data)
        else:
            self.parse(data)

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
                raise NetworkFull('network full while adding subnet "{0}" '
                                  'to network {1} of zone "{2}"'
                                  .format(elt['name'], data['network'],
                                          data['zone']))

            if not self.with_hosts:
                continue

            for host in elt.get('hosts', []):
                if issubclass(host, dict):
                    hostname = host['name']
                    hostvars = host['vars']
                else:
                    hostname = host
                    hostvars = None
                try:
                    subnet.add_host(hostname, hostvars=hostvars)
                except NetworkFull:
                    raise NetworkFull('network full while adding host "{0}" '
                                      'to subnet "{1}" in network "{2}" '
                                      'of zone "{3}"'
                                      .format(hostname, elt['name'],
                                              data['network'], data['zone']))

    def add_zone(self, name, network, vrf=None):
        zone = self.Zone(name, network, vrf)
        self.zones.append(zone)
        return zone

    def render(self, template, loader, params=None):
        env = Environment(loader=loader, extensions=['jinja2.ext.do'])
        TemplateUtils(self.ipversion).setup_environment(env)
        template = env.get_template('{0}.tpl'.format(template))
        return template.render(zones=self.zones,
                               ipv=self.ipversion,
                               params=(params or {}))

    def stream(self, template, loader, output_file, params=None):
        env = Environment(loader=loader,
                          extensions=['jinja2.ext.do'],
                          keep_trailing_newline=True)
        TemplateUtils(self.ipversion).setup_environment(env)
        template = env.get_template('{0}.tpl'.format(template))
        template.stream(zones=self.zones,
                        ipv=self.ipversion,
                        params=(params or {})).dump(output_file)


class IPv4NetworkGenerator(NetworkGenerator):

    Zone = IPv4Zone
    ipversion = 4


class IPv6NetworkGenerator(NetworkGenerator):

    Zone = IPv6Zone
    ipversion = 6


