#!/usr/bin/env python
import sys
import os
import argparse
import yaml
from voluptuous import Schema, MultipleInvalid
from ipaddress import IPv4Network
from netgen import NetworkGenerator, Topology
from jinja2 import FileSystemLoader
import netgen

def main():
    parser = argparse.ArgumentParser(description='generate ip address plan')
    parser.add_argument('-d', '--data-dir', metavar='DIR', type=str,
                        default='.',
                        help='the templates directory (default: ./templates)')
    parser.add_argument('--list-zones', action='store_true',
                        help='list the zones present in the config file')
    parser.add_argument('--zone', metavar='ZONE', type=str, default='',
                        help='name of the zone to generate')
    parser.add_argument('--vrf', metavar='VRF', type=str, default=None,
                        help='vrf to output (default: all)')
    parser.add_argument('--output', metavar='TEMPLATE',
                        type=str, default='netgen',
                        help='output template to use')
    args = parser.parse_args()

    schema = Schema({
        str: [{
            'vrf': str,
            'template': str,
            'network': lambda x : str(IPv4Network(x))
        }]
    })

    zones_file = '{0}/zones.yaml'.format(args.data_dir)
    templates_dir = '{0}/templates'.format(args.data_dir)

    for directory in [args.data_dir, templates_dir]:
        if not os.path.isdir(directory):
            parser.error('directory not found: {0}'.format(directory))

    if not os.path.isfile(zones_file):
        parser.error('file not found: {0}'.format(zones_file))

    try:
        with open(zones_file, 'r') as zones_fd:
            zones = schema(yaml.load(zones_fd))
    except MultipleInvalid as exception:
        sys.exit('error parsing config file: {0}'.format(exception))
    except Exception as exception:
        sys.exit('error: {0}'.format(exception))

    if args.list_zones:
        print('\n'.join(zones.keys()))
        sys.exit(0)

    if not args.zone:
        parser.error('no zone provided, use --zone ZONE')

    if args.zone not in zones:
        sys.exit('zone "{0}" does not exists'.format(args.zone))

    template_loader = FileSystemLoader('{}/templates'.format(args.data_dir))

    for vrf in zones[args.zone]:
        if args.vrf and vrf['vrf'] != args.vrf:
            continue
        topology = Topology(args.zone, vrf['vrf'], vrf['network'],
                            vrf['template'], template_loader)
        try:
            NetworkGenerator(topology).render(args.output, template_loader)
        except MultipleInvalid as exception:
            sys.exit('error parsing input data: {0}'.format(exception))
