import time
import multiprocessing as mp
import threading as th
from queue import Empty, Full
from .util import FactoryBase
from .module_exceptions import ConfigurationError
from collections import namedtuple
import asyncio
import logging

logger = logging.getLogger(__name__)


Task = namedtuple(
    'Task', 'ts,bfg,marker,data')


def signal_handler(signum, frame):
    pass


class BFG(object):
    '''
    A BFG load generator that manages multiple workers as processes
    and feeds them with tasks
    '''
    def __init__(
            self, gun, load_plan, results, name, instances, event_loop):
        self.name = name
        self.instances = instances
        self.gun = gun
        self.gun.results = results
        self.load_plan = load_plan
        self.event_loop = event_loop
        logger.info(
            '''
Name: {name}
Instances: {instances}
Gun: {gun.__class__.__name__}
'''.format(
            name=self.name,
            instances=self.instances,
            gun=gun,
        ))
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

    @asyncio.coroutine
    def _wait(self):
        try:
            logger.info("%s is waiting for workers", self.name)
            while mp.active_children():
                logger.debug("Active children: %d", len(mp.active_children()))
                yield from asyncio.sleep(1)
            logger.info("All workers of %s have exited", self.name)
            self.workers_finished = True
        except (KeyboardInterrupt, SystemExit):
            self.task_queue.close()
            self.quit.set()
            while mp.active_children():
                logger.debug("Active children: %d", len(mp.active_children()))
                yield from asyncio.sleep(1)
            logger.info("All workers of %s have exited", self.name)
            self.workers_finished = True

    def running(self):
        '''
        True while there are alive workers out there. Tank
        will quit when this would become False
        '''
        #return not self.workers_finished
        return len(mp.active_children())

    def stop(self):
        '''
        Say the workers to finish their jobs and quit.
        '''
        self.quit.set()

    @asyncio.coroutine
    def _feeder(self):
        '''
        A feeder coroutine
        '''
        for task in self.load_plan:
            task = task._replace(bfg=self.name)
            if self.quit.is_set():
                logger.info(
                    "%s observed quit flag and not going to feed anymore",
                    self.name)
                return
            # try putting a task to a queue unless there is a quit flag
            # or all workers have exited
            while True:
                try:
                    self.task_queue.put_nowait(task)
                    break
                except Full:
                    if self.quit.is_set() or self.workers_finished:
                        return
                    else:
                        yield from asyncio.sleep(1)
        workers_count = self.instances
        logger.info(
            "%s have feeded all data. Publishing %d poison pills",
            self.name, workers_count)
        while True:
            try:
                [self.task_queue.put_nowait(None) for _ in range(
                    0, workers_count)]
                break
            except Full:
                logger.warning(
                    "%s could not publish killer tasks."
                    "task queue is full. Retry in 1s", self.name)
                yield from asyncio.sleep(1)

    def _worker(self):
        '''
        A worker that runs in a distinct process
        '''
        logger.info("Started shooter process: %s", mp.current_process().name)
        self.gun.setup()
        while not self.quit.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                if not task:
                    logger.info(
                        "Got poison pill. Exiting %s",
                        mp.current_process().name)
                    break
                task = task._replace(ts=self.start_time + (task.ts / 1000.0))
                delay = task.ts - time.time()
                if delay > 0:
                    time.sleep(delay)
                self.gun.shoot(task)
            except (KeyboardInterrupt, SystemExit):
                break
            except Empty:
                if self.quit.is_set():
                    logger.debug(
                        "Empty queue and quit flag. Exiting %s",
                        mp.current_process().name)
                    break
        self.gun.teardown()


class BFGFactory(FactoryBase):
    FACTORY_NAME = 'bfg'

    def get(self, bfg_name):
        if bfg_name in self.factory_config:
            bfg_config = self.factory_config.get(bfg_name)
            ammo = self.component_factory.get_factory(
                'ammo', bfg_config.get('ammo'))
            schedule = self.component_factory.get_factory(
                'schedule', bfg_config.get('schedule'))
            lp = (
                Task(ts, bfg_name, marker, data)
                for ts, (marker, data) in zip(schedule, ammo))
            return BFG(
                name=bfg_name,
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
                "Configuration for '%s' BFG not found" % bfg_name)
