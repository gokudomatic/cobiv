import os
import unittest
from functools import partial
from os.path import expanduser
from time import sleep

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout

from cobiv.modules.core.entity import Entity
from cobiv.modules.core.session.Session import Session
from cobiv.modules.database.sqlitedb.sqlitedb import SqliteDb
from cobiv.modules.views.browser.browser import Browser
from cobiv.modules.views.browser.eolitem import EOLItem
from cobiv.modules.hud_components.sidebar.sidebar import Sidebar
from modules.database.datasources.sqlite.sqliteds import Sqliteds
from modules.database.sqlitedb.sqlitesetmanager import SqliteSetManager
from test.AbstractApp import AbstractApp

Window.size = (360, 360)


class TestMainWidget(GridLayout):
    def execute_cmd(self, action, *args, **kwargs):
        if action == "load-set":
            self.browser.load_set()
        elif action == "refresh-marked":
            self.browser.refresh_mark()
        else:
            pass

    def execute_cmds(self, *args, **kwargs):
        return self.execute_cmd(*args, **kwargs)

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass

    def set_browser(self, instance):
        self.browser = instance
        self.add_widget(instance)


class MockThumbloader(Entity):
    def __init__(self):
        super(MockThumbloader, self).__init__()
        self.thumb_path = os.path.join(expanduser('~'), '.cobiv', 'thumbnails')
        self.cell_size = 120

    def stop(self):
        pass

    def restart(self):
        pass

    def get_fullpath_from_file_id(self, file_id):
        return None

    def append(self, *items):
        pass

    def clear_cache(self):
        pass

    def get_filename_caption(self, filename):
        name = os.path.basename(filename)
        if len(name) > 12:
            name = name[:5] + "..." + name[-7:]
        return name

    def delete_thumbnail(self, *items):
        pass


class TestApp(AbstractApp):
    session = None

    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbnails.path': '',
            'repositories': ['osfs://images'],
            'thumbnails.path': self.get_user_path('thumbs')
        }
        self.ds = Sqliteds()

    def build(self):
        return TestMainWidget(size_hint=(1, 1), cols=1)

    def lookup(self, object_name, category):
        if category == "Entity" and object_name == "session":
            return self.session
        elif category == "Entity" and object_name == "thumbloader":
            return MockThumbloader()
        elif object_name == "sqlite_ds":
            return self.ds
        elif object_name == 'sqliteSetManager':
            return SqliteSetManager()
        else:
            return None


