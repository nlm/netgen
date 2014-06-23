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
        print u'#' * 50
        print u'Zone {} vrf {}'.format(zone.name, zone.vrf)
        print u'#' * 50

    def output_subnet(self, subnet, params):
        print u'Subnet {}{} is {} in the vrf {}'.format(
            subnet.zone.name,
            subnet.name,
            subnet.network,
            subnet.zone.vrf
        )

    def output_host(self, host, params):
        print u'  {}{} has address {}'.format(
            host.subnet.zone.name,
            host.name,
            host.address,
        )

class Bind(Output):
    def output_zone(self, zone, params=None):
        print u'; Zone {}'.format(zone.name)
        print u'@ IN SOA ( XXX )'

    def output_subnet(self, subnet, params=None):
        print u'; Subnet {}{} in vrf {}'.format(
            subnet.zone.name,
            subnet.name,
            subnet.zone.vrf)

    def output_host(self, host, params=None):
        print u'{}{} IN A {}'.format(
            host.subnet.zone.name,
            host.name,
            host.address
        )
