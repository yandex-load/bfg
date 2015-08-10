import logging
import time
import multiprocessing as mp
import threading as th
from queue import Empty, Full
from .util import AbstractFactory
from .module_exceptions import ConfigurationError


LOG = logging.getLogger(__name__)


def signal_handler(signum, frame):
    pass


class BFG(object):
    """
    A BFG load generator that manages multiple workers as processes and
    threads in each of them and feeds them with tasks
    """
    def __init__(
            self, gun, load_plan, results, name, instances):
        self.results = results
        self.name = name
        self.instances = instances
        self.gun = gun
        self.load_plan = load_plan
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
        self.feeder = th.Thread(target=self._feed, name="Feeder")
        self.workers_finished = False

    def start(self):
        self.start_time = time.time()
        for process in self.pool:
            process.daemon = True
            process.start()
        self.feeder.start()

    def running(self):
        """
        True while there are alive workers out there. Tank
        will quit when this would become False
        """
        return not self.workers_finished

    def stop(self):
        """
        Say the workers to finish their jobs and quit.
        """
        self.quit.set()

    def _feed(self):
        """
        A feeder that runs in distinct thread in main process.
        """
        for task in self.load_plan:
            if self.quit.is_set():
                LOG.info(
                    "%s observed quit flag and not going to feed anymore",
                    self.name)
                return
            # try putting a task to a queue unless there is a quit flag
            # or all workers have exited
            while True:
                try:
                    self.task_queue.put(task, timeout=1)
                    break
                except Full:
                    if self.quit.is_set() or self.workers_finished:
                        return
                    else:
                        continue
        workers_count = self.instances
        LOG.info(
            "%s have feeded all data. Publishing %d poison pills",
            self.name, workers_count)
        [self.task_queue.put(None, timeout=1) for _ in range(
            0, workers_count)]

        try:
            LOG.info("%s is waiting for workers", self.name)
            list([x.join() for x in self.pool])
            LOG.info("All workers of %s have exited", self.name)
            self.workers_finished = True
        except (KeyboardInterrupt, SystemExit):
            self.task_queue.close()
            self.quit.set()
            LOG.info("%s have set quit flag. Waiting for workers", self.name)
            list([x.join() for x in self.pool])
            self.workers_finished = True

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
                timestamp, missile, marker = task
                planned_time = self.start_time + (timestamp / 1000.0)
                delay = planned_time - time.time()
                if delay > 0:
                    time.sleep(delay)
                self.gun.shoot(missile, marker, self.results)
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
            )
        else:
            raise ConfigurationError(
                "Configuration for '%s' BFG not found" % key)
