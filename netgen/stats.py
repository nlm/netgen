from __future__ import division
import argparse
import json
import ipaddr
from ipaddress import IPv4Network
import sys


class Analyzer(object):

    def analyze(self, data, verbose=False):
        total_used = total_nused = total_avail = 0
        if not data:
            return
        for zone in data:
            (used, nused, avail) = self.analyze_zone(zone, verbose)
            total_used += used
            total_nused += nused
            total_avail += avail
        print('=> {} networks: {} used ({:.02f}% hosts / {:.02f}% net), '
              '{} wasted ({:.02f}% hosts / {:.02f}% net), {} total'
              .format(len(data),
                      total_used,
                      total_used / total_avail * 100,
                      total_nused / total_avail * 100,
                      total_avail - total_used,
                      (total_avail - total_used) / total_avail * 100,
                      (total_avail - total_nused) / total_avail * 100,
                      total_avail))

    def analyze_zone(self, zone, verbose=False):
        supernet = IPv4Network(zone['network'])
        supernet_hosts = supernet.num_addresses
        subnets_hosts = sum([IPv4Network(subnet['network']).num_addresses
                            for subnet in zone['subnets'] if 'hosts' in subnet])
        print('network {}: {}/{} netspace used ({:.02f}%)'
              .format(supernet, subnets_hosts,
                      supernet_hosts, subnets_hosts / supernet_hosts * 100))
        used_hosts = 0
        last_subnet = None
        for subnet in zone['subnets']:
            #if last_subnet is not None and subnet.subnet_of(last_subnet):
            #    continue
            used_hosts += self.analyze_subnet(subnet, verbose)
            last_subnet = subnet
        print('-> {}: {}/{} ({:.02f}%) really used, {} wasted\n'
              .format(supernet, used_hosts, supernet_hosts,
                      used_hosts / supernet_hosts * 100,
                      supernet_hosts - used_hosts))
        return (used_hosts, subnets_hosts, supernet_hosts)

    def analyze_subnet(self, subnet, verbose=False):
        subnet_obj = IPv4Network(subnet['network'])
        subnet_hosts_max = subnet_obj.num_addresses
        subnet_hosts = len(subnet.get('hosts', []))
        if not subnet_hosts:
            return 0
        if verbose:
            print('  - {}: {}/{} used ({:.02f}%)'
                  .format(subnet_obj, subnet_hosts, subnet_hosts_max,
                          subnet_hosts / subnet_hosts_max * 100))
        return subnet_hosts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        default=False)
    parser.add_argument('filename', nargs='?',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='netgen json data file name')
    args = parser.parse_args()
    try:
        data = json.load(args.filename)
    except ValueError as err:
        print('error loading file: {}'.format(err))

    Analyzer().analyze(data, args.verbose)
