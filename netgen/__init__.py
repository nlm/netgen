from __future__ import print_function, unicode_literals
from six import u
import sys
import yaml
from ipaddress import IPv4Network, IPv4Address
from jinja2 import Environment, FileSystemLoader
from voluptuous import Schema, Match, Required, Optional

class Topology(object):
    def __init__(self, zone, vrf, network, template,
                 loader=FileSystemLoader('templates')):
        env = Environment(loader=loader)
        self.template = env.get_template('{0}.yaml'.format(template))
        self.zone = zone
        self.vrf = vrf
        self.network = IPv4Network(u(network))
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


class NetworkGenerator(object):

    topology_schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9-]+$'),
        Required('network'): lambda x: str(IPv4Network(u(x))),
        Required('vrf'): Match('^[A-Za-z0-9-]+$'),
        Required('subnets'): [{
            Required('subnet'): Match('^[A-Za-z0-9-]+$'),
            Required('size'): int,
            Optional('vlan'): int,
            Optional('hosts'): [Match('^([A-Za-z0-9-]+|_)$')],
        }]
    })

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
        data = self.topology_schema(data)
        zone = self.add_zone(data['zone'], data['network'], data['vrf'])
        for elt in data.get('subnets', []):
            subnet = zone.add_subnet(elt['subnet'], elt['size'], elt.get('vlan'))
            for hostname in elt.get('hosts', []):
                subnet.add_host(hostname)

    def render(self, template, loader):
        env = Environment(loader=loader)
        template = env.get_template('{0}.tpl'.format(template))
        print(template.render(zones=self.zones))


class Zone(object):
    def __init__(self, name, network, vrf=None):
        self.name = name
        self.network = IPv4Network(u(network), strict=False)
        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)
        self.vrf = vrf
        self.cur_addr = self.network.network_address
        self.subnets = []

    def add_subnet(self, name, size, vlan=None):
        """
        Adds a subnet to this zone

        args:
            name: name of the subnet to be added
            size: size of the subnet
            vlan: optional vlan number
        returns:
            the created Subnet object
        """
        assert size <= 32
        subnet = Subnet(name, '{0}/{1}'.format(self.cur_addr, size), vlan)
        self.cur_addr += subnet.network.num_addresses
        self.subnets.append(subnet)
        return subnet

    def __repr__(self):
        return 'Zone({0}: {1}) [{2}]'.format(self.name, self.network, self.vrf)


class Subnet(object):
    """
    Object representing a Subnet
    """
    def __init__(self, name, network, vlan=None):
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
        self.network = IPv4Network(network, strict=False)
        self.cur_addr = self.network.network_address
        if network != str(self.network):
            print('warning: fixed {0} -> {1}'.format(network, self.network),
                  file=sys.stderr)

    def __repr__(self):
        if self.vlan is not None:
            return 'Subnet({0}: {1}) [{2}]'.format(self.name, self.network,
                                                   self.vlan)
        else:
            return 'Subnet({0}: {1})'.format(self.name, self.network)

    def add_host(self, name):
        """
        Adds a host to this subnet

        args:
            name: name of the host to be added
        returns:
            the created Host object
        """
        self.cur_addr += 1
        addr = self.cur_addr
        if addr not in self.network:
            raise Exception('subnet "{0}" full'.format(self.network))
        if name == '_':
            return None
        host = Host(name, addr)
        self.hosts.append(host)
        return host


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
        self.address = IPv4Address(address)

    def __repr__(self):
        return 'Host({0}: {1})'.format(self.name, self.address)
