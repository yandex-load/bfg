import pytoml
from . import schedule as sch


FACTORIES = {
    'schedule': lambda x: {k: sch.create(v) for k, v in x.items()},
    'bfg': lambda x: x,
    'scenario': lambda x: x,
    'http2': lambda x: x,
    'target': lambda x: x,
}


class ComponentFactory(object):
    def init_factory(section, config):
        if section in FACTORIES:
            return FACTORIES.get(section)(config)

    def __init__(self, config):
        self.config = config
        self.factories = {}
        for section, section_config in config.items():
            self.factories[section] = ComponentFactory.init_factory(
                section, section_config)

    def get(self, key):
        return self.factories.get(key)


def read(filename):
    with open(filename, 'rb') as fin:
        config = pytoml.load(fin)
    return config
