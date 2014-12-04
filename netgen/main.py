#!/usr/bin/env python
import sys
import argparse
import yaml
from voluptuous import Schema, MultipleInvalid
from ipaddress import IPv4Network
from netgen import NetworkGenerator, Topology
import netgen

def main():
    outplugins = {
        'text': netgen.output.Text,
        'bind': netgen.output.Bind,
    }

    ap = argparse.ArgumentParser(description='generate ip address plan')
    ap.add_argument('--config', metavar='config.yaml',
                    type=str, default='config.yaml',
                    help='config file to use (default: config.yaml)')
    ap.add_argument('--templates', metavar='DIR', type=str, default='templates',
                    help='the templates directory (default: templates)')
    ap.add_argument('--list-zones', action='store_true',
                    help='list the zones present in the config file')
    ap.add_argument('--zone', metavar='ZONE', type=str, default='',
                    help='name of the zone to generate')
    ap.add_argument('--vrf', metavar='VRF', type=str, default=None,
                    help='vrf to output (default: all)')
    ap.add_argument('--output', metavar='|'.join(outplugins.keys()),
                    type=str, choices=outplugins.keys(), default='text',
                    help='output plugin to use')
    args = ap.parse_args()

    schema = Schema({
        str: [{
            'vrf': str,
            'template': str,
            'network': lambda x : str(IPv4Network(x))
        }]
    })

    try:
        with open(args.config) as config_fd:
            config = schema(yaml.load(config_fd))
    except MultipleInvalid as e:
        sys.exit('error parsing config file: {0}'.format(e))
    except Exception as e:
        sys.exit('error: {0}'.format(e))

    if args.list_zones:
        print('\n'.join(config.keys()))
        sys.exit(0)

    if not args.zone:
        ap.error('no zone provided, use --zone ZONE')

    if args.zone not in config:
        sys.exit('zone "{0}" does not exists'.format(args.zone))

    for vrf in config[args.zone]:
        if args.vrf and vrf['vrf'] != args.vrf:
            continue
        topology = Topology(args.zone, vrf['vrf'], vrf['network'],
                            vrf['template'])
        try:
            NetworkGenerator(topology).output(outplugins[args.output])
        except MultipleInvalid as e:
            sys.exit('error parsing input data: {0}'.format(e))
