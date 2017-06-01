import unittest
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.session.cursor import Cursor, EOLCursor, CursorInterface


class TestMainWidget(Widget):
    def execute_cmd(self, *args):
        pass


class TestApp(App):
    def build(self):
        return TestMainWidget()


class MockData():
    items = None
    marked = None
    tags = None
    clipboard = None

    def __init__(self):
        self.items = range(1000)
        self.marked = set()
        self.tags = {}
        self.clipboard = []


class MockCursor(CursorInterface):
    data = None

    def __init__(self):
        self.pos = 0
        self.file_id = 0
        self.filename = "f0"
        self.data = MockData()

    def get_mark(self):
        return self.file_id in self.data.marked

    def get_previous_ids(self, amount):
        return self.data.items[self.pos:self.pos - amount:-1]

    def get_tags(self):
        try:
            return list(self.data.tags[self.pos])
        except KeyError:
            return []

    def get_all_marked(self):
        return self.data.marked

    def go_first(self):
        return self.go(0)

    def go_last(self):
        return self.go(len(self.data.items) - 1)

    def get_thumbnail(self):
        return ""

    def __len__(self):
        return len(self.data.items)

    def get_marked_count(self):
        return len(self.data.marked)

    def go_previous(self):
        return self.go(self.pos - 1)

    def get_cursor_by_pos(self, pos):
        c = self.clone()
        c.go(pos)
        return c

    def mark(self, value):
        if value or value is None and not self.file_id in self.data.marked:
            self.data.marked.add(self.file_id)
        else:
            try:
                self.data.marked.remove(self.file_id)
            except KeyError:
                pass

    def get_next_ids(self, amount, self_included=False):
        return self.data.items[self.pos + 0 if self_included else 1:self.pos + amount + 0 if self_included else 1]

    def clone(self):
        c = MockCursor()
        c.pos = self.pos
        c.filename = self.filename
        c.file_id = self.file_id
        c.data = self.data
        return c

    def get_position_mapping(self, file_id_list):
        result = []
        for i in file_id_list:
            try:
                result.append((i, self.data.items.index(i)))
            except ValueError:
                pass
        return result

    def go_next(self):
        return self.go(self.pos + 1)

    def go(self, idx):
        if idx < 0 or idx >= len(self.data.items):
            return None
        else:
            self.pos = idx
            self.file_id = self.data.items[idx]
            self.filename = "f" + str(idx)
            return self

    def remove(self):
        to_remove = self.pos
        self.data.items.remove(to_remove)
        if self.pos >= len(self.data.items):
            self.pos -= 1

    def get(self, idx):
        return self.data.items[idx]

    def move_to(self, idx):
        value = self.data.items[self.pos]
        self.remove()
        self.data.items.insert(idx, value)
        self.go(idx)

    def cut_marked(self):
        if len(self.data.marked) > 0:
            self.data.clipboard = []
            for k in self.data.marked:
                self.data.clipboard.append(self.data.items[k])
            for v in self.data.clipboard:
                self.data.items.remove(v)

    def paste_marked(self, new_pos=None, append=False):
        if append:
            for v in self.data.clipboard:
                self.data.items.append(v)
        else:
            if new_pos is None:
                new_pos = self.pos
            if len(self.data.clipboard) > 0:
                p = max(0, min(new_pos, len(self.data.items)))
                for v in reversed(self.data.clipboard):
                    self.data.items.insert(p, v)

    def mark_all(self, value=None):
        if value or value is None and len(self.data.marked) < len(self.data.items):
            self.data.marked = set(self.data.items)
        else:
            self.data.marked = set()

    def invert_marked(self):
        new_set = set(self.data.items) - self.data.marked
        self.data.marked = new_set

    def add_tag(self, *args):
        if not self.data.tags.has_key(self.pos):
            self.data.tags[self.pos] = set()
        for tag in args:
            self.data.tags[self.pos].add(tag)

    def remove_tag(self, *args):
        if not self.data.tags.has_key(self.pos):
            self.data.tags[self.pos] = set()
        for tag in args:
            self.data.tags[self.pos].remove(tag)


