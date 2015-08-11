import logging
import time
import multiprocessing as mp
import threading as th
from queue import Empty, Full
from .util import AbstractFactory
from .module_exceptions import ConfigurationError
import asyncio


LOG = logging.getLogger(__name__)


def signal_handler(signum, frame):
    pass


class BFG(object):
    """
    A BFG load generator that manages multiple workers as processes and
    threads in each of them and feeds them with tasks
    """
    def __init__(
            self, gun, load_plan, results, name, instances, event_loop):
        self.results = results
        self.name = name
        self.instances = instances
        self.gun = gun
        self.load_plan = load_plan
        self.event_loop = event_loop
        LOG.info(
            """
Name: {name}
Instances: {instances}
Gun: {gun.__class__.__name__}
""".format(
            name=self.name,
            instances=self.instances,
            gun=gun,
        ))
        self.results = results
        self.quit = mp.Event()
        self.task_queue = mp.Queue(1024)
        self.pool = [
            mp.Process(target=self._worker, name="%s-%s" % (self.name, i))
            for i in range(0, self.instances)]
        self.workers_finished = False

    def start(self):
        self.start_time = time.time()
        for process in self.pool:
            process.daemon = True
            process.start()
        self.event_loop.create_task(self._feeder())
        #self.event_loop.create_task(self._wait())

    @asyncio.coroutine
    def _wait(self):
        try:
            LOG.info("%s is waiting for workers", self.name)
            while mp.active_children():
                LOG.debug("Active children: %d", len(mp.active_children()))
                yield from asyncio.sleep(1)
            LOG.info("All workers of %s have exited", self.name)
            self.workers_finished = True
        except (KeyboardInterrupt, SystemExit):
            self.task_queue.close()
            self.quit.set()
            while mp.active_children():
                LOG.debug("Active children: %d", len(mp.active_children()))
                yield from asyncio.sleep(1)
            LOG.info("All workers of %s have exited", self.name)
            self.workers_finished = True

    def running(self):
        """
        True while there are alive workers out there. Tank
        will quit when this would become False
        """
        #return not self.workers_finished
        return len(mp.active_children())

    def stop(self):
        """
        Say the workers to finish their jobs and quit.
        """
        self.quit.set()

    @asyncio.coroutine
    def _feeder(self):
        """
        A feeder that runs in distinct thread in main process.
        """
        for timestamp, missile, marker in self.load_plan:
            if self.quit.is_set():
                LOG.info(
                    "%s observed quit flag and not going to feed anymore",
                    self.name)
                return
            # try putting a task to a queue unless there is a quit flag
            # or all workers have exited
            while True:
                try:
                    self.task_queue.put_nowait(
                        (timestamp, missile, marker, self.name))
                    break
                except Full:
                    if self.quit.is_set() or self.workers_finished:
                        return
                    else:
                        yield from asyncio.sleep(1)
        workers_count = self.instances
        LOG.info(
            "%s have feeded all data. Publishing %d poison pills",
            self.name, workers_count)
        while True:
            try:
                [self.task_queue.put_nowait(None) for _ in range(
                    0, workers_count)]
                break
            except Full:
                LOG.warning(
                    "%s could not publish killer tasks."
                    "task queue is full. Retry in 1s", self.name)
                yield from asyncio.sleep(1)

    def _worker(self):
        """
        A worker that runs in a distinct process and manages pool
        of thread workers that do actual jobs
        """
        LOG.info("Started shooter process: %s", mp.current_process().name)
        while not self.quit.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                if not task:
                    LOG.info(
                        "Got poison pill. Exiting %s",
                        mp.current_process().name)
                    return
                timestamp, missile, marker, scenario = task
                planned_time = self.start_time + (timestamp / 1000.0)
                delay = planned_time - time.time()
                if delay > 0:
                    time.sleep(delay)
                self.gun.shoot(
                    planned_time,
                    missile, scenario,
                    marker, self.results)
            except (KeyboardInterrupt, SystemExit):
                return
            except Empty:
                if self.quit.is_set():
                    LOG.debug(
                        "Empty queue and quit flag. Exiting %s",
                        mp.current_process().name)
                    return


class BFGFactory(AbstractFactory):
    FACTORY_NAME = 'bfg'

    def get(self, key):
        if key in self.factory_config:
            bfg_config = self.factory_config.get(key)
            ammo = self.component_factory.get_factory(
                'ammo', bfg_config.get('ammo'))
            schedule = self.component_factory.get_factory(
                'schedule', bfg_config.get('schedule'))
            lp = (
                (ts, missile, marker)
                for ts, (missile, marker) in zip(schedule, ammo))
            return BFG(
                name=key,
                gun=self.component_factory.get_factory(
                    'gun', bfg_config.get('gun')),
                load_plan=lp,
                instances=bfg_config.get('instances'),
                results=self.component_factory.get_factory(
                    'aggregator',
                    bfg_config.get('aggregator')).results_queue,
                event_loop=self.event_loop,
            )
        else:
            raise ConfigurationError(
                "Configuration for '%s' BFG not found" % key)
