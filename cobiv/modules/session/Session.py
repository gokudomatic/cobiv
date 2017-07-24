import os

from cobiv.modules.entity import Entity
from cobiv.modules.session.cursor import Cursor


class CoreVariables:
    def __init__(self, session):
        self.session = session

        session.fields['file_size']=self.get_file_size

    def get_file_size(self):
        if self.session.cursor.filename is not None:
            return CoreVariables.sizeof_fmt(os.path.getsize(self.session.cursor.filename))
        else:
            return "0 B"

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)


class Session(Entity):
    cursor = None

    fields = dict()

    def __init__(self):
        self.cursor = Cursor()
        CoreVariables(self)

    def set_cursor(self,new_cursor):
        self.cursor.unbind(file_id=self.on_file_id_change)
        self.cursor=new_cursor
        self.cursor.bind(file_id=self.on_file_id_change)

    def on_file_id_change(self,instance,value):
        pass

    def fill_text_fields(self, original_text):
        text = original_text
        for key in self.fields.keys():
            key_string = "%" + key + "%"
            if key_string in original_text:
                text = text.replace(key_string, str(self.fields.get(key)()))

        return text
