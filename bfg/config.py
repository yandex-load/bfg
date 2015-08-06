import pytoml
from .module_exceptions import ConfigurationError
from .schedule import ScheduleFactory
from .ammo import AmmoFactory
from .guns import GunFactory
from .aggregator import AggregatorFactory
from .worker import BFGFactory


class ComponentFactory(object):
    def __init__(self, config_filename):
        with open(config_filename, 'rb') as fin:
            self.config = pytoml.load(fin)
        self.factories = {
            'schedule': ScheduleFactory(self),
            'ammo': AmmoFactory(self),
            'gun': GunFactory(self),
            'bfg': BFGFactory(self),
            'aggregator': AggregatorFactory(self),
        }

    def get(self, factory, key):
        if factory in self.factories:
            return self.factories.get(factory).get(key)
        else:
            raise ConfigurationError("Factory '%s' not found" % factory)
