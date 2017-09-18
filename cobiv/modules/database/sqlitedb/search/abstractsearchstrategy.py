class AbstractSearchStrategy(object):
    tablename = None
    file_key_name = "file_key"

    def is_managing_kind(self, kind):
        return False

    def prepare(self, is_excluding, lists, kind, fn, values):
        pass

    def process(self, lists, *args):
        pass

    def get_sort_field(self,kind,order,is_number):
        pass

    def get_sort_query(self,kind,order,is_number):
        pass

    @staticmethod
    def add_query(query,joiner,item):
        return (joiner*(len(query)>0))+item