class BrowserTest(unittest.TestCase):
    def setUp(self):
        Clock._events = [[] for i in range(256)]

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def prepare_browser(self, app):
        app.session = Session()

        db = SqliteDb()
        db.init_test_db(app.session)

        b = Browser()

        app.root.set_browser(b)
        b.ready()
        b.on_switch(loader_thread=False)

        sleep(0.1)
        Clock.tick()

        return b, db

    def proceed_search(self, db, query=None):
        if query is not None:
            db.search_tag(query)
        else:
            db.search_tag()
        sleep(0.1)
        for i in range(2):
            Clock.tick()

    def _test_initialization(self, app, *args):
        b, db = self.prepare_browser(app)
        self.assertEqual(0, len(b.image_queue))

        self.assertEqual(len(b.grid.children), 1)
        self.assertCountEqual((360, 360), Window.size)
        self.assertCountEqual((1, 1), b.size_hint)
        self.assertCountEqual((360, 360), b.size)

        app.stop()

    def _test_load_set(self, app, *args):
        b, db = self.prepare_browser(app)
        self.assertEqual(0, len(b.image_queue))

        db.search_tag()
        sleep(0.1)
        Clock.tick()
        self.assertEqual(27, len(b.image_queue))

        for i in range(27):
            self.assertEqual("/%04d.jpg" % (i + 1,), b.image_queue[i][3])
        Clock.tick()

        self.assertEqual(len(b.grid.children), 27)

        self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos, b.cursor.pos)

        app.stop()

    def _test_basic_moves(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)

        cursor = b.cursor
        for i in range(10):
            b.select_next(0)
            Clock.tick()
            self.assertEqual(i + 1, cursor.pos)
            self.assertFalse(b.cursor.is_eol())
            self.assertNotEqual(b.page_cursor.pos, b.cursor.pos)
        for i in range(10):
            b.select_previous(0)
            Clock.tick()
            self.assertEqual(10 - i - 1, cursor.pos)
            self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos, b.cursor.pos)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(3, cursor.pos)
        b.select_next(0)
        b.select_down(0)
        Clock.tick()
        self.assertEqual(7, cursor.pos)
        b.select_next(0)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(5, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(2, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(0, cursor.pos)

        app.stop()

    def _test_load_more(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        for i in range(7):
            b.select_down(0)
            Clock.tick()

        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(21, cursor.pos)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(3, b.page_cursor.pos)
        self.assertEqual(24, cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        for i in range(23):
            b.select_down(0)
            Clock.tick()
        self.assertEqual(93, cursor.pos)
        self.assertEqual(72, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        b.select_down(0)
        Clock.tick()

        self.assertEqual(96, cursor.pos)
        self.assertEqual(len(b.grid.children), 26)
        self.assertEqual(75, b.page_cursor.pos)

        b.select_down(0)
        Clock.tick()

        self.assertEqual(99, cursor.pos)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(len(b.grid.children), 26)
        self.assertEqual(75, b.page_cursor.pos)

        # moving up
        b.select_up(0)
        Clock.tick()
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(97, cursor.pos)
        self.assertFalse(cursor.is_eol())

        for i in range(8):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(69, b.page_cursor.pos)
        self.assertEqual(73, cursor.pos)

        for i in range(24):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(1, cursor.pos)

        b.select_up(0)
        Clock.tick()

        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(0, cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()

    def _test_go(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        # go same pos
        b.select_next(0)
        b.select_custom(cursor.pos)
        self.assertEqual(1, cursor.pos)
        self.assertEqual("/0002.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go same page
        b.select_custom(8)
        Clock.tick()
        self.assertEqual(8, cursor.pos)
        self.assertEqual("/0009.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go end of current page
        b.select_custom(25)
        Clock.tick()
        self.assertEqual(25, cursor.pos)
        self.assertEqual("/0026.jpg", cursor.filename)
        self.assertEqual(3, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go another page
        b.select_custom(70)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(70, cursor.pos)
        self.assertEqual("/0071.jpg", cursor.filename)
        self.assertEqual(len(b.grid.children), 27)
        self.assertEqual(54, b.page_cursor.pos)

        b.select_custom(69)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(69, cursor.pos)
        self.assertEqual("/0070.jpg", cursor.filename)
        self.assertEqual(54, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # go multiple times
        b.select_custom(5)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        b.select_custom(40)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        b.select_custom(80)
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(80, cursor.pos)
        self.assertEqual("/0081.jpg", cursor.filename)
        self.assertEqual(66, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()

    def _test_first_last(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        # test first / same page
        for i in range(5):
            b.select_first()
            Clock.tick()
        self.assertEqual(0, cursor.pos)
        self.assertEqual("/0001.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        for i in range(5):
            for j in range(i + 1):
                b.select_next(0)
            b.select_first()
            Clock.tick()

            self.assertEqual(0, cursor.pos)
            self.assertEqual("/0001.jpg", cursor.filename)
            self.assertEqual(0, b.page_cursor.pos)
            self.assertEqual(len(b.grid.children), 27)

        # test first / other page
        b.select_custom(60)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(len(b.grid.children), 27)

        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, cursor.pos)
        self.assertEqual("/0001.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # test last
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("/0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_previous(0)
        b.select_previous(0)
        b.select_previous(0)
        self.assertEqual(96, cursor.pos)
        self.assertEqual("/0097.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)
        Clock.tick()
        b.select_last()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("/0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        app.stop()

    def _test_eol_basic(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        # test previous & next
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        for i in range(5):
            b.select_next(0)
            Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_previous(0)
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("/0100.jpg", cursor.filename)
        self.assertFalse(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)

        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())

        # test up & bottom
        b.select_up(0)
        Clock.tick()
        self.assertEqual(97, cursor.pos)
        self.assertEqual("/0098.jpg", cursor.filename)
        self.assertFalse(cursor.is_eol())
        self.assertEqual(75, b.page_cursor.pos)

        for i in range(3):
            b.select_down(0)
            Clock.tick()
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())

        # test first & last

        b.select_last()
        Clock.tick()
        self.assertEqual(99, cursor.pos)
        self.assertEqual("/0100.jpg", cursor.filename)
        self.assertEqual(75, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 26)

        b.select_next(0)
        self.assertEqual(100, cursor.pos)
        self.assertTrue(cursor.is_eol())

        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, cursor.pos)
        self.assertEqual("/0001.jpg", cursor.filename)
        self.assertEqual(0, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        # test custom go
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        self.assertEqual(100, cursor.pos)

        b.select_custom(50)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(50, cursor.pos)
        self.assertEqual("/0051.jpg", cursor.filename)
        self.assertEqual(36, b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()

    def _test_mark(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(0, len(marked))

        b.select_custom(3)
        b.mark_current(True)

        for i in range(3):
            b.select_next(0)
            b.select_next(0)
            # Clock.tick()
            b.mark_current(True)

        self.assertEqual(4, cursor.get_marked_count())
        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertCountEqual([3, 5, 7, 9], marked)

        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertCountEqual([], marked)

        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertCountEqual([3, 5, 7, 9], marked)

        b.select_custom(5)
        b.mark_current()

        # test load more
        for i in range(11):
            b.select_down(0)
            Clock.tick()

        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertCountEqual([], marked)

        # test load more
        for i in range(10):
            b.select_up(0)
            Clock.tick()

        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertCountEqual([3, 7, 9], marked)

        cursor.mark_all()
        b.refresh_mark()
        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(27, len(marked))

        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(25, len(marked))

        # test eol
        b.select_last()
        sleep(0.1)
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        cursor.mark_all()
        b.refresh_mark()
        marked = [e.position for e in b.grid.children if e.is_marked()]
        self.assertEqual(0, len(marked))

        app.stop()

    def _test_cut_1(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        def cut_one():
            self.proceed_search(db)
            b.select_custom(4)
            b.mark_current()
            Clock.tick()

        def cut_row():
            self.proceed_search(db)
            for i in range(6, 9):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        def cut_page():
            self.proceed_search(db)
            for i in range(27):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        def cut_all():
            self.proceed_search(db)
            cursor.mark_all()
            Clock.tick()

        def get_filenames(c, qty):
            pc = c.clone()
            filenames = []
            for i in range(qty):
                filenames.append(pc.filename)
                pc.go_next()
            return filenames

        def cut(cut_method, position=None):
            cut_method()
            if position is not None:
                b.select_custom(position)
                Clock.tick()
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            b.cut_marked()
            sleep(0.1)
            Clock.tick()
            Clock.tick()

        def test_page(expected):
            self.assertEqual(len(expected), len(b.grid.children))
            marked = [e.position for e in b.grid.children if e.is_marked()]
            self.assertEqual(0, len(marked))
            filenames = get_filenames(b.page_cursor, len(expected))
            self.assertCountEqual(expected, filenames)

        # test direct cut
        # # one
        cut(cut_one, 2)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(28) if i != 4])
        self.assertEqual("/0001.jpg", b.page_cursor.filename)

        cut(cut_one)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(28) if i != 4])
        self.assertEqual("/0001.jpg", b.page_cursor.filename)

        # # row
        cut(cut_row, 0)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(30) if i not in range(6, 9)])
        self.assertEqual("/0001.jpg", b.page_cursor.filename)

        cut(cut_row)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(30) if i not in range(6, 9)])
        self.assertEqual("/0001.jpg", b.page_cursor.filename)

        # # page
        cut(cut_page, 0)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(27, 27 * 2)])
        self.assertEqual("/0028.jpg", b.page_cursor.filename)

        # test load more
        # # one
        cut(cut_one, 35)
        self.assertNotEqual(0, b.page_cursor.pos)
        self.assertEqual(35, cursor.pos)
        for i in range(10):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0, b.page_cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(28) if i != 4])

        # # row
        cut(cut_row, 38)
        self.assertNotEqual(0, b.page_cursor.pos)
        for i in range(12):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0, b.page_cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(30) if i not in range(6, 9)])

        # # page
        cut(cut_page, 69)
        self.assertEqual(69, b.cursor.pos)
        self.assertNotEqual(0, b.page_cursor.pos)
        self.assertEqual(48, b.page_cursor.pos)
        for i in range(21):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0, b.page_cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(27, 27 * 2)])

        # test load set
        # # one
        cut(cut_one, 35)
        b.select_custom(position=0)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        test_page(["/%04d.jpg" % (i + 1,) for i in range(28) if i != 4])

        # # row
        cut(cut_row, 38)
        b.select_custom(position=0)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        test_page(["/%04d.jpg" % (i + 1,) for i in range(30) if i not in range(6, 9)])

        # # page
        cut(cut_page, 69)
        b.select_custom(position=0)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        test_page(["/%04d.jpg" % (i + 1,) for i in range(27, 27 * 2)])

        app.stop()

    def _test_cut_2(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        def get_filenames(c, qty):
            pc = c.clone()
            filenames = []
            for i in range(qty):
                filenames.append(pc.filename)
                pc.go_next()
            return filenames

        def test_page(expected):
            self.assertEqual(b.grid.children[-1].position, b.page_cursor.pos)
            self.assertEqual(b.grid.children[-1].file_id, b.page_cursor.file_id)

            self.assertEqual(len(expected),
                             len(b.grid.children) - (1 if isinstance(b.grid.children[0], EOLItem) else 0))
            marked = [e.position for e in b.grid.children if e.is_marked()]
            self.assertEqual(0, len(marked))
            filenames = get_filenames(b.page_cursor, len(expected))

            self.assertCountEqual(expected, filenames)

        def cut_first(qty):
            self.proceed_search(db)
            self.assertEqual('/0001.jpg', cursor.filename)
            for i in range(qty):
                b.mark_current()
                b.select_next(0)
            b.select_first()
            b.cut_marked()
            Clock.tick()

        def cut_last(qty):
            self.proceed_search(db)
            b.select_last()
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            self.assertEqual('/0100.jpg', cursor.filename)
            self.assertEqual(26, len(b.grid.children))
            for i in range(qty):
                b.mark_current()
                b.select_previous(0)
            b.select_last()
            b.cut_marked()
            sleep(0.1)
            Clock.tick()
            Clock.tick()

        def cut_eol(qty):
            self.proceed_search(db)
            b.select_last()
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            self.assertEqual('/0100.jpg', cursor.filename)
            self.assertEqual(26, len(b.grid.children))
            for i in range(qty):
                b.mark_current()
                b.select_previous(0)
            b.select_last()
            b.select_next(0)
            self.assertTrue(cursor.is_eol())
            b.cut_marked()
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            self.assertTrue(cursor.is_eol())

        cut_first(1)
        c1 = cursor.clone()
        c1.go_first()
        self.assertEqual(c1.file_id, b.page_cursor.file_id)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(1, 1 + 27)])

        cut_first(3)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(3, 3 + 27)])

        # test last
        cut_last(1)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(75, 99)])

        cut_last(3)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(72, 97)])

        # test eol
        cut_eol(1)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(75, 99)])

        cut_eol(3)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(72, 97)])

        # # test some navigation after cut
        self.assertEqual(97, cursor.pos)
        b.select_previous(0)
        Clock.tick()
        self.assertFalse(cursor.is_eol())
        self.assertEqual(96, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertFalse(cursor.is_eol())
        self.assertEqual(93, cursor.pos)
        b.select_up(0)
        Clock.tick()
        self.assertEqual(90, cursor.pos)
        b.select_down(0)
        Clock.tick()
        self.assertEqual(93, cursor.pos)
        b.select_down(0)
        Clock.tick()
        self.assertEqual(96, cursor.pos)
        b.select_down(0)
        Clock.tick()
        self.assertEqual(97, cursor.pos)
        b.select_up(0)
        Clock.tick()
        b.select_previous(0)
        Clock.tick()
        b.select_previous(0)
        Clock.tick()
        b.select_down(0)
        Clock.tick()
        b.select_next(0)
        Clock.tick()
        self.assertEqual(96, cursor.pos)

        # test multiple cut
        self.proceed_search(db)
        b.select_custom(3)
        b.mark_current(True)
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(1, cursor.get_clipboard_size())
        b.select_custom(5)
        b.mark_current(True)
        b.select_custom(2)
        b.mark_current(True)
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(2, cursor.get_clipboard_size())
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(2, cursor.get_clipboard_size())

        # test cut all
        self.proceed_search(db)
        cursor.mark_all(True)
        b.refresh_mark()
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(1, len(b.grid.children))
        self.assertEqual(100, cursor.get_clipboard_size())
        self.assertTrue(cursor.is_eol())
        self.assertEqual(0, cursor.pos)

        # test outside displacement
        self.proceed_search(db)
        b.mark_current()
        b.select_custom(70)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(70, cursor.pos)
        self.assertEqual(54, b.page_cursor.pos)
        self.assertEqual("/%04d.jpg" % (71,), cursor.filename)
        self.assertEqual("/%04d.jpg" % (55,), b.page_cursor.filename)
        self.assertEqual(cursor.file_id, b.grid.children[10].file_id)
        self.assertEqual(b.page_cursor.file_id, b.grid.children[-1].file_id)

        b.cut_marked()
        Clock.tick()
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(70, cursor.pos)
        self.assertEqual(54, b.page_cursor.pos)
        self.assertEqual("/%04d.jpg" % (72,), cursor.filename)
        self.assertEqual("/%04d.jpg" % (56,), b.page_cursor.filename)
        self.assertEqual(cursor.file_id, b.grid.children[10].file_id)
        self.assertEqual(b.page_cursor.file_id, b.grid.children[-1].file_id)

        self.proceed_search(db)
        b.mark_current()
        b.select_custom(70)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.mark_current()
        b.cut_marked()
        Clock.tick()
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(70, cursor.pos)
        self.assertEqual(54, b.page_cursor.pos)
        self.assertEqual("/%04d.jpg" % (73,), cursor.filename)
        self.assertEqual("/%04d.jpg" % (56,), b.page_cursor.filename)
        self.assertEqual(cursor.file_id, b.grid.children[10].file_id)
        self.assertEqual(b.page_cursor.file_id, b.grid.children[-1].file_id)

        app.stop()

    def _test_cut_3(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        def test_pos(qty, pos):
            self.proceed_search(db)
            for i in range(qty):
                b.select_custom(i)
                b.mark_current()
            sleep(0.1)
            Clock.tick()
            Clock.tick()

            b.select_custom(pos)
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            b.cut_marked()
            sleep(0.1)
            Clock.tick()
            Clock.tick()
            self.assertEqual(b.page_cursor.pos, b.grid.children[-1].position)
            self.assertEqual(pos, cursor.pos)

        test_pos(27, 28)

        test_pos(1, 1)
        test_pos(1, 2)
        test_pos(1, 15)
        test_pos(1, 27)
        test_pos(1, 65)
        test_pos(3, 3)
        test_pos(3, 4)
        test_pos(3, 15)
        test_pos(3, 27)
        test_pos(3, 65)
        test_pos(10, 27)
        test_pos(12, 65)
        test_pos(27, 65)
        test_pos(20, 64)

        app.stop()

    def _test_paste(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        def get_filenames(c, qty):
            pc = c.clone()
            filenames = []
            for i in range(qty):
                filenames.append(pc.filename)
                pc.go_next()
            return filenames

        def test_page(expected, debug=False):
            self.assertEqual(b.grid.children[-1].position, b.page_cursor.pos)
            self.assertEqual(b.grid.children[-1].file_id, b.page_cursor.file_id)

            self.assertEqual(len(expected),
                             len(b.grid.children) - (1 if isinstance(b.grid.children[0], EOLItem) else 0))
            marked = [e.position for e in b.grid.children if e.is_marked()]
            self.assertEqual(0, len(marked))
            filenames = get_filenames(b.page_cursor, len(expected))

            self.assertCountEqual(expected, filenames)

        def mark_one(init=True):
            if init:
                self.proceed_search(db)
            b.select_custom(4)
            b.mark_current()
            Clock.tick()

        def mark_row():
            self.proceed_search(db)
            for i in range(6, 9):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        def mark_page():
            self.proceed_search(db)
            for i in range(27):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        # test same cut and paste
        mark_one()
        b.cut_marked()
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(4, cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(27)])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children if not isinstance(i, EOLItem)])

        mark_row()
        self.assertEqual(8, cursor.pos)
        b.cut_marked()
        self.assertEqual(8, cursor.pos)
        b.select_custom(6)
        self.assertEqual(6, cursor.pos)
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(6, cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in range(27)])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children if not isinstance(i, EOLItem)])

        mark_page()
        self.assertEqual(26, cursor.pos)
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(26, cursor.pos)
        self.assertEqual(12, b.page_cursor.pos)
        b.select_first()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, b.page_cursor.pos)

        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(0, cursor.pos)
        self.assertEqual(0, b.page_cursor.pos)

        test_page(["/%04d.jpg" % (i + 1,) for i in range(27)])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children if not isinstance(i, EOLItem)])

        # test different cut and paste
        mark_one()
        b.select_custom(6)
        b.cut_marked()
        b.select_custom(2)
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertEqual(2, cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in [0, 1, 3, 2] + list(range(4, 27))])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children])

        mark_row()
        b.cut_marked()
        b.select_custom(50)
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual("/%04d.jpg" % (39 + 1,), b.page_cursor.filename)
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(50, cursor.pos)
        self.assertEqual(36, b.page_cursor.pos)
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(b.page_cursor.file_id, b.grid.children[-1].file_id)
        self.assertEqual("/%04d.jpg" % (39 + 1,), b.page_cursor.filename)
        test_page(["/%04d.jpg" % (i + 1,) for i in list(range(39, 53)) + list(range(6, 9)) + list(range(53, 63))])

        mark_page()
        b.cut_marked()
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(26, len(b.grid.children))
        self.assertEqual(72, cursor.pos)
        self.assertEqual(48, b.page_cursor.pos)
        self.assertEqual(b.page_cursor.file_id, b.grid.children[-1].file_id)
        self.assertEqual("/%04d.jpg" % (75 + 1,), b.page_cursor.filename)
        self.assertEqual("/%04d.jpg" % (99 + 1,), cursor.filename)
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(27, len(b.grid.children))
        self.assertEqual(57, b.page_cursor.pos)
        self.assertEqual(72, cursor.pos)
        self.assertEqual("/%04d.jpg" % (84 + 1,), b.page_cursor.filename)
        self.assertEqual("/%04d.jpg" % (0 + 1,), b.cursor.filename)

        # test multiple cut
        mark_one()
        b.cut_marked()
        mark_one(init=False)
        b.cut_marked()
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(4, cursor.pos)
        test_page(["/%04d.jpg" % (i + 1,) for i in list(range(4)) + list(range(5, 28))])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children if not isinstance(i, EOLItem)])

        # test cut and paste all
        self.proceed_search(db)
        cursor.mark_all(True)
        b.refresh_mark()
        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        self.assertEqual(0, cursor.pos)

        test_page(["/%04d.jpg" % (i + 1,) for i in range(27)])
        self.assertCountEqual(range(27), [i.position for i in b.grid.children])

        app.stop()

    def _test_eol_yank(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor = b.cursor

        def get_filenames(c, qty):
            pc = c.clone()
            filenames = []
            for i in range(qty):
                filenames.append(pc.filename)
                pc.go_next()
            return filenames

        def test_page(expected, debug=False):
            self.assertEqual(b.grid.children[-1].position, b.page_cursor.pos)
            self.assertEqual(b.grid.children[-1].file_id, b.page_cursor.file_id)

            self.assertEqual(len(expected),
                             len(b.grid.children) - (1 if isinstance(b.grid.children[0], EOLItem) else 0))
            marked = [e.position for e in b.grid.children if e.is_marked()]
            self.assertEqual(0, len(marked))
            filenames = get_filenames(b.page_cursor, len(expected))

            self.assertCountEqual(expected, filenames)

        def mark_one(init=True):
            if init:
                self.proceed_search(db)
            b.select_custom(4)
            b.mark_current()
            Clock.tick()

        def mark_row():
            self.proceed_search(db)
            for i in range(6, 9):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        def mark_page():
            self.proceed_search(db)
            for i in range(27):
                b.select_custom(i)
                b.mark_current()
            Clock.tick()

        # test cut
        self.proceed_search(db)
        for i in range(6, 9):
            b.select_custom(i)
            b.mark_current()
        Clock.tick()
        b.select_last()
        sleep(0.1)
        Clock.tick()
        Clock.tick()
        b.select_next(0)
        self.assertTrue(cursor.is_eol())

        b.cut_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertTrue(cursor.is_eol())
        test_page(["/%04d.jpg" % (i + 1,) for i in range(75, 100)])
        self.assertEqual(26, len(b.grid.children))
        self.assertCountEqual(range(72, 97), [c.position for c in b.grid.children if not isinstance(c, EOLItem)])

        # test paste
        b.paste_marked()
        sleep(0.1)
        Clock.tick()
        Clock.tick()

        self.assertTrue(96, cursor.pos)
        self.assertFalse(cursor.is_eol())
        test_page(["/%04d.jpg" % (i + 1,) for i in list(range(78, 100)) + list(range(6, 9))])
        self.assertEqual(26, len(b.grid.children))
        self.assertCountEqual(range(75, 100), [c.position for c in b.grid.children if not isinstance(c, EOLItem)])

        app.stop()

    def _test_calculate_to_remove(self, app, *args):
        b, db = self.prepare_browser(app)

        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=0, page_size=27, actual_size=27))
        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=13, page_size=27, actual_size=27))
        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=26, page_size=27, actual_size=27))

        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=0, page_size=27, actual_size=30))
        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=5, page_size=27, actual_size=30))
        self.assertEqual(0, b._calculate_lines_to_remove(local_pos=13, page_size=27, actual_size=36))
        self.assertEqual(9, b._calculate_lines_to_remove(local_pos=26, page_size=27, actual_size=36))

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_01_initialization(self):
        self.call_test(self._test_initialization)

    def test_02_load_set(self):
        self.call_test(self._test_load_set)

    def test_03_basic_moves(self):
        self.call_test(self._test_basic_moves)

    def test_04_load_more(self):
        self.call_test(self._test_load_more)

    def test_05_go(self):
        self.call_test(self._test_go)

    def test_06_first_last(self):
        self.call_test(self._test_first_last)

    def test_07_eol(self):
        self.call_test(self._test_eol_basic)

    def test_08_mark(self):
        self.call_test(self._test_mark)

    def test_17_cut_1(self):
        self.call_test(self._test_cut_1)

    def test_17_cut_2(self):
        self.call_test(self._test_cut_2)

    def test_17_cut_3(self):
        self.call_test(self._test_cut_3)

    def test_18_paste(self):
        self.call_test(self._test_paste)

    def test_19_eol_yank(self):
        self.call_test(self._test_eol_yank)

    def test_20_calc_to_remove(self):
        self.call_test(self._test_calculate_to_remove)


if __name__ == "__main__":
    unittest.main()
