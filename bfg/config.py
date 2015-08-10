import pytoml
from .module_exceptions import ConfigurationError
from .schedule import ScheduleFactory
from .ammo import AmmoFactory
from .guns import GunFactory
from .aggregator import AggregatorFactory
from .worker import BFGFactory
import logging


LOG = logging.getLogger(__name__)


class ComponentFactory(object):
    def __init__(self, config_filename, event_loop):
        self.event_loop = event_loop
        with open(config_filename, 'rb') as fin:
            self.config = pytoml.load(fin)
        self.factories = {
            'schedule': ScheduleFactory(self),
            'ammo': AmmoFactory(self),
            'gun': GunFactory(self),
            'bfg': BFGFactory(self),
            'aggregator': AggregatorFactory(self),
        }

    def get_config(self, factory):
        if factory in self.config:
            return self.config.get(factory)
        else:
            raise ConfigurationError("Config for '%s' not found" % factory)

    def get_factory(self, factory, key):
        if factory in self.factories:
            return self.factories.get(factory).get(key)
        else:
            raise ConfigurationError("Factory '%s' not found" % factory)
