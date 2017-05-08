from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty, ObjectProperty

class CursorInterface(EventDispatcher):
    filename = StringProperty(None)
    pos = NumericProperty(None)
    file_id = NumericProperty(None)

    def clone(self):
        return None

    def go_next(self):
        return None

    def go_previous(self):
        return None

    def go_first(self):
        return None

    def go_last(self):
        return None

    def get(self, idx):
        return self

    def get_next_ids(self, amount):
        return []

    def get_previous_ids(self, amount):
        return []

    def go(self, idx):
        return None

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

class EOLCursor(CursorInterface):

    last_cursor = ObjectProperty(None)

    def __len__(self):
        if self.last_cursor is None:
            return 0
        else:
            return self.last_cursor.__len__()

    def go_first(self):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.go_first()

    def go_last(self):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.go_last()

    def go_previous(self):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor

    def get_previous_ids(self, amount):
        if self.last_cursor is None:
            return []
        else:
            return self.last_cursor.get_previous_ids(amount)

    def get_all_marked(self):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.get_all_marked()

    def get_position_mapping(self, file_id_list):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.get_position_mapping(file_id_list)

    def get_cursor_by_pos(self, pos):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.get_cursor_by_pos(pos)

    def go(self, idx):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.go(idx)



class Cursor(EventDispatcher):
    filename = StringProperty(None,allownone=True)
    implementation = None
    pos = NumericProperty(None,allownone=True)
    file_id = NumericProperty(None,allownone=True)
    eol_implementation = None

    def __init__(self, **kwargs):
        super(Cursor, self).__init__(**kwargs)
        self.eol_implementation=EOLCursor()

    def get_app(self):
        return App.get_running_app()

    def set_implementation(self, instance):
        if self.implementation is not None:
            self.implementation.unbind(filename=self.on_filename_change, file_id=self.on_file_id_change,
                                       pos=self.on_pos_change)
        self.implementation = instance
        if instance==self.eol_implementation:
            self.filename = None
            self.file_id = None
            self.pos=self.eol_implementation.pos
        elif instance is not None:
            self.set_eol_implementation(self.implementation.clone().go_last())
            self.implementation.bind(filename=self.on_filename_change)
            self.implementation.bind(file_id=self.on_file_id_change)
            self.implementation.bind(pos=self.on_pos_change)
            self.pos = self.implementation.pos
            self.filename = self.implementation.filename
            self.file_id = self.implementation.file_id
        else:
            self.set_eol_implementation(None)
            self.filename = None
            self.file_id = None
            self.pos = None

    def set_eol_implementation(self,last_cursor):
        self.eol_implementation=EOLCursor(last_cursor=last_cursor,pos=last_cursor.pos+1)

    def on_pos_change(self, instance, value):
        self.pos = value

    def on_filename_change(self, instance, value):
        self.filename = value

    def on_file_id_change(self, instance, value):
        self.file_id = value

    def _set_new_impl(self,impl):
        if impl is None and not self.is_eol():
            self.set_implementation(self.eol_implementation)
        elif self.implementation==self.eol_implementation:
            self.set_implementation(impl)

    def go_next(self):
        self._set_new_impl(self.implementation.go_next())
        return True

    def go_previous(self):
        c = self.implementation.go_previous()
        if c is None and not self.is_eol():
            c = self.implementation.go_first()
        self._set_new_impl(c)
        return True

    def go_first(self):
        self._set_new_impl(self.implementation.go_first())
        return True

    def go_last(self):
        self._set_new_impl(self.implementation.go_last())
        return True

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
            c=self.implementation.go(idx)
            if c is None and not self.is_eol() and idx<0:
                c=self.implementation.go_first()
            self._set_new_impl(c)
            return True

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

    def is_eol(self):
        return self.implementation==self.eol_implementation

    def go_eol(self):
        self.set_implementation(self.eol_implementation)