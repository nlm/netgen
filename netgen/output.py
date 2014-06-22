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
        print u'Zone {}'.format(zone.name)
        print u'#' * 50

    def output_subnet(self, subnet, params):
        print u'Subnet {}{} is {}'.format(
            subnet.zone.name,
            subnet.name,
            subnet.network,
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
        print u'; Subnet {}{}'.format(subnet.zone.name, subnet.name)

    def output_host(self, host, params=None):
        print u'{}{}-{} IN A {}'.format(
            host.subnet.zone.name,
            host.subnet.name,
            host.name,
            host.address
        )
