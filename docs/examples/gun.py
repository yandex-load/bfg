import logging
import random
import time

log = logging.getLogger(__name__)


class LoadTest(object):
    def __init__(self, gun):
        self.gun = gun

    def case1(self, task):
        with self.gun.measure(task):
            log.info("Shoot case 1: %s", task.data)
            time.sleep(random.random())

    def case2(self, task):
        with self.gun.measure(task) as m:
            m.action = "PREPARE"
            log.info("Prepare case 2: %s", task.data)
            time.sleep(random.random())
        with self.gun.measure(task) as m:
            m.action = "SHOOT"
            log.info("Shoot case 2: %s", task.data)
            time.sleep(random.random())
            raise RuntimeError()

    def default(self, task):
        with self.gun.measure(task):
            log.info("Shoot default case: %s", task.data)
            time.sleep(random.random())

    def setup(self, param):
        log.info("Setting up LoadTest: %s", param)

    def teardown(self):
        log.info("Tearing down LoadTest")
