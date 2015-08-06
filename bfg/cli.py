from .worker import BFG
from .config import ComponentFactory
import time
import numpy as np


def main():
    cf = ComponentFactory("tmp/load.toml")
    worker = cf.get('bfg', 'mobile')
    worker.start()
    while worker.running():
        time.sleep(1)
    rs = cf.get('aggregator', 'lunapark')
    rs.stop()
    aggr = {
        ts: {
            "rps": len(samples),
            "avg": np.average(list(s.overallRT for s in samples)),
        } for ts, samples in rs.results.items()
    }
    for ts in sorted(aggr.keys()):
        print("%s: %s rps, %02dms avg" % (
            ts, aggr.get(ts).get("rps"), aggr.get(ts).get("avg")))


if __name__ == '__main__':
    main()
