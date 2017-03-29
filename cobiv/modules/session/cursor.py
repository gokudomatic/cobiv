from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, NumericProperty


class CursorInterface(EventDispatcher):
    filename = StringProperty(None)
    id = NumericProperty(None)
    pos = NumericProperty(None)

    def go_next(self):
        return False

    def go_previous(self):
        return False

    def go_first(self):
        return False

    def go_last(self):
        return False

    def get_file_key(self):
        return None

    def get(self, idx):
        return self

    def go(self, idx):
        return False

    def get_tags(self):
        return []

    def mark(self):
        pass

    def get_mark(self):
        return False

    def remove(self):
        return False

    def __len__(self):
        return 0

    def get_cursor_by_pos(self,pos):
        return None

    def get_thumbnail(self):
        return None

class Cursor(EventDispatcher):
    filename = StringProperty(None)
    implementation = None
    id = NumericProperty(None)
    pos = NumericProperty(None)

    def __init__(self, **kwargs):
        super(Cursor, self).__init__(**kwargs)

    def get_app(self):
        return App.get_running_app()

    def set_implementation(self, instance):
        if self.implementation is not None:
            self.implementation.unbind(filename=self.on_filename_change, id=self.on_id_change, pos=self.on_pos_change)
        self.implementation = instance
        if instance is not None:
            self.implementation.bind(filename=self.on_filename_change)
            self.implementation.bind(id=self.on_id_change)
            self.implementation.bind(pos=self.on_pos_change)
            self.id = self.implementation.id
            self.pos=self.implementation.pos
            self.filename = self.implementation.filename
        else:
            self.filename = None
            self.id = None

    def on_id_change(self, instance, value):
        self.id = value

    def on_pos_change(self, instance, value):
        self.pos = value

    def on_filename_change(self, instance, value):
        self.filename = value

    def go_next(self):
        return self.implementation.go_next()

    def go_previous(self):
        return self.implementation.go_previous()

    def go_first(self):
        return self.implementation.go_first()

    def go_last(self):
        return self.implementation.go_last()

    def get_file_key(self):
        return self.implementation.get_file_key()

    def get(self, idx):
        return self.implementation.get(idx)

    def go(self, idx):
        return self.implementation.go(idx)

    def get_tags(self):
        return self.implementation.get_tags()

    def mark(self):
        self.implementation.mark()
        self.get_app().root.execute_cmd("refresh-marked")

    def get_mark(self):
        return self.implementation.get_mark()

    def remove(self):
        return self.implementation.remove()

    def __len__(self):
        return self.implementation.__len__()

    def get_cursor_by_pos(self,pos):
        return self.implementation.get_cursor_by_pos(pos)

    def get_thumbnail(self):
        return self.implementation.get_thumbnail()
