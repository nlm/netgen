import argparse
import sys
import yaml
import json

def yaml2json():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='the yaml input file name')
    parser.add_argument('output', nargs='?',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='the json output file name')
    args = parser.parse_args()
    json.dump(yaml.safe_load(args.input), args.output)

def json2yaml():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='the json input file name')
    parser.add_argument('output', nargs='?',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='the yaml output file name')
    args = parser.parse_args()
    yaml.safe_dump(json.load(args.input), args.output)
