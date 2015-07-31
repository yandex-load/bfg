import logging
import time
import multiprocessing as mp
import threading as th
from queue import Empty, Full


LOG = logging.getLogger(__name__)


def signal_handler(signum, frame):
    pass


class BFG(object):
    """
    A BFG load generator that manages multiple workers as processes and
    threads in each of them and feeds them with tasks
    """
    def __init__(
            self, config, gun, ammo):
        self.config = config
        self.instances = self.config.get('bfg.instances')
        self.gun = gun
        self.ammo = ammo
        LOG.info(
            """
Instances: {instances}
Gun: {gun.__class__.__name__}
""".format(
            instances=self.instances,
            gun=gun,
        ))
        self.quit = mp.Event()
        self.task_queue = mp.Queue(1024)
        self.pool = [
            mp.Process(target=self._worker) for _ in range(0, self.instances)]
        self.feeder = th.Thread(target=self._feed, name="Feeder")
        self.workers_finished = False

    def start(self):
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
        self.start_time = time.time()
        for task in self.ammo:
            if self.quit.is_set():
                LOG.info("Stop feeding: gonna quit")
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
            "Feeded all data. Publishing %d killer tasks" % (
                workers_count))
        [self.task_queue.put(None, timeout=1) for _ in range(
            0, workers_count)]

        try:
            LOG.info("Waiting for workers")
            list([x.join() for x in self.pool])
            LOG.info("All workers exited.")
            self.workers_finished = True
        except (KeyboardInterrupt, SystemExit):
            self.task_queue.close()
            self.quit.set()
            LOG.info("Going to quit. Waiting for workers")
            list([x.join() for x in self.pool])
            self.workers_finished = True

    def _worker(self):
        """
        A worker that runs in a distinct process and manages pool
        of thread workers that do actual jobs
        """
        LOG.info("Started shooter process...")
        while not self.quit.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                if not task:
                    LOG.info(
                        "Shooter process got killer task. Exiting")
                    return
                timestamp, missile, marker = task
                planned_time = self.start_time + (timestamp / 1000.0)
                delay = planned_time - time.time()
                if delay > 0:
                    time.sleep(delay)
                self.gun.shoot(missile, marker)
            except (KeyboardInterrupt, SystemExit):
                return
            except Empty:
                if self.quit.is_set():
                    LOG.debug(
                        "Empty queue. Exiting")
                    return
