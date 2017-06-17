import os
import unittest
from functools import partial
from time import sleep

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout

from cobiv.modules.browser.browser import Browser
from cobiv.modules.session.Session import Session
from cobiv.modules.sqlitedb.sqlitedb import SqliteDb

from kivy.core.window import Window

Window.size = (360, 360)


class TestMainWidget(GridLayout):
    def execute_cmd(self, action, *args, **kwargs):
        if action == "load-set":
            self.browser.load_set()
        else:
            pass

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass

    def set_browser(self, instance):
        self.browser = instance
        self.add_widget(instance)


class TestApp(App):
    session = None

    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbnails.path': '',
            'repository': 'images',
            'thumbnails.path': self.get_user_path('thumbs')
        }

    def build(self):
        return TestMainWidget(size_hint=(1, 1), cols=1)

    def get_config_value(self, key, default=""):
        if self.configuration.has_key(key):
            return self.configuration[key]
        else:
            return default

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def lookup(self, object_name, category):
        if category == "Entity" and object_name == "session":
            return self.session
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
        db.init_test_db()
        db.session = app.session

        b = Browser()

        app.root.set_browser(b)
        b.ready()
        b.on_switch(loader_thread=False)

        sleep(0.1)
        Clock.tick()

        return b, db

    def proceed_search(self,db,query=None):
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
        self.assertItemsEqual((360, 360), Window.size)
        self.assertItemsEqual((1, 1), b.size_hint)
        self.assertItemsEqual((360, 360), b.size)

        app.stop()


    def _test_load_set(self, app, *args):
        b, db = self.prepare_browser(app)
        self.assertEqual(0, len(b.image_queue))

        db.search_tag()
        sleep(0.1)
        Clock.tick()
        self.assertEqual(27, len(b.image_queue))

        for i in range(27):
            self.assertEqual("images\\%04d.jpg" % (i + 1,), b.image_queue[i][3])
        Clock.tick()

        self.assertEqual(len(b.grid.children), 27)

        self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos,b.cursor.pos)

        app.stop()

    def _test_basic_moves(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)

        cursor=b.cursor
        for i in range(10):
            b.select_next(0)
            Clock.tick()
            self.assertEqual(i+1,cursor.pos)
            self.assertFalse(b.cursor.is_eol())
            self.assertNotEqual(b.page_cursor.pos,b.cursor.pos)
        for i in range(10):
            b.select_previous(0)
            Clock.tick()
            self.assertEqual(10-i-1,cursor.pos)
            self.assertFalse(b.cursor.is_eol())
        self.assertEqual(b.page_cursor.pos,b.cursor.pos)

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
        cursor=b.cursor

        for i in range(7):
            b.select_down(0)
            Clock.tick()

        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(21,cursor.pos)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(3,b.page_cursor.pos)
        self.assertEqual(24,cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        for i in range(25):
            b.select_down(0)
            Clock.tick()
        self.assertEqual(99,cursor.pos)
        self.assertEqual(74,b.page_cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        b.select_down(0)
        Clock.tick()
        self.assertEqual(100,cursor.pos)
        self.assertTrue(cursor.is_eol())
        self.assertEqual(len(b.grid.children), 27)
        self.assertEqual(74,b.page_cursor.pos)

        # moving up
        b.select_up(0)
        Clock.tick()
        self.assertEqual(74,b.page_cursor.pos)
        self.assertEqual(97,cursor.pos)
        self.assertFalse(cursor.is_eol())

        for i in range(32):
            b.select_up(0)
            Clock.tick()
        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(1,cursor.pos)

        b.select_up(0)
        Clock.tick()

        self.assertEqual(0,b.page_cursor.pos)
        self.assertEqual(0,cursor.pos)
        self.assertEqual(len(b.grid.children), 27)

        app.stop()


    def _test_go(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        app.stop()

    def _test_first_last(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        app.stop()

    def _test_mark(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        app.stop()

    def _test_cut(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

        app.stop()

    def _test_paste(self, app, *args):
        b, db = self.prepare_browser(app)
        self.proceed_search(db)
        cursor=b.cursor

        self.assertTrue(False)

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

    def test_07_mark(self):
        self.call_test(self._test_mark)

    def test_17_cut(self):
        self.call_test(self._test_cut)

    def test_18_paste(self):
        self.call_test(self._test_paste)

if __name__ == "__main__":
    unittest.main()
