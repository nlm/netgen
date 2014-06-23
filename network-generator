#!/usr/bin/env python
import sys
import argparse
import yaml
import voluptuous
import ipaddress
import netgen

def main():
    outplugins = {
        'text': netgen.output.Text,
        'bind': netgen.output.Bind,
    }
    ap = argparse.ArgumentParser(description='generate ip address plan')
    ap.add_argument('--zone', metavar='ZONE', type=str, required=True,
                    help='name of the zone to generate')
    ap.add_argument('--config', metavar='config.yaml',
                    type=str, default='config.yaml',
                    help='config file to use (default: config.yaml)')
    ap.add_argument('--output', metavar='|'.join(outplugins.keys()),
                    type=str, choices=outplugins.keys(), default='text',
                    help='output plugin to use')
    ap.add_argument('--vrf', metavar='VRF', type=str, default=None,
                    help='vrf to output (default: all)')
    args = ap.parse_args()

    with open(args.config) as config_fd:
        config = yaml.load(config_fd)
        schema = voluptuous.Schema({
            str: [{
                'vrf': str,
                'template': str,
                'network': lambda x: ipaddress.IPv4Network(unicode(x)),
            }]
        })
        try:
            schema(config)
        except voluptuous.MultipleInvalid as e:
            sys.exit("Error parsing config file: " + str(e))
        if args.zone not in config:
            sys.exit('zone "{}" does not exists'.format(args.zone))
        zone = config[args.zone]
        for vrf in zone:
            if args.vrf is not None and vrf['vrf'] != args.vrf:
                continue
            topology = netgen.Topology(args.zone, vrf['vrf'],
                                        vrf['network'], vrf['template'])
            try:
                netgen.NetworkGenerator(topology).output(outplugins[args.output])
            except voluptuous.MultipleInvalid as e:
                sys.exit("Error parsing input data: " + str(e))

if __name__ == '__main__':
    main()
