from .worker import BFG
from .config import ComponentFactory
import time
import numpy as np
import asyncio
import logging
import sys


LOG = logging.getLogger(__name__)


def init_logging(debug=False):
    default_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    dbg_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    dbg_handler = logging.FileHandler('bfg.log')
    dbg_handler.setLevel(debug)
    dbg_handler.setFormatter(dbg_formatter)

    cmd_handler = logging.StreamHandler(sys.stdout)
    cmd_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    cmd_handler.setFormatter(dbg_formatter if debug else default_formatter)

    warn_handler = logging.StreamHandler(sys.stdout)
    warn_handler.setLevel(logging.WARN)
    warn_handler.setFormatter(dbg_formatter)

    logger = logging.getLogger("hyper")  # configure root logger
    logger.setLevel(logging.WARNING)

    logger = logging.getLogger("")  # configure root logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(cmd_handler)
    logger.addHandler(dbg_handler)
    logging.getLogger().addHandler(dbg_handler)


def main():
    init_logging()
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main_coro(event_loop))
    event_loop.close()


@asyncio.coroutine
def main_coro(event_loop):
    LOG.info("Configuring component factory")
    cf = ComponentFactory("tmp/load.toml", event_loop)
    LOG.info("Creating workers")
    workers = [
        cf.get_factory('bfg', bfg_name)
        for bfg_name in cf.get_config('bfg')]
    LOG.info("Starting workers")
    [worker.start() for worker in workers]
    LOG.info("Waiting for workers")
    while any(worker.running() for worker in workers):
        yield from asyncio.sleep(1)
    LOG.info("All workers finished")
    rs = cf.get_factory('aggregator', 'lunapark')
    rs.stop()
    aggr = {
        ts: {
            "rps": len(samples),
            "avg": np.average(list(s.overall for s in samples)),
        } for ts, samples in rs.results.items()
    }
    for ts in sorted(aggr.keys()):
        print("%s: %s rps, %02dms avg" % (
            ts, aggr.get(ts).get("rps"), aggr.get(ts).get("avg")))


if __name__ == '__main__':
    main()
