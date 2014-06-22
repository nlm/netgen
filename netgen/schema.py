from voluptuous import Schema,Match,Required

class Validator(object):
    schema = Schema({
        Required('zone'): Match('^[A-Za-z0-9_-]+$'),
        Required('network'): Match('^[\d.]+/\d{2}$'),
        Required('subnets'): [{
            Required('subnet'): Match('^\w+$'),
            Required('size'): int,
            Required('hosts'): [
                str
            ]
        }]
    });

    def validate(self, data):
        return self.schema(data)
