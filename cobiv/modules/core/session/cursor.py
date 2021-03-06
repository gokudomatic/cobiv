from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty, ObjectProperty


class CursorInterface(EventDispatcher):
    filename = StringProperty(None, allownone=True)
    repo_key = NumericProperty(None, allownone=True)
    pos = NumericProperty(None, allownone=True)
    file_id = NumericProperty(None, allownone=True)

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

    def get_all_marked(self, offset=0, limit=0):
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

    def paste_marked(self, new_pos=None, append=False):
        pass

    def mark_all(self, value=None):
        pass

    def invert_marked(self):
        pass

    def add_tag(self, *args):
        pass

    def add_tag_to_marked(self, *args):
        pass

    def remove_tag(self, *args):
        pass

    def remove_tag_to_marked(self, *args):
        pass

    def get_tags(self):
        return []

    def get_clipboard_size(self):
        return 0

    def sort(self, *fields):
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

    def get_all_marked(self, offset, limit):
        if self.last_cursor is None:
            return None
        else:
            return self.last_cursor.get_all_marked(offset, limit)

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
            self.last_cursor.paste_marked(new_pos, append=True)

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
            last = self.last_cursor.go_last()
            if last is None:
                self.pos = 0
            else:
                self.pos = last.pos + 1

    def update_last(self):
        if self.last_cursor is not None:
            self.last_cursor = self.last_cursor.go_last()

    def get_clipboard_size(self):
        if self.last_cursor is None:
            return 0
        else:
            return self.last_cursor.get_clipboard_size()


