from contextlib import contextmanager
import time
from collections import namedtuple

Sample = namedtuple(
    'Sample', 'marker,threads,overallRT,httpCode,netCode,'
    'sent,received,connect,send,latency,receive,accuracy')


@contextmanager
def measure(marker, results):
    start_time = time.time()
    yield
    response_time = int((time.time() - start_time) * 1000)
    data_item = Sample(
        marker,             # marker
        0,  # threads
        response_time,      # overall response time
        200,                # httpCode
        0,                  # netCode
        0,                  # sent
        0,                  # received
        0,                  # connect
        0,                  # send
        response_time,      # latency
        0,                  # receive
        0,                  # accuracy
    )
    results.put((int(time.time()), data_item), timeout=1)
