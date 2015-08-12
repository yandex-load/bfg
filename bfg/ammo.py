from .util import get_opener, AbstractFactory
from .module_exceptions import ConfigurationError
from .worker import Task
import logging


LOG = logging.getLogger(__name__)


class LineReader(object):

    ''' One line -- one missile '''

    def __init__(self, filename, **kwargs):
        self.filename = filename

    def __iter__(self):
        LOG.info("LineReader. Using '%s' as ammo source", self.filename)
        with get_opener(self.filename)(self.filename, 'r') as ammo_file:
            while True:
                for line in ammo_file:
                    yield (None, line.rstrip('\r\n'))
                LOG.debug("EOF. Restarting from the beginning")
                ammo_file.seek(0)


class Group(object):
    def __init__(self, iterable, group_size):
        self.group_size = group_size
        self.iterable = iter(iterable)

    def __iter__(self):
        while True:
            yield (
                "multi-%s" % self.group_size,
                [next(self.iterable) for _ in range(self.group_size)])


class AmmoFactory(AbstractFactory):
    FACTORY_NAME = 'ammo'

    def get(self, key):
        if key in self.factory_config:
            return Group(
                LineReader(self.factory_config.get(key).get("file")), 10)
        else:
            raise ConfigurationError(
                "Configuration for %s ammo not found" % key)
