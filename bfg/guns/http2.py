import logging
import hyper
from hyper import HTTPConnection
from .measure import measure
import time


LOG = logging.getLogger(__name__)


class HttpGun(object):
    SECTION = 'http_gun'

    def __init__(self, base_address):
        self.base_address = base_address
        LOG.info("Initialized http2 gun with target '%s'", base_address)
        self.conn = HTTPConnection(base_address, secure=True)

    def shoot(self, missile, marker, results):
        LOG.debug("Missile: %s\n%s", marker, missile)
        LOG.debug("Sending request: %s", self.base_address + missile)
        start_time = time.time()
        with measure(marker, results) as sw:
            self.conn.request('GET', missile)
            resp = self.conn.get_response()
            sw.stop()
            sw.set_code(resp.status)
