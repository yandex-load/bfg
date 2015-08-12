import threading as th
import queue
import multiprocessing as mp
from .module_exceptions import ConfigurationError
from .util import AbstractFactory
import asyncio
import time
import numpy as np
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


class CachingAggregator(object):
    def __init__(self, event_loop):
        self.cache_depth = 5
        self.event_loop = event_loop
        self.results = {}
        self.aggregated_results = {}
        self.results_queue = mp.Queue()
        self._stop = False
        self.reader_stopped = False
        self.aggregator_stopped = False
        self.event_loop.create_task(self._reader())
        self.event_loop.create_task(self._aggregator())

    @asyncio.coroutine
    def stop(self):
        self.cache_depth = 0  # empty the cache
        self._stop = True
        while not self.reader_stopped:
            yield from asyncio.sleep(1)
        while not self.aggregator_stopped:
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
        self.reader_stopped = True

    @asyncio.coroutine
    def _aggregator(self):
        while not (self.reader_stopped and len(self.results) == 0):
            yield from asyncio.sleep(1)
            for _ in range(len(self.results) - self.cache_depth):
                smallest_key = min(self.results.keys())
                self.aggregate(
                    smallest_key, self.results.pop(smallest_key))
        LOG.info("Results aggregator stopped")
        self.aggregator_stopped = True

    def aggregate(self, ts, samples):
        if ts in self.aggregated_results:
            LOG.warning(
                "%s already aggregated. Some data points lost."
                "Try increasing aggregator cache")

        aggr = {
            "rps": len(samples),
            "avg_rt": np.average(list(s.overall for s in samples)),
            "avg_delay": np.average(list(s.delay for s in samples)),
        }
        LOG.info("Aggregated data for %s:\n%s", ts, aggr)
        self.aggregated_results[ts] = aggr

class AggregatorFactory(AbstractFactory):
    FACTORY_NAME = "aggregator"

    def __init__(self, component_factory):
        super().__init__(component_factory)
        self.results = CachingAggregator(self.event_loop)

    def get(self, key):
        if key in self.factory_config:
            return self.results
        else:
            raise ConfigurationError(
                "Configuration for %s schedule not found" % key)
