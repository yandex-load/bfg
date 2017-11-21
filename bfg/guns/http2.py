'''
Guns for HTTP/2
'''
import logging
from collections import namedtuple
from hyper import HTTP20Connection, tls
import ssl
from hyper.http20.exceptions import ConnectionError
from .base import GunBase

Http2Ammo = namedtuple("Http2Ammo", "method,uri,headers,body")


logger = logging.getLogger(__name__)


class HttpMultiGun(GunBase):
    '''
    Multi request gun. Only GET. Expects an array of (marker, request)
    tuples in task.data. A stream is opened for every request first and
    responses are readed after all streams have been opened. A sample is
    measured for every action and for overall time for a whole batch.
    The sample for overall time is marked with 'overall' in action field.
    '''
    SECTION = 'http_gun'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_address = self.get_option('target')
        logger.info("Initialized http2 gun with target '%s'", self.base_address)
        context = tls.init_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.conn = HTTP20Connection(self.base_address, secure=True, ssl_context=context)

    def shoot(self, task):
        logger.debug("Task: %s", task)
        scenario = task.marker
        subtasks = [
            task._replace(data=missile[1], marker=missile[0])
            for missile in task.data
        ]
        streams = []
        with self.measure(task) as overall_sw:
            for subtask in subtasks:
                with self.measure(subtask) as sw:
                    logger.debug("Request GET %s", subtask.data)
                    streams.append(
                        (subtask, self.conn.request('GET', subtask.data)))
                    sw.stop()
                    sw.scenario = scenario
                    sw.action = "request"
            for (subtask, stream) in streams:
                with self.measure(subtask) as sw:
                    logger.debug("Response for %s from %s ", subtask.data, stream)
                    try:
                        resp = self.conn.get_response(stream)
                    except (ConnectionError, KeyError) as e:
                        sw.stop()
                        # TODO: try to add a meaningful code here
                        sw.set_error(1)
                        overall_sw.set_error(1)
                        sw.ext["error"] = str(e)
                        overall_sw.ext.setdefault('error', []).append(str(e))
                        logger.warning("Error getting response: %s", str(e))
                    else:
                        sw.stop()
                        sw.set_code(str(resp.status))
                    sw.scenario = scenario
                    sw.action = "response"
            overall_sw.stop()
            overall_sw.scenario = scenario
            overall_sw.action = "overall"
