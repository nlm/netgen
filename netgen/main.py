#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import sys
import os
import argparse
import yaml
from six import u
from voluptuous import Schema, MultipleInvalid
from ipaddress import IPv4Network
from jinja2 import FileSystemLoader
from . import IPv4NetworkGenerator, IPv4Topology

def main(arguments=None):
    parser = argparse.ArgumentParser(description='generate ip address plan')
    parser.add_argument('--data', '-d', metavar='DIR', type=str,
                        default='.',
                        help='the data directory (default: .)')
    parser.add_argument('--list-zones', action='store_true',
                        help='list the zones present in the config file')
    parser.add_argument('--zone', metavar='ZONE', type=str, required=True,
                        help='name of the zone to generate')
    parser.add_argument('--vrf', metavar='VRF', type=str, default=None,
                        help='vrf to output (default: all)')
    parser.add_argument('--output', metavar='TEMPLATE',
                        type=str, default='netgen',
                        help='output template to use')
    args = parser.parse_args(arguments)

    schema = Schema({
        str: [{
            'vrf': str,
            'template': str,
            'network': lambda x : str(IPv4Network(u(x)))
        }]
    })

    data_dir = args.data
    zones_file = '{0}/zones.yaml'.format(data_dir)
    topology_dir = '{0}/topology'.format(data_dir)
    output_dir = '{0}/output'.format(data_dir)

    if not os.path.isfile(zones_file):
        parser.error('file not found: {0}'.format(zones_file))

    for directory in [data_dir, topology_dir, output_dir]:
        if not os.path.isdir(directory):
            parser.error('directory not found: {0}'.format(directory))

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

    for vrf in zones[args.zone]:
        if args.vrf and vrf['vrf'] != args.vrf:
            continue
        topology = IPv4Topology(args.zone, vrf['vrf'], vrf['network'],
                            vrf['template'], topo_loader)
        try:
            IPv4NetworkGenerator(topology).render(args.output, output_loader)
        except MultipleInvalid as exception:
            sys.exit('error parsing input data: {0}'.format(exception))
