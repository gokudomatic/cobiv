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

    def get_next_ids(self, amount, self_included=False):
        return []

    def get_previous_ids(self, amount):
        return []

    def go(self, idx):
        return None

    def get_tags(self):
        return []

    def mark(self, value):
        pass

    def get_mark(self):
        return False

    def get_marked_count(self):
        return 0

    def get_all_marked(self):
        return False

    def remove(self):
        return False

    def __len__(self):
        return 0

    def get_cursor_by_pos(self, pos):
        return None

    def move_to(self, idx):
        return None

    def get_position_mapping(self, file_id_list):
        return []

    def cut_marked(self):
        pass

    def paste_marked(self, new_pos, append=False):
        pass

    def mark_all(self, value=None):
        pass

    def invert_marked(self):
        pass

class EOLCursor(CursorInterface):
    last_cursor = ObjectProperty(None)

    def clone(self):
        return EOLCursor(last_cursor=self.last_cursor)

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
            return self.last_cursor.go_last()

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

    def get_marked_count(self):
        if self.last_cursor is None:
            return 0
        else:
            return self.last_cursor.get_marked_count()

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

    def go_next(self):
        return self

    def paste_marked(self, new_pos=None, append=False):
        if self.last_cursor is not None:
            self.last_cursor.paste_marked(new_pos,append=True)

    def cut_marked(self):
        if self.last_cursor is not None:
            self.last_cursor.cut_marked()

    def mark_all(self, value=None):
        if self.last_cursor is not None:
            self.last_cursor.mark_all(value)

    def invert_marked(self):
        if self.last_cursor is not None:
            self.last_cursor.invert_marked()

    def update_pos(self):
        if self.last_cursor is not None:
            last=self.last_cursor.go_last()
            if last is None:
                self.pos=0
            else:
                self.pos=last.pos+1

class Cursor(EventDispatcher):
    filename = StringProperty(None, allownone=True)
    implementation = None
    pos = NumericProperty(None, allownone=True)
    file_id = NumericProperty(None, allownone=True)
    eol_implementation = None

    def __init__(self, **kwargs):
        super(Cursor, self).__init__(**kwargs)
        self.eol_implementation = EOLCursor()

    def clone(self):
        new_cursor = Cursor()
        if self.implementation is not None:
            new_cursor.implementation = self.implementation.clone()
        new_cursor.pos = self.pos
        new_cursor.file_id = self.file_id
        new_cursor.filename = self.filename
        new_cursor.eol_implementation = self.eol_implementation
        return new_cursor

    def get_app(self):
        return App.get_running_app()

    def set_implementation(self, instance):
        if instance == self.implementation or instance is None and isinstance(self.implementation,EOLCursor):
            return

        if not isinstance(instance, CursorInterface) and instance is not None:
            raise NameError("instance is not a CursorImplementation")

        if self.implementation is not None:
            self.implementation.unbind(filename=self.on_filename_change, file_id=self.on_file_id_change,
                                       pos=self.on_pos_change)
        self.implementation = instance
        if instance == self.eol_implementation:
            self.filename = None
            self.file_id = None
            self.pos = self.eol_implementation.pos
            self.implementation.bind(pos=self.on_pos_change)
        elif instance is not None:
            if instance.pos is not None:
                c = instance.clone()
                c.go_last()
                self.set_eol_implementation(c)
            else:
                self.set_eol_implementation(None)
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

    def set_eol_implementation(self, last_cursor):
        if not isinstance(last_cursor, CursorInterface) and last_cursor is not None:
            raise NameError("last_cursor is not a Cursor")

        if last_cursor is not None:
            self.eol_implementation = EOLCursor(last_cursor=last_cursor, pos=last_cursor.pos + 1)
        else:
            self.eol_implementation = EOLCursor()

    def on_pos_change(self, instance, value):
        self.pos = value

    def on_filename_change(self, instance, value):
        self.filename = value

    def on_file_id_change(self, instance, value):
        self.file_id = value

    def _set_new_impl(self, impl):
        if impl is None and not self.is_eol():
            self.set_implementation(self.eol_implementation)
        elif isinstance(self.implementation, EOLCursor):
            self.set_implementation(impl)

    def go_next(self):
        if self.implementation is not None:
            self._set_new_impl(self.implementation.go_next())
        return True

    def go_previous(self):
        if self.implementation is not None:
            c = self.implementation.go_previous()
            if c is None and not self.is_eol():
                c = self.implementation.go_first()
            if c is not None:
                self._set_new_impl(c)
        return True

    def go_first(self):
        if self.implementation is not None:
            self._set_new_impl(self.implementation.go_first())
        return True

    def go_last(self):
        if self.implementation is not None:
            self._set_new_impl(self.implementation.go_last())
        return True

    def get(self, idx):
        return self.implementation.get(idx)

    def get_next_ids(self, amount, self_included=False):
        return self.implementation.get_next_ids(amount, self_included=self_included)

    def get_previous_ids(self, amount):
        return self.implementation.get_previous_ids(amount)

    def go(self, idx, force=False):
        if not force and self.pos is not None and idx == self.pos:
            return True
        else:
            c = self.implementation.go(idx)
            if c is None and not self.is_eol() and idx < 0:
                c = self.implementation.go_first()
            elif c is None and self.is_eol() and idx>self.pos:
                return True
            elif c is None and self.is_eol():
                self.implementation.pos=0
                return True
            self._set_new_impl(c)
            return True

    def get_tags(self):
        return self.implementation.get_tags()

    def mark(self, value=None):
        self.implementation.mark(value)
        self.get_app().root.execute_cmd("refresh-marked")

    def get_mark(self):
        return self.implementation.get_mark()

    def get_all_marked(self):
        return self.implementation.get_all_marked()

    def get_marked_count(self):
        return self.implementation.get_marked_count()

    def remove(self):
        return self.implementation.remove()

    def __len__(self):
        return self.implementation.__len__()

    def get_cursor_by_pos(self, pos):
        c = self.clone()
        c.go(pos)
        return c

    def move_to(self, idx):
        if idx < 0:
            idx = 0
        else:
            current_size = len(self)
            if idx >= current_size:
                idx = current_size - 1

        result = self.implementation.move_to(idx)
        if idx == len(self.implementation) - 1:
            self.update_eol_implementation()
        return result

    def get_position_mapping(self, file_id_list):
        return self.implementation.get_position_mapping(file_id_list)

    def is_eol(self):
        return isinstance(self.implementation, EOLCursor)

    def go_eol(self):
        self.set_implementation(self.eol_implementation)

    def update_eol_implementation(self):
        self.set_eol_implementation(self.implementation.clone().go_last())

    def get_last(self):
        c = self.clone()
        c.go_last()
        return c

    def cut_marked(self):
        if self.implementation is not None:
            if self.implementation.get_marked_count()>0:
                self.implementation.cut_marked()
                self.go(self.pos,force=True)
                if self.is_eol():
                    self.implementation.update_pos()
                    # self.pos=
                self.mark_all(False)

    def paste_marked(self, new_pos=None):
        if self.implementation is not None:
            self.implementation.paste_marked(new_pos)
            self.go(self.pos,force=True)

    def mark_all(self, value=None):
        if self.implementation is not None:
            self.implementation.mark_all(value)

    def invert_marked(self):
        if self.implementation is not None:
            self.implementation.invert_marked()
