from voluptuous import Schema,Match,Required
from ipaddress import IPv4Network

class Validator(object):
    schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9-]+$'),
        Required('network'): lambda x: IPv4Network(unicode(x)),
        Required('subnets'): [{
            Required('subnet'): Match('^[A-Za-z0-9-]+$'),
            Required('size'): int,
            Required('hosts'): [ str ]
        }]
    });

    def validate(self, data):
        return self.schema(data)