class CursorTest(unittest.TestCase):
    def setUp(self):
        pass

    def _test_empty_cursor(self, app, *args):
        c = Cursor()
        self.assertIsNone(c.filename)
        self.assertIsNone(c.pos)
        self.assertIsNone(c.file_id)
        self.assertIsNone(c.implementation)
        self.assertIsInstance(c.eol_implementation, EOLCursor)

        c1 = c.clone()
        self.assertIsNone(c1.filename)
        self.assertIsNone(c1.pos)
        self.assertIsNone(c1.file_id)
        self.assertIsNone(c1.implementation)
        self.assertIsInstance(c1.eol_implementation, EOLCursor)
        self.assertNotEqual(c, c1)

        c.go_next()
        c.go_previous()
        c.go_first()
        c.go_last()

        c.go_eol()
        self.assertIsInstance(c1.eol_implementation, EOLCursor)

        app.stop()

    def _test_set_implementation(self, app, *args):
        c = Cursor()
        c.set_implementation(MockCursor())
        self.assertEqual(0, c.pos)
        self.assertEqual(0, c.file_id)
        app.stop()

    def _test_navigate(self, app, *args):
        c = Cursor()
        c.set_implementation(MockCursor())
        self.assertEqual(0, c.pos)
        c.go_next()
        self.assertEqual(1, c.pos)
        c.go_previous()
        self.assertEqual(0, c.pos)
        for i in range(5):
            c.go_next()
        self.assertEqual(5, c.pos)
        c.go_first()
        self.assertEqual(0, c.pos)
        c.go_previous()
        self.assertEqual(0, c.pos)
        c.go(200)
        self.assertEqual(200, c.pos)
        self.assertFalse(c.is_eol())
        c.go_last()
        self.assertEqual(999, c.pos)
        c.go_next()
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)
        c.go_next()
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)
        c.go_previous()
        self.assertEqual(999, c.pos)

        c.go_eol()
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)
        c.go_first()
        self.assertEqual(0, c.pos)
        self.assertFalse(c.is_eol())
        c.go_eol()
        c.go_eol()
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)

        c.go(500)
        self.assertEqual(500, c.pos)
        self.assertFalse(c.is_eol())

        c.go(-5)
        self.assertEqual(0, c.pos)
        self.assertFalse(c.is_eol())

        c.go(1001)
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)

        c.go(2000)
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)
        c.go_first()
        c.go(2000)
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)
        c.go_previous()
        self.assertEqual(999, c.pos)

        app.stop()

    def _test_move_items(self, app, *args):
        c = Cursor()
        c.set_implementation(MockCursor())
        c.go(5)
        c.move_to(4)
        self.assertEqual(4, c.pos)
        self.assertEqual(5, c.file_id)
        c.go(5)
        self.assertEqual(5, c.pos)
        self.assertEqual(4, c.file_id)

        c.go(20)
        c.move_to(10)
        self.assertEqual(10, c.pos)
        self.assertEqual(20, c.file_id)
        c.go_next()
        self.assertEqual(11, c.pos)
        self.assertEqual(10, c.file_id)
        c.go_next()
        self.assertEqual(12, c.pos)
        self.assertEqual(11, c.file_id)
        c.go(20)
        self.assertEqual(20, c.pos)
        self.assertEqual(19, c.file_id)
        c.go_next()
        self.assertEqual(21, c.pos)
        self.assertEqual(21, c.file_id)
        c.go_previous()
        self.assertEqual(20, c.pos)
        self.assertEqual(19, c.file_id)

        c.go(30)
        c.move_to(35)
        self.assertEqual(35, c.pos)
        self.assertEqual(30, c.file_id)
        c.go_next()
        self.assertEqual(36, c.pos)
        self.assertEqual(36, c.file_id)
        c.go(30)
        self.assertEqual(30, c.pos)
        self.assertEqual(31, c.file_id)
        c.go(34)
        self.assertEqual(34, c.pos)
        self.assertEqual(35, c.file_id)

        # cases with first place

        c.go_first()
        c.move_to(2)
        self.assertEqual(2, c.pos)
        self.assertEqual(0, c.file_id)
        c.go_first()
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)
        c.go(500)
        c.move_to(0)
        self.assertEqual(0, c.pos)
        self.assertEqual(500, c.file_id)
        c.go_next()
        self.assertEqual(1, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_previous()
        c.go_previous()
        self.assertEqual(0, c.pos)
        self.assertEqual(500, c.file_id)

        # cases with last place
        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(999, c.file_id)
        c.move_to(990)
        self.assertEqual(990, c.pos)
        self.assertEqual(999, c.file_id)
        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(998, c.file_id)
        c.go_next()
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())
        c.go_next()
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())
        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(998, c.file_id)
        c.go(995)
        c.move_to(999)
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)
        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)
        c.go_next()
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())
        c.go_previous()
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)

        # case with eol
        c.go(999)
        c.move_to(1000)
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)
        c.go_eol()
        c.move_to(700)
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())
        c.go_previous()
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)
        c.go(700)
        self.assertEqual(700, c.pos)
        self.assertEqual(700, c.file_id)
        self.assertFalse(c.is_eol())
        c.go_eol()
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())
        c.go_previous()
        self.assertEqual(999, c.pos)
        self.assertEqual(994, c.file_id)
        c.go_eol()
        c.go_first()
        self.assertEqual(0, c.pos)
        self.assertEqual(500, c.file_id)
        c.go_eol()
        for i in range(3):
            c.go_next()
        self.assertEqual(1000, c.pos)
        self.assertTrue(c.is_eol())

        app.stop()

    def _test_mark(self, app, *args):
        c = Cursor()
        c.set_implementation(MockCursor())
        self.assertFalse(c.get_mark())

        # test marking
        c.mark()
        self.assertTrue(c.get_mark())
        c.go_next()
        self.assertFalse(c.get_mark())
        c.mark(True)
        self.assertTrue(c.get_mark())
        c.go_next()
        self.assertFalse(c.get_mark())
        c.go_first()
        self.assertTrue(c.get_mark())

        self.assertEqual(2, c.get_marked_count())

        # test unmarking
        c.mark()
        self.assertFalse(c.get_mark())
        c.go_next()
        c.mark()
        self.assertFalse(c.get_mark())
        c.go_next()
        c.mark(False)
        self.assertFalse(c.get_mark())
        self.assertEqual(0, c.get_marked_count())

        # test cut & paste
        c.go(5)
        self.assertEqual(5, c.file_id)
        c.mark()
        c.go_first()
        c.cut_marked()
        self.assertEqual(999, len(c))
        c.go(5)
        self.assertEqual(5, c.pos)
        self.assertEqual(6, c.file_id)
        c.go(1)
        c.paste_marked()
        self.assertEqual(1000, len(c))
        self.assertEqual(1, c.pos)
        self.assertEqual(5, c.file_id)
        c.go(10)
        for i in range(20):
            c.mark()
            c.go_next()
        c.go(10)
        c.cut_marked()
        self.assertEqual(10, c.pos)
        self.assertEqual(30, c.file_id)
        c.go_next()
        self.assertEqual(11, c.pos)
        self.assertEqual(31, c.file_id)
        c.go_previous()
        c.paste_marked()
        self.assertEqual(10, c.pos)
        self.assertEqual(10, c.file_id)
        c.go_next()
        self.assertEqual(11, c.pos)
        self.assertEqual(11, c.file_id)

        # reset cursor
        c = Cursor()
        c.set_implementation(MockCursor())

        # test special cases like first and last
        c.go_first()
        c.mark()
        c.cut_marked()
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_previous()
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_next()
        self.assertEqual(1, c.pos)
        self.assertEqual(2, c.file_id)
        c.paste_marked()
        self.assertEqual(1, c.pos)
        self.assertEqual(0, c.file_id)
        c.go_next()
        self.assertEqual(2, c.pos)
        self.assertEqual(2, c.file_id)

        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(999, c.file_id)
        c.mark()
        self.assertTrue(c.get_mark())
        c.cut_marked()
        self.assertEqual(999, c.pos)
        self.assertIsNone(c.file_id)
        self.assertTrue(c.is_eol())
        c.paste_marked()
        self.assertEqual(999, c.pos)
        self.assertEqual(999, c.file_id)
        self.assertFalse(c.is_eol())

        # reset cursor
        c = Cursor()
        c.set_implementation(MockCursor())

        # test cut all
        c.mark_all()
        c.cut_marked()
        self.assertTrue(c.is_eol())
        self.assertEqual(0, c.pos)
        self.assertIsNone(c.file_id)
        self.assertEqual(0, len(c))
        c.paste_marked()
        self.assertFalse(c.is_eol())
        self.assertEqual(1000, len(c))
        self.assertEqual(0, c.pos)
        self.assertEqual(0, c.file_id)
        c.go_next()
        self.assertEqual(1, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_previous()
        c.go_previous()
        self.assertEqual(0, c.pos)
        self.assertEqual(0, c.file_id)
        c.go_last()
        self.assertEqual(999, c.pos)
        self.assertEqual(999, c.file_id)
        c.go_next()
        self.assertTrue(c.is_eol())
        self.assertEqual(1000, c.pos)

        c.mark_all(True)
        c.cut_marked()
        c.cut_marked()
        self.assertTrue(c.is_eol())
        self.assertEqual(0, c.pos)
        self.assertIsNone(c.file_id)
        self.assertEqual(0, len(c))
        c.paste_marked()
        self.assertFalse(c.is_eol())
        self.assertEqual(1000, len(c))
        self.assertEqual(0, c.pos)
        self.assertEqual(0, c.file_id)

        app.stop()

    def _test_advanced_mark(self, app, *args):

        def test_eol(c):
            self.assertTrue(c.is_eol())
            self.assertEqual(0, c.pos)
            self.assertIsNone(c.file_id)
            self.assertEqual(0, len(c))

        c = Cursor()
        c.set_implementation(MockCursor())
        c.go(500)
        c.mark_all()
        c.cut_marked()
        test_eol(c)
        c.go_previous()
        test_eol(c)
        c.go_next()
        test_eol(c)
        c.go_first()
        test_eol(c)
        c.go_last()
        test_eol(c)
        c.go_eol()
        test_eol(c)
        c.go(200)
        test_eol(c)
        c.go_previous()
        test_eol(c)
        c.go_next()
        test_eol(c)

        c.paste_marked()
        self.assertFalse(c.is_eol())
        self.assertEqual(1000, len(c))
        self.assertEqual(0, c.pos)
        self.assertEqual(0, c.file_id)
        c.go_next()
        self.assertEqual(1, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_clone(self, app, *args):
        c = Cursor()
        c.set_implementation(MockCursor())
        c.go(300)
        c.mark()
        self.assertEqual(c.pos, 300)
        c1 = c.clone()
        self.assertEqual(c1.pos, 300)
        self.assertEqual(c1.eol_implementation, c.eol_implementation)
        self.assertEqual(c1.file_id, c.file_id)
        self.assertEqual(c1.filename, c.filename)
        self.assertEqual(c1.get_marked_count(), 1)
        c.mark_all(False)
        self.assertEqual(c1.get_marked_count(), c.get_marked_count())

        c.go_eol()
        c1 = c.clone()
        self.assertEqual(c1.pos, c1.pos)
        self.assertEqual(c1.eol_implementation, c.eol_implementation)
        self.assertEqual(c1.file_id, c.file_id)
        self.assertEqual(c1.filename, c.filename)
        self.assertEqual(1000, c1.pos)
        c1.go_previous()
        self.assertEqual(999, c1.pos)
        self.assertEqual(999, c1.file_id)

        app.stop()

    def _test_position_mapping(self, app, *args):

        def get_map(id_list):
            return [(r[0], r[1]) for r in c.get_position_mapping(id_list)]

        c = Cursor()
        c.set_implementation(MockCursor())

        self.assertItemsEqual([(1, 1), (3, 3), (5, 5)], get_map([1, 3, 5]))

        app.stop()

    def _test_tags(self, app, *args):

        c = Cursor()
        c.set_implementation(MockCursor())

        c.add_tag("one")
        self.assertItemsEqual(c.get_tags(), ["one"])
        c.add_tag("two")
        self.assertItemsEqual(c.get_tags(), ["one", "two"])
        c.remove_tag("one")
        self.assertItemsEqual(c.get_tags(), ["two"])
        c.add_tag("three")
        self.assertItemsEqual(c.get_tags(), ["two", "three"])
        c.remove_tag("three", "two")
        self.assertItemsEqual(c.get_tags(), [])
        c.add_tag("one", "two")
        self.assertItemsEqual(c.get_tags(), ["one", "two"])

        c = Cursor()
        c.set_implementation(MockCursor())
        c.go_last()
        c.add_tag("a")
        c.go_previous()
        c.add_tag("1", "2")
        c.go_first()
        self.assertItemsEqual(c.get_tags(), [])
        c.go_next()
        c.go_last()
        self.assertItemsEqual(c.get_tags(), ["a"])

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_empty_cursor(self):
        self.call_test(self._test_empty_cursor)

    def test_set_impl(self):
        self.call_test(self._test_set_implementation)

    def test_navigate(self):
        self.call_test(self._test_navigate)

    def test_move_items(self):
        self.call_test(self._test_move_items)

    def test_mark(self):
        self.call_test(self._test_mark)

    def test_advanced_mark(self):
        self.call_test(self._test_advanced_mark)

    def test_clone(self):
        self.call_test(self._test_clone)

    def test_position_mapping(self):
        self.call_test(self._test_position_mapping)

    def test_tags(self):
        self.call_test(self._test_tags)


if __name__ == "__main__":
    unittest.main()
