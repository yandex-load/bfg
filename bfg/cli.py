'''
Entry point. Init logging, initialize component factory,
start asyncio event loop, manage components lifecycle
'''

import logging
import yaml
import pytoml
import json
import sys
from .loadtest import LoadTest


LOG = logging.getLogger(__name__)


def init_logging(debug=False, filename='bfg.log'):
    ''' Configure logging: verbose or not '''
    default_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    dbg_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    dbg_handler = logging.FileHandler(filename)
    dbg_handler.setLevel(debug)
    dbg_handler.setFormatter(dbg_formatter)

    cmd_handler = logging.StreamHandler(sys.stdout)
    cmd_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    cmd_handler.setFormatter(dbg_formatter if debug else default_formatter)

    warn_handler = logging.StreamHandler(sys.stdout)
    warn_handler.setLevel(logging.WARN)
    warn_handler.setFormatter(dbg_formatter)

    logger = logging.getLogger("hyper")
    logger.setLevel(logging.WARNING)

    logger = logging.getLogger("")  # configure root logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(cmd_handler)
    logger.addHandler(dbg_handler)
    logging.getLogger().addHandler(dbg_handler)


def main():
    ''' Run test '''
    config_filename = "load.yaml"
    if len(sys.argv) > 1:
        config_filename = sys.argv[1]

    filename_components = config_filename.split('.')
    if len(filename_components) > 1:
        extension = filename_components[-1]

        with open(config_filename, 'rb') as fin:
            if extension == 'toml':
                config = pytoml.load(fin)
            elif extension in ['yaml', 'yml']:
                config = yaml.load(fin)
            elif extension == 'json':
                config = json.load(fin)
            else:
                print("Config file has unsupported format: %s" % extension)
    else:
        print(
            "Config file should have one of the following extensions:"
            " .toml, .json, .yaml")
        return 1
    init_logging()
    lt = LoadTest(config)
    lt.run_test()


if __name__ == '__main__':
    main()
