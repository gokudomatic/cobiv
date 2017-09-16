class AbstractSearchStrategy(object):
    def is_managing_kind(self, kind):
        return False

    def prepare(self, is_excluding, lists, kind, fn, values):
        pass

    def process(self, lists, *args):
        pass
