import bfg.scheduling
import bfg.ammo
from bfg.guns.http2 import HttpGun
from bfg.worker import BFG


class Results(object):
    def put(self, r):
        print(r)


def main():
    schedule = bfg.scheduling.create(['line(1,10,1m)'])
    ammo = bfg.ammo.LineReader('ammo.line')
    gun = HttpGun("http2bin.org")
    r = Results()
    lp = ((ts, missile, marker) for ts, (missile, marker) in zip(schedule, ammo))
    worker = BFG(gun, lp, r)
    worker.start()

if __name__ == '__main__':
    main()
