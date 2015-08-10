import threading as th
import queue
import multiprocessing as mp
from .module_exceptions import ConfigurationError
import logging


LOG = logging.getLogger(__name__)


class ResultsSink(object):
    def __init__(self):
        self.results = {}
        self.results_queue = mp.Queue()
        self._stopped = th.Event()
        self.reader = th.Thread(target=self._reader)
        self.reader.start()

    def stop(self):
        self._stopped.set()

    def _reader(self):
        LOG.info("Results reader started")
        while not self._stopped.is_set():
            try:
                ts, sample = self.results_queue.get(timeout=1)
                self.results.setdefault(ts, []).append(sample)
            except queue.Empty:
                if self._stopped.is_set():
                    LOG.info("Stopping results reader")
                    return


class AggregatorFactory(object):
    def __init__(self, component_factory):
        self.config = component_factory.config
        self.factory_config = self.config.get('aggregator')
        self.results = ResultsSink()

    def get(self, key):
        if key in self.factory_config:
            return self.results
        else:
            raise ConfigurationError(
                "Configuration for %s schedule not found" % key)
