from .schedule import ScheduleFactory
from .ammo import AmmoFactory
from .guns import GunFactory
from .worker import BFG
from . import config as cfg
import time
import multiprocessing as mp
import threading as th
import queue
import numpy as np


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
        while not self._stopped.is_set():
            try:
                ts, sample = self.results_queue.get(timeout=1)
                self.results.setdefault(ts, []).append(sample)
            except queue.Empty:
                if self._stopped.is_set():
                    return


def main():
    config = cfg.read("tmp/load.toml")
    sf = ScheduleFactory(config)
    af = AmmoFactory(config)
    gf = GunFactory(config)
    schedule = sf.get('ramp')
    ammo = af.get('cache')
    gun = gf.get('mobile')
    rs = ResultsSink()
    lp = (
        (ts, missile, marker)
        for ts, (missile, marker) in zip(schedule, ammo))
    worker = BFG(gun, lp, rs.results_queue)
    worker.start()
    while worker.running():
        time.sleep(1)
    rs.stop()
    aggr = {
        ts: {
            "rps": len(samples),
            "avg": np.average(list(s.overallRT for s in samples)),
        } for ts, samples in rs.results.items()
    }
    for ts in sorted(aggr.keys()):
        print("%s: %s rps, %02dms avg" % (ts, aggr.get(ts).get("rps"), aggr.get(ts).get("avg")))


if __name__ == '__main__':
    main()
