from .http2 import HttpGun
from ..module_exceptions import ConfigurationError


class GunFactory(object):
    def __init__(self, config):
        self.config = config
        self.factory_config = self.config.get('gun')

    def get(self, key):
        if key in self.factory_config:
            return HttpGun(self.factory_config.get(key).get('target'))
        else:
            raise ConfigurationError(
                "Configuration for %s schedule not found" % key)
