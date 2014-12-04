from voluptuous import Schema, Match, Required, Optional
from ipaddress import IPv4Network

class Validator(object):

    schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9-]+$'),
        Required('network'): lambda x: str(IPv4Network(x)),
        Required('vrf'): Match('^[A-Za-z0-9-]+$'),
        Required('subnets'): [{
            Required('subnet'): Match('^[A-Za-z0-9-]+$'),
            Required('size'): int,
            Optional('hosts'): [Match('^[A-Za-z0-9-]+$')]
        }]
    })

    def validate(self, data):
        return self.schema(data)
