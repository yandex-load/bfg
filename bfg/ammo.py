'''
Missile object and generators

You should update Stepper.status.ammo_count and Stepper.status.loop_count in your custom generators!
'''
from .util import get_opener
from itertools import cycle
from .module_exceptions import AmmoFileError, ConfigurationError
import logging


class LineReader(object):

    '''One line -- one missile'''

    def __init__(self, filename, **kwargs):
        self.filename = filename

    def __iter__(self):
        with get_opener(self.filename)(self.filename, 'r') as ammo_file:
            while True:
                for line in ammo_file:
                    yield (line.rstrip('\r\n'), None)
                ammo_file.seek(0)


class AmmoFactory(object):
    def __init__(self, component_factory):
        self.config = component_factory.config
        self.factory_config = self.config.get('ammo')

    def get(self, key):
        if key in self.factory_config:
            return LineReader(self.factory_config.get(key).get("file"))
        else:
            raise ConfigurationError(
                "Configuration for %s ammo not found" % key)
