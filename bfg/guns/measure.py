from contextlib import contextmanager
import time
from collections import namedtuple

Sample = namedtuple(
    'Sample', 'ts,scenario,marker,overall,error,code,delay,ext')


class StopWatch(object):
    def __init__(self, planned_time, scenario, marker):
        self.planned_time = planned_time
        self.marker = marker
        self.start_time = time.time()
        self.end_time = self.start_time
        self.error = False
        self.scenario = scenario
        self.code = None
        self.ext = {}
        self.stopped = False

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if not self.stopped:
            self.stopped = True
            self.end_time = time.time()

    def set_error(self, code=None):
        if code:
            self.set_code(code)
        self.error = True

    def set_code(self, code):
        self.code = code

    def as_sample(self):
        overall = int(
            (self.end_time - self.start_time) * 1000)
        return Sample(
            int(self.start_time),
            self.scenario,
            self.marker,
            overall,
            self.error,
            self.code,
            self.start_time - self.planned_time,
            self.ext,
        )


@contextmanager
def measure(planned_time, scenario, marker, results):
    sw = StopWatch(planned_time, scenario, marker)
    yield sw
    sw.stop()
    results.put(sw.as_sample())
