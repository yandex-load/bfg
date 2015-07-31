from sqlalchemy import create_engine
from sqlalchemy import exc


class SqlGun(AbstractPlugin):
    SECTION = 'sql_gun'

    def __init__(self, core):
        self.log = logging.getLogger(__name__)
        AbstractPlugin.__init__(self, core)
        self.engine = create_engine(self.get_option("db"))

    def shoot(self, missile, marker, results):
        self.log.debug("Missile: %s\n%s", marker, missile)
        start_time = time.time()
        errno = 0
        httpCode = 200
        try:
            cursor = self.engine.execute(missile.replace('%', '%%'))
            cursor.fetchall()
            cursor.close()
        except exc.TimeoutError as e:
            self.log.debug("Timeout: %s", e)
            errno = 110
        except exc.ResourceClosedError as e:
            self.log.debug(e)
        except exc.SQLAlchemyError as e:
            httpCode = 500
            self.log.debug(e.orig.args)
        except exc.SAWarning as e:
            httpCode = 400
            self.log.debug(e)
        except Exception as e:
            httpCode = 500
            self.log.debug(e)
        rt = int((time.time() - start_time) * 1000)
        data_item = Sample(
            marker,             # marker
            th.active_count(),  # threads
            rt,                 # overallRT
            httpCode,           # httpCode
            errno,              # netCode
            0,                  # sent
            0,                  # received
            0,                  # connect
            0,                  # send
            rt,                 # latency
            0,                  # receive
            0,                  # accuracy
        )
        results.put((int(time.time()), data_item), timeout=1)
