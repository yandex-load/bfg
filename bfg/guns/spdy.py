'''
Gun for SPDY/2+
'''
import logging
import select
import ssl
import socket
import spdylay
from .base import GunBase, StopWatch

logger = logging.getLogger(__name__)


class SpdyTaskHandler(object):
    def __init__(self, task, scenario, results):
        self.task = task
        self.scenario = scenario
        self.results = results
        self.stream_id = None
        self.sw = None
        self.is_finished = False
        self.is_failed = False

    def on_start(self, stream_id):
        assert(self.stream_id is None)
        self.stream_id = stream_id

        self.sw = StopWatch(self.task)
        self.sw.scenario = self.scenario
        self.sw.action = 'request'

    def on_error(self, error_code=None):
        assert(self.sw is not None)

        self.sw.stop()
        self.sw.set_error(error_code)
        self.is_failed = True
        self.is_finished = True

    def on_request_sent(self):
        assert(self.sw is not None)
        assert(self.sw.action == 'request')

        self.sw.stop()
        self.results.put(self.sw.as_sample())

        self.sw = StopWatch(self.task)
        self.sw.scenario = self.scenario
        self.sw.action = 'response_start'

    def on_header(self, headers):
        assert(self.sw is not None)

        if self.sw.action == 'response_start':
            self.sw.stop()
            self.results.put(self.sw.as_sample())
        else:
            assert(self.sw.action == 'response')

        self.sw = StopWatch(self.task)
        self.sw.scenario = self.scenario
        self.sw.action = 'response'
        self.sw.ext['length'] = 0

        for k, v in headers:
            if k == ':status':
                self.sw.set_code(int(v))

    def on_data(self, length):
        assert(self.sw is not None)
        assert(self.sw.action == 'response')
        assert('length' in self.sw.ext)

        self.sw.ext['length'] += length

    def on_response_end(self):
        assert(self.sw is not None)
        assert(self.sw.action == 'response')

        self.sw.stop()
        self.results.put(self.sw.as_sample())

        self.sw = None
        self.is_finished = True


class SpdyMultiGun(GunBase):
    '''
    Multi request gun. Only GET. Expects an array of (marker, request)
    tuples in task.data. A stream is opened for every request first and
    responses are readed after all streams have been opened. A sample is
    measured for every action and for overall time for a whole batch.
    The sample for overall time is marked with 'overall' in action field.

    Based on UrlFetcher from python-spdylay.
    '''
    SECTION = 'spdy_gun'

    SPDY_VERSIONS = {
        spdylay.PROTO_SPDY2: "2",
        spdylay.PROTO_SPDY3: "3",
        # spdylay.PROTO_SPDY3_1: "3.1"
        4: "3.1"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_address = self.get_option('target')
        logger.info("Initialized spdy gun with target '%s'", self.base_address)

        self.ctx = None
        self.sock = None
        self.session = None

    def connect(self):
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.ctx.options = (
            ssl.OP_ALL | ssl.OP_NO_SSLv2 | ssl.OP_NO_COMPRESSION)
        self.ctx.set_npn_protocols(spdylay.get_npn_protocols())

        self.sock = socket.create_connection((self.base_address, 443))
        self.sock = self.ctx.wrap_socket(self.sock)

        version = spdylay.npn_get_version(self.sock.selected_npn_protocol())
        if version == 0:
            raise RuntimeError('NPN failed')
        logger.info(
            "Negotiated SPDY version: %s",
            self.SPDY_VERSIONS.get(version, 'unknown'))

        self.sock.setblocking(False)
        self.session = spdylay.Session(
            spdylay.CLIENT,
            version,
            send_cb=self.send_cb,
            on_ctrl_recv_cb=self.on_ctrl_recv_cb,
            on_data_recv_cb=self.on_data_recv_cb,
            before_ctrl_send_cb=self.before_ctrl_send_cb,
            on_ctrl_send_cb=self.on_ctrl_send_cb,
            on_stream_close_cb=self.on_stream_close_cb)

        self.session.submit_settings(
            spdylay.FLAG_SETTINGS_NONE,
            [(spdylay.SETTINGS_MAX_CONCURRENT_STREAMS,
              spdylay.ID_FLAG_SETTINGS_NONE,
              100)]
        )

    def send_cb(self, session, data):
        return self.sock.send(data)

    def before_ctrl_send_cb(self, session, frame):
        if frame.frame_type == spdylay.SYN_STREAM:
            handler = session.get_stream_user_data(frame.stream_id)
            handler.on_start(frame.stream_id)

    def on_ctrl_send_cb(self, session, frame):
        if frame.frame_type == spdylay.SYN_STREAM:
            handler = session.get_stream_user_data(frame.stream_id)
            handler.on_request_sent()

    def on_ctrl_recv_cb(self, session, frame):
        if (frame.frame_type == spdylay.SYN_REPLY or
                frame.frame_type == spdylay.HEADERS):
            handler = session.get_stream_user_data(frame.stream_id)
            handler.on_header(frame.nv)

    def on_data_recv_cb(self, session, flags, stream_id, length):
        handler = session.get_stream_user_data(stream_id)
        handler.on_data(length)

    def on_stream_close_cb(self, session, stream_id, status_code):
        handler = session.get_stream_user_data(stream_id)
        if status_code == spdylay.OK:
            handler.on_response_end()
        else:
            handler.on_error(status_code)

    def shoot(self, task):
        if self.session is None:
            self.connect()

        logger.debug("Task: %s", task)
        scenario = task.marker
        subtasks = [
            task._replace(data=missile[1], marker=missile[0])
            for missile in task.data
        ]
        handlers = []
        with self.measure(task) as overall_sw:
            for subtask in subtasks:
                logger.debug("Request GET %s", subtask.data)
                handler = SpdyTaskHandler(subtask, scenario, self.results)
                self.session.submit_request(
                    0, [
                        (':method', 'GET'),
                        (':scheme', 'https'),
                        (':path', subtask.data),
                        (':version', 'HTTP/1.1'),
                        (':host', self.base_address),
                        ('accept', '*/*'),
                        ('user-agent', 'bfg-spdy')],
                    stream_user_data=handler)
                handlers.append(handler)

            while ((self.session.want_read() or
                    self.session.want_write()) and not
                    all(h.is_finished for h in handlers)):
                want_read = want_write = False
                try:
                    data = self.sock.recv(4096)
                    if data:
                        self.session.recv(data)
                    else:
                        break
                except ssl.SSLWantReadError:
                    want_read = True
                except ssl.SSLWantWriteError:
                    want_write = True
                try:
                    self.session.send()
                except ssl.SSLWantReadError:
                    want_read = True
                except ssl.SSLWantWriteError:
                    want_write = True

                if want_read or want_write:
                    select.select([self.sock] if want_read else [],
                                  [self.sock] if want_write else [],
                                  [])

            overall_sw.stop()
            overall_sw.scenario = scenario
            overall_sw.action = "overall"

            failed = [h for h in handlers if h.is_failed]
            if failed:
                overall_sw.set_error()
