from datetime import datetime

from cobiv.libs.templite import Templite

from cobiv.modules.core.entity import Entity
from cobiv.modules.core.session.cursor import Cursor


class CoreVariables:
    def __init__(self, session):
        self.session = session

        session.fields['file_size'] = self.get_file_size
        session.fields['image_size'] = self.get_image_size
        session.fields['file_format'] = self.get_image_format
        session.fields['file_date'] = self.get_file_date
        session.fields['filename'] = lambda: self.session.cursor.filename
        session.fields['currentset_position'] = lambda: (
        self.session.cursor.pos + 1) if self.session.cursor.pos is not None else "0"
        session.fields['currentset_count'] = lambda: len(
            self.session.cursor) if self.session.cursor.pos is not None else "0"

    def get_simple_field(self, category, field_name, formatter=None):
        if self.session.cursor.file_id is None:
            return "N/A"
        if not field_name in self.session.cursor.get_tags()[category]:
            return "N/A"

        values = self.session.cursor.get_tags()[category][field_name]
        value = values[0] if len(values) > 0 else None
        if formatter is None:
            return value
        else:
            return formatter(value)

    def get_file_size(self):
        return self.get_simple_field(0, 'size')

    def get_file_date(self):
        mod_date = self.get_simple_field(0, 'file_date')
        if mod_date != "N/A":
            mod_date = datetime.fromtimestamp(float(mod_date)).strftime('%Y-%m-%d %H:%M:%S')
        return mod_date

    def get_image_size(self):
        if self.session.cursor.file_id is not None:
            tags = self.session.cursor.get_tags()
            width = tags[0]['width'][0]
            height = tags[0]['height'][0]
            if width is not None and height is not None:
                return str(width) + " x " + str(height)
        return "N/A"

    def get_image_format(self):
        return self.get_simple_field(0, 'format')

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        num = int(num)
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)


class Session(Entity):
    cursor = None
    fields = {}
    active_fs = {}
    cmd_actions = {}
    cmd_hotkeys = {}

    def __init__(self):
        self.cursor = Cursor()
        CoreVariables(self)

    def set_cursor(self, new_cursor):
        self.cursor.unbind(file_id=self.on_file_id_change)
        self.cursor = new_cursor
        self.cursor.bind(file_id=self.on_file_id_change)

    def on_file_id_change(self, instance, value):
        pass

    def fill_text_fields(self, original_text):
        return Templite(original_text.replace("%{", "${write(").replace("}%", ")}$")).render(**self.fields)

    def get_filesystem(self, key):
        return self.active_fs[key]

    def add_filesystem(self, key, filesystem):
        self.active_fs[key] = filesystem

    def set_action(self, name, fn, profile="default"):
        if name in self.cmd_actions:
            self.cmd_actions[name][profile] = fn
        else:
            self.cmd_actions[name] = {profile: fn}


    def set_hotkey(self, key, command, modifier=0, profile="default"):
        if key in self.cmd_hotkeys:
            hotkey = self.cmd_hotkeys[key]
            if profile in hotkey:
                hotkey[profile][modifier] = command
            else:
                hotkey[profile] = {modifier: command}
        else:
            self.cmd_hotkeys[key] = {profile: {modifier: command}}


    def get_hotkey_command(self, key, modifier=0, profile="default"):
        hotkeys_profiles = self.cmd_hotkeys[key]
        if profile in hotkeys_profiles:
            hotkeys = hotkeys_profiles[profile]
            if modifier in hotkeys:
                return hotkeys[modifier]

        return False
