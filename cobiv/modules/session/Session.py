import os
from datetime import datetime

from templite import Templite

from cobiv.modules.entity import Entity
from cobiv.modules.session.cursor import Cursor


class CoreVariables:
    def __init__(self, session):
        self.session = session

        session.fields['file_size']=self.get_file_size
        session.fields['image_size']=self.get_image_size
        session.fields['file_format']=self.get_image_format
        session.fields['modified_date']=self.get_modification_date

    def get_simple_field(self,category,field_name,formatter=None):
        if self.session.cursor.file_id is None:
            return "N/A"
        if not self.session.cursor.get_tags()[category].has_key(field_name):
            return "N/A"

        values=self.session.cursor.get_tags()[category][field_name]
        value=values[0] if len(values)>0 else None
        if formatter is None:
            return value
        else:
            return formatter(value)

    def get_file_size(self):
        return self.get_simple_field(0,'size',CoreVariables.sizeof_fmt)

    def get_modification_date(self):
        mod_date=self.get_simple_field(0,'modification_date')
        if mod_date!="N/A":
            mod_date=datetime.fromtimestamp(float(mod_date)).strftime('%Y-%m-%d %H:%M:%S')
        return mod_date

    def get_image_size(self):
        if self.session.cursor.file_id is not None:
            tags=self.session.cursor.get_tags()
            width=tags[0]['width'][0]
            height=tags[0]['height'][0]
            if width is not None and height is not None:
                return width+" x "+height
        return "N/A"

    def get_image_format(self):
        return self.get_simple_field(0,'format')

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        num=int(num)
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)


class Session(Entity):
    cursor = None

    fields = {}

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
        text = original_text.replace("%{","${write(").replace("}%",")}$")
        # for key in self.fields.keys():
        #     key_string = "%" + key + "%"
        #     if key_string in original_text:
        #         text = text.replace(key_string, str(self.fields.get(key)()))
        template=Templite(text)
        text=template.render(**self.fields)

        return text
