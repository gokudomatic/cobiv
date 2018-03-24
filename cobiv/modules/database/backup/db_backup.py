import json

class DbBackup(object):

    def load_json(self, filepath):
        with open(filepath, 'r') as infile:
            return json.loads(infile.read())

    def dump_json(self, filepath, data):
        with open(filepath, 'w') as outfile:
            json.dump(data.__dict__,outfile,separators=(',', ':'))


class JsonBackupBody(object):

    def __init__(self, files=None) -> None:
        super().__init__()
        self.files = [] if files is None else files
