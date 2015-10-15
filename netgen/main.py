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
from .engine import IPv4NetworkGenerator, IPv6NetworkGenerator, Topology
from .exception import NetworkFull, ConfigError, UnalignedSubnet

def parse_arguments(arguments):

    parser = argparse.ArgumentParser(description='generate ip address plan')
    parser.add_argument('--data', '-d', metavar='DIR', type=str,
                        default='.', help='the data directory (default: .)')
    parser.add_argument('--zone', '-z', metavar='ZONE', type=str,
                        required=True, help='name of the zone to generate')
    parser.add_argument('--vrf', '-v',  metavar='VRF', type=str, default=None,
                        help='vrf to output (default: all)')
#    parser.add_argument('--free', '-f', action='store_true', default=False,
#                        help='output free networks')
    parser.add_argument('--without-hosts', '-H', action='store_true',
                        default=False, help='hide hosts')
    parser.add_argument('--output-template', '-o', metavar='TEMPLATE',
                        type=str, default='netgen',
                        help='output template to use')
    parser.add_argument('--dump-topology', action='store_true', default=False,
                        help='dump the rendered topology instead')
    return parser.parse_args(arguments)


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

    data_dir = args.data
    zones_file = '{0}/zones.yaml'.format(data_dir)
    topology_dir = '{0}/topology'.format(data_dir)
    output_dir = '{0}/output'.format(data_dir)

    if not os.path.isfile(zones_file):
        parser.error('file not found: {0}'.format(zones_file))

    for directory in [data_dir, topology_dir, output_dir]:
        if not os.path.isdir(directory):
            parser.error('directory not found: {0}'.format(directory))

    # Parsing Zone file

    try:
        with open(zones_file, 'r') as zones_fd:
            zones = schema(yaml.load(zones_fd))
    except MultipleInvalid as exception:
        sys.exit('error parsing zone file: {0}'.format(exception))
    except Exception as exception:
        sys.exit('error: {0}'.format(exception))

    if args.zone not in zones:
        sys.exit('zone "{0}" does not exists'.format(args.zone))

    topo_loader = FileSystemLoader(topology_dir)
    output_loader = FileSystemLoader(output_dir)

    for subzone in zones[args.zone]:
        if args.vrf and subzone['vrf'] != args.vrf:
            continue

        try:
            topology = Topology(args.zone, subzone['vrf'], subzone['network'],
                                subzone['topology'], loader=topo_loader,
                                params=subzone.get('params'))

            if args.dump_topology is True:
                print('# topology: {0}\n'.format(subzone['topology']))
                print(topology)
                continue

            if topology.ipversion == 4:
                NetworkGenerator = IPv4NetworkGenerator
            elif topology.ipversion == 6:
                NetworkGenerator = IPv6NetworkGenerator

            print(NetworkGenerator(topology,
                                   showfree=False)
                  .render(args.output_template,
                          output_loader,
                          not args.without_hosts)
                  .encode('utf-8'))

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
