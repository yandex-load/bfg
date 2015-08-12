import logging
import hyper
from hyper import HTTP20Connection
from .measure import measure
import time


LOG = logging.getLogger(__name__)


class HttpGun(object):
    SECTION = 'http_gun'

    def __init__(self, base_address):
        self.base_address = base_address
        LOG.info("Initialized http2 gun with target '%s'", base_address)
        self.conn = HTTP20Connection(base_address, secure=True)

    def shoot(self, task, results):
        LOG.debug("Task: %s", task)
        LOG.debug("Sending request: %s", self.base_address + task.data)
        with measure(task, results) as sw:
            stream = self.conn.request('GET', task.data)
            resp = self.conn.get_response(stream)
            sw.stop()
            sw.set_code(resp.status)

class HttpMultiGun(object):
    SECTION = 'http_gun'

    def __init__(self, base_address):
        self.base_address = base_address
        LOG.info("Initialized http2 gun with target '%s'", base_address)
        self.conn = HTTP20Connection(base_address, secure=True)

    def shoot(self, planned_time, task, results):
        #LOG.debug("Missile: %s/%s\n%s", scenario, marker, missile)
        #LOG.debug("Sending request: %s", self.base_address + missile)
        start_time = time.time()
        with measure(planned_time, task, results) as sw:
            streams = [
                self.conn.request('GET', missile)
                for missile in missiles]
            responses = [
                self.conn.get_response(s)
                for s in streams]
            sw.stop()
            #sw.set_code(resp.status)
