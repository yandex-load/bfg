'''
Utilities: parsers, converters, etc.
'''
import re
import logging
from itertools import islice
from .module_exceptions import ConfigurationError
import math
import gzip
import yaml
import logging


LOG = logging.getLogger(__name__)


def take(number, iter):
    return list(islice(iter, 0, number))


def parse_duration(duration):
    '''
    Parse duration string, such as '3h2m3s' into milliseconds

    >>> parse_duration('3h2m3s')
    10923000

    >>> parse_duration('0.3s')
    300

    >>> parse_duration('5')
    5000
    '''
    _re_token = re.compile("([0-9.]+)([dhms]?)")

    def parse_token(time, multiplier):
        multipliers = {
            'h': 3600,
            'm': 60,
            's': 1,
        }
        if multiplier:
            if multiplier in multipliers:
                return int(float(time) * multipliers[multiplier] * 1000)
            else:
                raise ConfigurationError(
                    'Failed to parse duration: %s' % duration)
        else:
            return int(float(time) * 1000)

    return sum(parse_token(*token) for token in _re_token.findall(duration))


def solve_quadratic(a, b, c):
    '''
    >>> solve_quadratic(1.0, 2.0, 1.0)
    (-1.0, -1.0)
    '''
    disc_root = math.sqrt((b * b) - 4 * a * c)
    root1 = (-b - disc_root) / (2 * a)
    root2 = (-b + disc_root) / (2 * a)
    return (root1, root2)


def s_to_ms(f_sec):
    return int(f_sec * 1000.0)


def get_opener(f_path):
    """ Returns opener function according to file extensions:
        bouth open and gzip.open calls return fileobj.

    Args:
        f_path: str, ammo file path.

    Returns:
        function, to call for file open.
    """
    if f_path.endswith('.gz'):
        logging.info("Using gzip opener")
        return gzip.open
    else:
        return open


class AbstractFactory(object):
    FACTORY_NAME = ""

    def __init__(self, component_factory):
        if not self.FACTORY_NAME:
            raise TypeError(
                "Trying to create an abstract class"
                " or did not redefine FACTORY_NAME")
        self.component_factory = component_factory
        self.config = component_factory.config
        self.event_loop = component_factory.event_loop
        self.factory_config = self.config.get(self.FACTORY_NAME)
        LOG.info(
            "%s factory config:\n%s", self.FACTORY_NAME,
            yaml.safe_dump(self.factory_config))

    def get(self, key):
        raise NotImplementedError("Calling method from abstract class")
