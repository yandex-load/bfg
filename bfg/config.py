import pytoml


class DotDict(dict):
    """
    Inspired by
    http://stackoverflow.com/questions/3031219/python-recursively-access-dict-via-attributes-as-well-as-index-access
    """
    def __init__(self, value=None):
        if isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('expected dict')

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        super(DotDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        return self.get(key)

    __setattr__ = __setitem__
    __getattr__ = __getitem__


def read():
    with open('load.toml', 'rb') as fin:
        config = DotDict(pytoml.load(fin))
    return config
