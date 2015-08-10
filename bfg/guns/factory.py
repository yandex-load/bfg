from .http2 import HttpGun
from ..util import AbstractFactory
from ..module_exceptions import ConfigurationError


class GunFactory(AbstractFactory):
    FACTORY_NAME = 'gun'

    def get(self, key):
        if key in self.factory_config:
            return HttpGun(self.factory_config.get(key).get('target'))
        else:
            raise ConfigurationError(
                "Configuration for %s schedule not found" % key)