class Cursor(EventDispatcher):
    filename = StringProperty(None, allownone=True)
    repo_key = NumericProperty(None, allownone=True)
    implementation = None
    pos = NumericProperty(None, allownone=True)
    file_id = NumericProperty(None, allownone=True)
    eol_implementation = None
    tags = None
    size = None

    def __init__(self, **kwargs):
        super(Cursor, self).__init__(**kwargs)
        self.eol_implementation = EOLCursor()

    def clone(self):
        new_cursor = Cursor()
        if self.implementation is not None:
            new_cursor.implementation = self.implementation.clone()
            new_cursor.implementation.bind(filename=new_cursor.on_filename_change)
            new_cursor.implementation.bind(repo_key=new_cursor.on_repo_key_change)
            new_cursor.implementation.bind(file_id=new_cursor.on_file_id_change)
            new_cursor.implementation.bind(pos=new_cursor.on_pos_change)

        new_cursor.pos = self.pos
        new_cursor.file_id = self.file_id
        new_cursor.filename = self.filename
        new_cursor.repo_key = self.repo_key
        new_cursor.eol_implementation = self.eol_implementation
        new_cursor.tags = self.tags
        new_cursor.size = self.size
        return new_cursor

    def get_app(self):
        return App.get_running_app()

    def set_implementation(self, instance):
        self.tags = None
        if instance == self.implementation or instance is None and isinstance(self.implementation, EOLCursor):
            return

        if not isinstance(instance, CursorInterface) and instance is not None:
            raise NameError("instance is not a CursorImplementation")

        if self.implementation is not None:
            self.implementation.unbind(filename=self.on_filename_change, file_id=self.on_file_id_change,
                                       pos=self.on_pos_change, repo_key=self.on_repo_key_change)
        self.implementation = instance
        if instance == self.eol_implementation:
            self.filename = None
            self.repo_key = None
            self.file_id = None
            self.size = None
            self.pos = self.eol_implementation.pos
            self.implementation.bind(pos=self.on_pos_change)
        elif instance is not None:
            self.size = self.size if self.size > 0 else None
            if instance.pos is not None:
                c = instance.clone()
                c.go_last()
                self.set_eol_implementation(c)
            else:
                self.set_eol_implementation(None)
            self.implementation.bind(filename=self.on_filename_change, file_id=self.on_file_id_change,
                                     pos=self.on_pos_change, repo_key=self.on_repo_key_change)
            self.pos = self.implementation.pos
            self.repo_key = self.implementation.repo_key
            self.filename = self.implementation.filename
            self.file_id = self.implementation.file_id

        else:
            self.set_eol_implementation(None)
            self.filename = None
            self.repo_key = None
            self.file_id = None
            self.pos = None
            self.size = None

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

    def on_repo_key_change(self, instance, value):
        self.repo_key = value

    def on_file_id_change(self, instance, value):
        self.tags = None
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

    def reload(self):
        if self.is_eol():
            self.implementation.update_last()
        else:
            self.go(self.pos, force=True)

    def go(self, idx, force=False):
        if not force and self.pos is not None and idx == self.pos:
            return True
        else:
            self.tags = None
            c = self.implementation.go(idx)
            if c is None and not self.is_eol() and idx < 0:
                c = self.implementation.go_first()
                return True
            elif c is None and self.is_eol() and idx > self.pos:
                return True
            elif c is None and self.is_eol():
                self.pos = 0
                self.implementation.pos = 0
                return True
            else:
                if c is None and self.eol_implementation.pos > 0 and idx == 0:
                    self.eol_implementation.pos = 0
                self._set_new_impl(c)
                return True

    def get_tags(self):
        if self.implementation is None:
            return []

        if self.tags is None:
            self.tags = [{}, {}]
            for cat, kind, value in self.implementation.get_tags():
                if kind not in self.tags[int(cat)]:
                    self.tags[int(cat)][kind] = []
                self.tags[int(cat)][kind].append(value)
        return self.tags

    def get_tag(self, category, kind, index):
        results = self.get_tag_list(category=category, kind=kind)
        return results[index] if len(results) > index else None

    def get_tag_list(self, category, kind):
        if self.implementation is None:
            return []

        if self.tags is None:
            self.get_tags()

        if kind in self.tags[category]:
            return self.tags[category][kind]
        else:
            return []

    def mark(self, value=None):
        self.implementation.mark(value)
        self.get_app().root.execute_cmds("refresh-marked")

    def get_mark(self):
        return self.implementation.get_mark()

    def get_all_marked(self, offset=0, limit=0):
        return self.implementation.get_all_marked(offset, limit)

    def get_marked_count(self):
        return self.implementation.get_marked_count()

    def remove(self):
        return self.implementation.remove()

    def __len__(self):
        if self.size is None:
            self.size = self.implementation.__len__() if self.implementation is not None else 0
        return self.size

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
            if self.implementation.get_marked_count() > 0:
                self.size = None
                self.implementation.cut_marked()
                self.go(min(self.pos, len(self)), force=True)
                if self.is_eol():
                    self.implementation.update_pos()
                self.mark_all(False)

    def paste_marked(self, new_pos=None, append=False, update_cursor=True):
        if self.implementation is not None:
            self.size = None
            self.implementation.paste_marked(new_pos=new_pos, append=append)
            if update_cursor:
                self.go(self.pos, force=True)

    def mark_all(self, value=None):
        if self.implementation is not None:
            self.implementation.mark_all(value)

    def invert_marked(self):
        if self.implementation is not None:
            self.implementation.invert_marked()

    def add_tag(self, *args):
        if self.implementation is not None:
            self.implementation.add_tag(*args)
            self.tags = None

    def add_tag_to_marked(self, *args):
        if self.implementation is not None:
            self.implementation.add_tag_to_marked(*args)
            self.tags = None

    def remove_tag(self, *args):
        if self.implementation is not None:
            self.implementation.remove_tag(*args)
            self.tags = None

    def remove_tag_to_marked(self, *args):
        if self.implementation is not None:
            self.implementation.remove_tag_to_marked(*args)
            self.tags = None

    def get_clipboard_size(self):
        if self.implementation is not None:
            return self.implementation.get_clipboard_size()
        else:
            return 0

    def sort(self, *fields):
        if self.implementation is not None:
            self.implementation.sort(*fields)

    def mark_dirty(self):
        self.size = None
        self.pos = 0
