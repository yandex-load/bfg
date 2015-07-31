from . import config
from .scheduling import create


def main():
    f = config.read()

    print(f.get('scenarios'))


if __name__ == '__main__':
    main()
