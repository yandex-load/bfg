class AbstractGun(object):
    def __init__(self, config, results):
        self.config = config
        self.results = results

    def publish(self, ts, sample):
        self.results.push(ts, sample, )
