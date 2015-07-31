import bfg.config
from .scheduling import create


def main():
    c = bfg.config.read()
    n = c.get("schedules")
    lp = {}
    for k, v in n.items():
        lp[k] = create(v)
    print(c.get("bfg.events.scenario"))


if __name__ == '__main__':
    main()
