import bfg.scheduling
import bfg.ammo
from bfg.guns.http import HttpGun


class Results(object):
    def put(self, r):
        print(r)


def main():
    schedule = bfg.scheduling.create(['line(1,10,1m)'])
    ammo = bfg.ammo.LineReader('ammo.line')
    gun = HttpGun("http://bsgraphite-gfe01h.yandex.ru")
    r = Results()
    lp = zip(schedule, ammo)
    for ts, a in lp:
        print(ts, a)
        print(gun.shoot(a[0], a[1], r))

if __name__ == '__main__':
    main()
