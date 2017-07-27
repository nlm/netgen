from colors import color
from functools import partial
from jinja2.exceptions import TemplateRuntimeError
import math
from math import log, ceil
from six.moves import xrange

class TemplateUtils(object):

    def __init__(self, ipversion):
        if ipversion not in (4, 6):
            raise ValueError('ipversion must be 4 or 6')
        self.function_ip46 = partial(self.ipver, ipversion)
        self.function_minpref = partial(self.minpref, ipversion)

    @property
    def ipversion(self):
        '''
        ipversion() -> int
        Returns the ip version for which this class is instantiated
        '''
        return self._ipversion

    @staticmethod
    def ipver(ipversion, valuev4, valuev6):
        if ipversion == 4:
            return valuev4
        elif ipversion == 6:
            return valuev6
        else:
            raise ValueError('invalid value for ipversion: {0}'
                             .format(ipversion))

    @staticmethod
    def filter_dotreverse(value, sep=None):
        '''
        filter_dot_reverse('1.2.3.4.5') -> '5.4.3.2.1'
        Reverses a dotted string
        '''
        if sep is None:
            sep = '.'
        return sep.join(reversed(str(value).split(sep)))

    @staticmethod
    def filter_colored(text, fg, bg=None, style=None):
        try:
            return color(text, fg=fg, bg=bg, style=style)
        except Exception as exc:
            raise TemplateRuntimeError(exc)

    @staticmethod
    def minpref(ipversion, host_count):
        if ipversion == 4:
            return 32 - int(ceil(log(host_count, 2)))
        elif ipversion == 6:
            return 128 - int(ceil(log(host_count, 2)))
        else:
            raise ValueError('invalid value for ipversion: {0}'
                             .format(ipversion))

    @staticmethod
    def function_orange(*args, **kwargs):
        offset = int(kwargs.get('offset', 0))
        return [i + offset for i in range(*args)]

    @staticmethod
    def function_xorange(*args, **kwargs):
        offset = int(kwargs.get('offset', 0))
        return (i + offset for i in xrange(*args))

    @classmethod
    def function_range1(cls, *args, **kwargs):
        return cls.function_orange(*args, offset=1, **kwargs)

    @classmethod
    def function_xrange1(cls, *args, **kwargs):
        return cls.function_xorange(*args, offset=1, **kwargs)

    @staticmethod
    def function_raise(message):
        raise TemplateRuntimeError(message)

    @staticmethod
    def function_assert(expr, message):
        if not expr:
            raise TemplateRuntimeError(message)

    # Setup the environment

    def add_custom_filters(self, env):
        for name in ('colored', 'dotreverse'):
            env.filters[name] = getattr(self, 'filter_{0}'.format(name))

    def add_custom_functions(self, env):
        for name in ('assert', 'ip46', 'minpref', 'raise'):
            env.globals[name] = getattr(self, 'function_{0}'.format(name))
        env.globals['range'] = self.function_xorange
        env.globals['range1'] = self.function_xrange1

        math.int = int
        math.float = float
        math.round = round
        math.min = min
        math.max = max
        env.globals['math'] = math

    def setup_environment(self, env):
        self.add_custom_functions(env)
        self.add_custom_filters(env)
        return env
