#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import sys
import os
import argparse
import json
import re
import yaml
from six import u
from voluptuous import Schema, MultipleInvalid, Optional, Required, Extra, Any
from ipaddress import IPv4Network, IPv6Network
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from pkg_resources import resource_filename
from .engine import IPv4NetworkGenerator, IPv6NetworkGenerator, Topology
from .exception import NetworkFull, ConfigError, UnalignedSubnet

def flatten(l):
    return [item for y in l for item in (y if type(y) == list or
                                         type(y) == tuple else [y])]

def auto_convert_value(value):
    if value == 'true':
        return True
    elif value == 'false':
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value

def auto_convert_network(network_address):
    try:
        return IPv4Network(u(network_address))
    except:
        pass
    try:
        return IPv6Network(u(network_address))
    except:
        pass
    raise ValueError(network_address)

def regular_expression(pattern):
    try:
        return re.compile(pattern)
    except:
        raise ValueError(pattern)

def parse_arguments(arguments):

    parser = argparse.ArgumentParser(description='generate ip address plan')
    parser.add_argument('--data', '-d', metavar='DIR', type=str,
                        help='the data directory (default: .)')
    parser.add_argument('--zone', '-z', metavar='ZONE', type=str,
                        action='append',
                        required=True, help='name of the zone to generate')
    parser.add_argument('--without-hosts', '-H', action='store_true',
                        default=False, help='hide hosts')
    parser.add_argument('--output-template', '-o', metavar='TEMPLATE',
                        type=str, default='netgen',
                        help='output template to use for rendering')
    parser.add_argument('--dump-topology', action='store_true', default=False,
                        help=('dump the intermediate topology'
                              ' instead of regular output'))
    parser.add_argument('--debug', action='store_true', default=False,
                        help='don\'t catch exceptions')
    parser.add_argument('--with-param', '-p', action='append', nargs=2,
                        default=[], help='override network params')

    filters = parser.add_argument_group('filters')

    filters.add_argument('--vrf', '-v',  metavar='VRF', type=str, default=None,
                        action='append',
                        help='only output zones in this vrf (default: all)')
    filters.add_argument('--network', '-n',  metavar='NETWORK', type=str,
                        default=None, action='append',
                        help='only output network using this address (default: all)')
    filters.add_argument('--in-network', '-N',  metavar='NETWORK', type=str,
                        default=None, action='append',
                        help='only output networks contained in this network (default: all)')
    filters.add_argument('--topology', '-t',  metavar='TOPOLOGY', type=str,
                        default=None, action='append',
                        help='only output networks using this template (default: all)')
    filters.add_argument('--match-topology', '-T',  metavar='TOPOLOGY',
                        default=None, action='append', type=regular_expression,
                        help='only output networks matching this template (default: all)')

    ipv_group = filters.add_mutually_exclusive_group()

    ipv_group.add_argument('--ipv4', '-4', action='store_true', default=False,
                           help='only output ipv4 entries')
    ipv_group.add_argument('--ipv6', '-6', action='store_true', default=False,
                           help='only output ipv6 entries')

    args = parser.parse_args(arguments)

    params = {}
    for key, value in args.with_param:
        params.update({key: auto_convert_value(value)})
    args.params = params

    return args

def main(arguments=None):

    args = parse_arguments(arguments)

    schema = Schema({
        str: [{
            Required('vrf'): str,
            Required('topology'): str,
            Required('network'): Any([Any(lambda x: str(IPv4Network(u(x))),
                                           lambda x: str(IPv6Network(u(x))))],
                                     lambda x: str(IPv4Network(u(x))),
                                     lambda x: str(IPv6Network(u(x)))),
            Optional('params'): {Extra: object},
        }]
    })

    # Check for required files and directories

    if args.data is not None:
        data_dir = args.data
    else:
        data_dir = os.environ.get('NETGEN_DATA_DIR', '.')
    zones_file = '{0}/zones.yaml'.format(data_dir)
    topology_dir = '{0}/topology'.format(data_dir)

    output_dirs = []
    local_output_dir = '{0}/output'.format(data_dir)
    if os.path.isdir(local_output_dir):
        output_dirs.append(local_output_dir)
    output_dirs.append(resource_filename(__name__, 'templates'))

    if not os.path.isfile(zones_file):
        sys.exit('file not found: {0}'.format(zones_file))

    for directory in [data_dir, topology_dir]:
        if not os.path.isdir(directory):
            sys.exit('directory not found: {0}'.format(directory))

    # Parsing Zone file

    try:
        with open(zones_file, 'r') as zones_fd:
            zones = schema(yaml.safe_load(zones_fd))
    except MultipleInvalid as exception:
        if args.debug:
            raise
        sys.exit('error parsing zone file: {0}'.format(exception))
    except Exception as exception:
        if args.debug:
            raise
        sys.exit('error: {0}'.format(exception))

    for zone in args.zone:
        if zone not in zones:
            sys.exit('zone "{0}" does not exists'.format(zone))

    topo_loader = FileSystemLoader(topology_dir)
    output_loader = FileSystemLoader(output_dirs)

    for zone in args.zone:
        for subzone in zones[zone]:
            for network in flatten([subzone['network']]):
                # only output networks in the specified vrf
                if args.vrf and subzone['vrf'] not in args.vrf:
                    continue

                # check if exactly matching the network address
                if args.network and network not in args.network:
                    continue

                # continue if not a subnet of a selected network
                if args.in_network:
                    subzone_network = auto_convert_network(network)
                    for network_address in args.in_network:
                        wanted_network = auto_convert_network(network_address)
                        if (type(wanted_network) == type(subzone_network)
                            and subzone_network.subnet_of(wanted_network)):
                            break
                    else:
                        continue

                # only output networks using this topology
                if args.topology and subzone['topology'] not in args.topology:
                    continue

                # continue if topology does not match patterns
                if args.topology:
                    for regexp in args.match_topology:
                        if regexp.match(subzone['topology']):
                            break
                    else:
                        continue

                try:
                    params = subzone.get('params', {}).copy()
                    params.update(args.params)

                    topology = Topology(zone, subzone['vrf'],
                                        network, subzone['topology'],
                                        loader=topo_loader,
                                        params=params)

                    if ((args.ipv4 is True and topology.ipversion != 4) or
                        (args.ipv6 is True and topology.ipversion != 6)):
                            continue

                    if args.dump_topology is True:
                        print('# topology: {0}\n'.format(subzone['topology']))
                        print(topology)
                        continue

                    if topology.ipversion == 4:
                        NetworkGenerator = IPv4NetworkGenerator
                    elif topology.ipversion == 6:
                        NetworkGenerator = IPv6NetworkGenerator
                    else:
                        raise AssertionError

                    ngen = NetworkGenerator(topology,
                                            with_hosts=not args.without_hosts)


                    ngen.stream(args.output_template,
                                output_loader, sys.stdout,
                                params=params)

                except MultipleInvalid as exception:
                    sys.exit('error parsing topology: {0}'.format(exception))
                except TemplateNotFound as exception:
                    sys.exit('template not found: {0}'.format(exception))
                except NetworkFull as exception:
                    sys.exit('network full: {0}'.format(exception))
                except ConfigError as exception:
                    sys.exit('config error: {0}'.format(exception))
                except UnalignedSubnet as exception:
                    sys.exit('unaligned subnet: {0}'.format(exception))
                except IOError as exception:
                    sys.exit('io error: {0}'.format(exception))


if __name__ == '__main__':
    main()
