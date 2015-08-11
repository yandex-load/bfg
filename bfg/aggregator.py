import threading as th
import queue
import multiprocessing as mp
from .module_exceptions import ConfigurationError
from .util import AbstractFactory
import asyncio
import time
import logging


LOG = logging.getLogger(__name__)


class ResultsSink(object):
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.results = {}
        self.results_queue = mp.Queue()
        self._stop = False
        self.stopped = False
        self.event_loop.create_task(self._reader())

    @asyncio.coroutine
    def stop(self):
        self._stop = True
        while not self.stopped:
            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def _reader(self):
        LOG.info("Results reader started")
        while not self._stop:
            try:
                sample = self.results_queue.get_nowait()
                self.results.setdefault(sample.ts, []).append(sample)
            except queue.Empty:
                yield from asyncio.sleep(1)
        LOG.info("Results reader stopped")
        self.stopped = True


class AggregatorFactory(AbstractFactory):
    FACTORY_NAME = "aggregator"

    def __init__(self, component_factory):
        super().__init__(component_factory)
        self.results = ResultsSink(self.event_loop)

    def get(self, key):
        if key in self.factory_config:
            return self.results
        else:
            raise ConfigurationError(
                "Configuration for %s schedule not found" % key)
