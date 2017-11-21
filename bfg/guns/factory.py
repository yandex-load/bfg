'''
Gun factory. Returns a gun of requested type
'''
from .http2 import HttpMultiGun
from .ultimate import UltimateGun
from ..util import FactoryBase
from ..module_exceptions import ConfigurationError

import logging

logger = logging.getLogger(__name__)


class GunFactory(FactoryBase):
    FACTORY_NAME = 'gun'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.guns = {
            'http2': HttpMultiGun,
            'ultimate': UltimateGun,
        }
        try:
            from .spdy import SpdyMultiGun
            self.guns['spdy'] = SpdyMultiGun
        except ModuleNotFoundError:
            logger.info("Python spdylay library not found. SPDY module disabled")

    def get(self, key):
        if key in self.factory_config:
            gun_config = self.factory_config.get(key)
            gun_type = gun_config.get('type')
            if gun_type in self.guns:
                return self.guns.get(gun_type)(gun_config)
            else:
                raise ConfigurationError(
                    "Gun of type %s not found" % gun_type)
        else:
            raise ConfigurationError(
                "Configuration for %s gun not found" % key)
