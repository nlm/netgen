#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import sys
import os
import argparse
import yaml
from six import u
from voluptuous import Schema, MultipleInvalid, Optional, Required, Extra, Any
from ipaddress import IPv4Network, IPv6Network
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from pkg_resources import resource_filename
from .engine import IPv4NetworkGenerator, IPv6NetworkGenerator, Topology
from .exception import NetworkFull, ConfigError, UnalignedSubnet

def parse_arguments(arguments):

    parser = argparse.ArgumentParser(description='generate ip address plan')
    parser.add_argument('--data', '-d', metavar='DIR', type=str,
                        help='the data directory (default: .)')
    parser.add_argument('--zone', '-z', metavar='ZONE', type=str,
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

    filters = parser.add_argument_group('filters')

    filters.add_argument('--vrf', '-v',  metavar='VRF', type=str, default=None,
                        help='only output zones in this vrf (default: all)')
    filters.add_argument('--network', '-n',  metavar='NETWORK', type=str, default=None,
                        help='only output zones using this network (default: all)')
    filters.add_argument('--topology', '-t',  metavar='TOPOLOGY', type=str, default=None,
                        help='only output zones using this template (default: all)')

    ipv_group = filters.add_mutually_exclusive_group()

    ipv_group.add_argument('--ipv4', '-4', action='store_true', default=False,
                           help='only output ipv4 entries')
    ipv_group.add_argument('--ipv6', '-6', action='store_true', default=False,
                           help='only output ipv6 entries')

    args = parser.parse_args(arguments)

    return args

def main(arguments=None):

    args = parse_arguments(arguments)

    schema = Schema({
        str: [{
            Required('vrf'): str,
            Required('topology'): str,
            Required('network'): Any(lambda x: str(IPv4Network(u(x))),
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

    if args.zone not in zones:
        sys.exit('zone "{0}" does not exists'.format(args.zone))

    topo_loader = FileSystemLoader(topology_dir)
    output_loader = FileSystemLoader(output_dirs)

    for subzone in zones[args.zone]:
        if args.vrf and subzone['vrf'] != args.vrf:
            continue

        if args.network and subzone['network'] != args.network:
            continue

        if args.topology and subzone['topology'] != args.topology:
            continue

        try:
            topology = Topology(args.zone, subzone['vrf'], subzone['network'],
                                subzone['topology'], loader=topo_loader,
                                params=subzone.get('params', {}))

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

            print(NetworkGenerator(topology,
                                   with_hosts=not args.without_hosts)
                  .render(args.output_template,
                          output_loader,
                          params=subzone.get('params', {})))

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
