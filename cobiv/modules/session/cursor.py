from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty


class CursorInterface(EventDispatcher):
    filename = StringProperty(None)
    pos = NumericProperty(None)
    file_id = NumericProperty(None)

    def go_next(self):
        return False

    def go_previous(self):
        return False

    def go_first(self):
        return False

    def go_last(self):
        return False

    def get(self, idx):
        return self

    def get_next_ids(self, amount):
        return []

    def get_previous_ids(self, amount):
        return []

    def go(self, idx):
        return False

    def get_tags(self):
        return []

    def mark(self,value):
        pass

    def get_mark(self):
        return False

    def get_all_marked(self):
        return False

    def remove(self):
        return False

    def __len__(self):
        return 0

    def get_cursor_by_pos(self, pos):
        return None

    def get_thumbnail(self):
        return None

    def move_to(self,idx):
        return None

    def get_position_mapping(self, file_id_list):
        return []

class Cursor(EventDispatcher):
    filename = StringProperty(None)
    implementation = None
    pos = NumericProperty(None)
    file_id = NumericProperty(None)

    def __init__(self, **kwargs):
        super(Cursor, self).__init__(**kwargs)

    def get_app(self):
        return App.get_running_app()

    def set_implementation(self, instance):
        if self.implementation is not None:
            self.implementation.unbind(filename=self.on_filename_change, file_id=self.on_file_id_change,
                                       pos=self.on_pos_change)
        self.implementation = instance
        if instance is not None:
            self.implementation.bind(filename=self.on_filename_change)
            self.implementation.bind(file_id=self.on_file_id_change)
            self.implementation.bind(pos=self.on_pos_change)
            self.pos = self.implementation.pos
            self.filename = self.implementation.filename
            self.file_id = self.implementation.file_id
        else:
            self.filename = None
            self.file_id = None

    def on_pos_change(self, instance, value):
        self.pos = value

    def on_filename_change(self, instance, value):
        self.filename = value

    def on_file_id_change(self, instance, value):
        self.file_id = value

    def go_next(self):
        return self.implementation.go_next()

    def go_previous(self):
        return self.implementation.go_previous()

    def go_first(self):
        return self.implementation.go_first()

    def go_last(self):
        return self.implementation.go_last()

    def get(self, idx):
        return self.implementation.get(idx)

    def get_next_ids(self, amount):
        return self.implementation.get_next_ids(amount)

    def get_previous_ids(self, amount):
        return self.implementation.get_previous_ids(amount)

    def go(self, idx):
        if self.pos is not None and idx==self.pos:
            return True
        else:
            return self.implementation.go(idx)

    def get_tags(self):
        return self.implementation.get_tags()

    def mark(self,value=None):
        self.implementation.mark(value)
        self.get_app().root.execute_cmd("refresh-marked")

    def get_mark(self):
        return self.implementation.get_mark()

    def get_all_marked(self):
        return self.implementation.get_all_marked()

    def remove(self):
        return self.implementation.remove()

    def __len__(self):
        return self.implementation.__len__()

    def get_cursor_by_pos(self, pos):
        return self.implementation.get_cursor_by_pos(pos)

    def get_thumbnail(self):
        return self.implementation.get_thumbnail()

    def move_to(self,idx):
        return self.implementation.move_to(idx)

    def get_position_mapping(self,file_id_list):
        return self.implementation.get_position_mapping(file_id_list)