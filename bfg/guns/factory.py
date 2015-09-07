'''
Gun factory. Returns a gun of requested type
'''
#TODO: actually it doesn't for now
from .http2 import HttpMultiGun
from .scenario import ScenarioGun
from .spdy import SpdyMultiGun
from ..util import AbstractFactory
from ..module_exceptions import ConfigurationError


class GunFactory(AbstractFactory):
    FACTORY_NAME = 'gun'

    GUNS = {
        'http2': HttpMultiGun,
        'scenario': ScenarioGun,
        'spdy': SpdyMultiGun
    }

    def get(self, key):
        if key in self.factory_config:
            gun_config = self.factory_config.get(key)
            gun_type = gun_config.get('type')
            if gun_type in self.GUNS:
                return self.GUNS.get(gun_type)(gun_config)
            else:
                raise ConfigurationError(
                    "Gun type %s not found" % gun_type)
        else:
            raise ConfigurationError(
                "Configuration for %s gun not found" % key)
