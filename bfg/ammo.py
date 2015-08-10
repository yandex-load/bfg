from .util import get_opener, AbstractFactory
from .module_exceptions import ConfigurationError
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
                    yield (line.rstrip('\r\n'), None)
                LOG.debug("EOF. Restarting from the beginning")
                ammo_file.seek(0)


class AmmoFactory(AbstractFactory):
    FACTORY_NAME = 'ammo'

    def get(self, key):
        if key in self.factory_config:
            return LineReader(self.factory_config.get(key).get("file"))
        else:
            raise ConfigurationError(
                "Configuration for %s ammo not found" % key)
