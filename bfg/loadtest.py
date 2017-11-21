''' Load test: entry point '''
from .worker import BFG
from .config import ComponentFactory
import time
import numpy as np
import asyncio
import logging


logger = logging.getLogger(__name__)


class LoadTest(object):

    ''' Load test lifecycle '''

    def __init__(self, config):
        self.config = config
        self.event_loop = asyncio.get_event_loop()

    def __del__(self):
        self.event_loop.close()

    def run_test(self):
        self.event_loop.run_until_complete(self._test())

    @asyncio.coroutine
    def _test(self):
        ''' Main coroutine. Manage components' lifecycle '''

        # Configure factories using config files
        logger.info("Configuring component factory")
        cf = ComponentFactory(self.config, self.event_loop)

        # Create workers using 'bfg' section from config
        logger.info("Creating workers")
        workers = [
            cf.get_factory('bfg', bfg_name)
            for bfg_name in cf.get_config('bfg')]

        # Start workers and wait for them asyncronously
        logger.info("Starting workers")
        [worker.start() for worker in workers]
        logger.info("Waiting for workers")
        while any(worker.running() for worker in workers):
            yield from asyncio.sleep(1)
        logger.info("All workers finished")

        # Stop aggregator
        rs = cf.get_factory('aggregator', 'lunapark')
        yield from rs.stop()
