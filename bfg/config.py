import pytoml


class Configuration(dict):
    def __init__(self, value=None, root=None):
        super().__init__()
        if isinstance(value, dict):
            self.__root__ = root
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('expected dict')

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(
            value, Configuration
        ):
            value = Configuration(value, self.__root__ or self)
        super().__setitem__(key, value)

    def __setattr__(self, key, value):
        if key[0] is '_':
            super().__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def __getitem__(self, key):
        if key[0] is '_':
            return super().__getitem__(key)
        value = self.get(key)
        if not value:
            raise ValueError("Key not found: '%s'" % key)
        if isinstance(value, str) and value[0] is '&':
            value = self.__root__.get(value[1:].split('.'))
        return value

    def get(self, key):
        if isinstance(key, str) and '.' in key:
            key = key.split('.')
        if isinstance(key, list):
            if len(key) > 1:
                next_node = self.get(key[0])
                if next_node:
                    return next_node.__getitem__(key[1:])
                else:
                    raise ValueError("Key not found: '%s'" % key[0])
            else:
                key = key[0]
        return super().get(key)
    __getattr__ = __getitem__


class ComponentFactory(object):
    def __init__(self, config):
        self.config = config
        self.factories = {}
        for section, section_config in config.items:
            self.factories[section] = ComponentFactory.init_factory(
                section, section_config)


def read():
    with open('load.toml', 'rb') as fin:
        config = Configuration(pytoml.load(fin))
    return config
