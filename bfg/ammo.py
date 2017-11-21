''' Ammo producers '''
from .util import get_opener, FactoryBase
from .module_exceptions import ConfigurationError
from .guns.http2 import Http2Ammo
import logging


logger = logging.getLogger(__name__)


class LineReader(object):

    ''' One line -- one missile '''

    def __init__(self, filename, **kwargs):
        self.filename = filename

    def __iter__(self):
        logger.info("LineReader. Using '%s' as ammo source", self.filename)
        with get_opener(self.filename)(self.filename, 'r') as ammo_file:
            while True:
                for line in ammo_file:
                    parts = line.rstrip('\r\n').split(maxsplit=1)
                    if len(parts) == 2:
                        yield (parts[1], parts[0])
                    elif len(parts) == 1:
                        yield ("", parts[0])
                    else:
                        raise RuntimeError("Unreachable branch")
                logger.debug("EOF. Restarting from the beginning")
                ammo_file.seek(0)


class Group(object):

    ''' Group missiles into batches '''

    def __init__(self, iterable, group_size):
        self.group_size = group_size
        self.iterable = iter(iterable)

    def __iter__(self):
        while True:
            yield (
                "multi-%s" % self.group_size,
                [next(self.iterable) for _ in range(self.group_size)])


class Http2AmmoProducer(object):

    ''' Create HTTP/2 missiles from data '''

    def __init__(self, iterable):
        self.iterable = iter(iterable)

    def __iter__(self):
        while True:
            ammo = next(self.iterable)
            yield Http2Ammo("GET", ammo, {}, None)


class AmmoFactory(FactoryBase):
    FACTORY_NAME = 'ammo'

    def get(self, key):
        '''
        Return a _new_ reader every time
        '''
        if key in self.factory_config:
            ammo_config = self.factory_config.get(key)
            ammo_reader = LineReader(self.factory_config.get(key).get("file"))
            batch_size = ammo_config.get("batch", 1)
            if batch_size > 1:
                ammo_reader = Group(ammo_reader, batch_size)
            return ammo_reader
        else:
            raise ConfigurationError(
                "Configuration for %s ammo not found" % key)
