import pytoml
from . import scheduling as sch


FACTORIES = {
    'schedules': lambda x: {k: sch.create(v) for k, v in x.items()},
    'bfg': lambda x: x,
    'scenarios': lambda x: x,
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


def read():
    with open('load.toml', 'rb') as fin:
        factory = ComponentFactory(pytoml.load(fin))
    return factory
