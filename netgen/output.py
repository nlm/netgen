class Output(object):
    def output_zone(self, zone, params):
        pass

    def output_subnet(self, subnet, params):
        pass

    def output_host(self, host, params):
        pass

    def output(self, netgen, params):
        from . import NetworkGenerator
        if not isinstance(netgen, NetworkGenerator):
            raise "bad netgen"
        for zone in netgen.zones:
            self.output_zone(zone, params)
            for subnet in zone.subnets:
                self.output_subnet(subnet, params)
                for host in subnet.hosts:
                    self.output_host(host, params)

class Text(Output):
    def output_zone(self, zone, params):
        print(u'#' * 50)
        print(u'Zone {0} vrf {1}'.format(zone.name, zone.vrf))
        print(u'#' * 50)

    def output_subnet(self, subnet, params):
        print(u'Subnet {0}{1} is {2} in the vrf {3}'.format(
            subnet.zone.name,
            subnet.name,
            subnet.network,
            subnet.zone.vrf
        ))

    def output_host(self, host, params):
        print(u'  {0}{1} has address {2}'.format(
            host.subnet.zone.name,
            host.name,
            host.address,
        ))

class Bind(Output):
    def output_zone(self, zone, params=None):
        print(u'; Zone {0}'.format(zone.name))
        print(u'@ IN SOA ( XXX )')

    def output_subnet(self, subnet, params=None):
        print(u'; Subnet {0}{1} in vrf {2}'.format(
            subnet.zone.name,
            subnet.name,
            subnet.zone.vrf))

    def output_host(self, host, params=None):
        print(u'{0}{1} IN A {2}'.format(
            host.subnet.zone.name,
            host.name,
            host.address
        ))
