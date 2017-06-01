import os
import unittest
from functools import partial
import shutil

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.session.Session import Session
from cobiv.modules.session.cursor import CursorInterface
from cobiv.modules.sqlitedb.sqlitedb import SqliteCursor, SqliteDb

import sqlite3


class TestMainWidget(Widget):
    def execute_cmd(self, *args, **kwargs):
        pass

    def show_progressbar(self, *args, **kwargs):
        pass

    def set_progressbar_value(self, *args, **kwargs):
        pass

    def close_progressbar(self, *args, **kwargs):
        pass


class TestApp(App):


    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.configuration = {
            'thumbnails.path': '',
            'repository': 'images',
            'thumbnails.path': self.get_user_path('thumbs')
        }

    def build(self):
        return TestMainWidget()

    def get_config_value(self, key, defaultValue=""):
        if self.configuration.has_key(key):
            return self.configuration[key]
        else:
            return defaultValue

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


class SQLiteCursorTest(unittest.TestCase):

    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


    def setUp(self):
        self.session=Session()

        f_path=self.get_user_path('images','test.jpg')
        if os.path.exists(f_path):
            os.remove(f_path)

    def init_db_with_tags(self):
        db = SqliteDb()
        db.init_test_db()
        db.session = self.session

        db.search_tag()
        c = self.session.cursor

        c.add_tag("one","o","e")
        c.go_next()
        c.add_tag("two","o","t")
        c.go_next()
        c.add_tag("three","t","r","e","3")

        return db

    def _test_initialization(self, app, *args):
        db = SqliteDb()
        db.init_test_db()

        db.close_db()

        app.stop()

    def _test_search_all(self, app, *args):
        db = SqliteDb()
        db.init_test_db()
        db.session=self.session

        db.search_tag()
        c = self.session.cursor

        self.assertEqual(3,len(c))
        self.assertEqual("images\\0001.jpg",c.filename)
        c.go_next()
        self.assertEqual("images\\0002.jpg",c.filename)
        c.go_next()
        self.assertEqual("images\\0003.jpg",c.filename)

        db.close_db()
        app.stop()

    def _test_search_tag(self, app, *args):
        db=self.init_db_with_tags()
        c = self.session.cursor

        db.search_tag("one")
        self.assertEqual(1, len(c))

        db.search_tag("o")
        self.assertEqual(2, len(c))

        db.search_tag("o","-one")
        self.assertEqual(1, len(c))
        self.assertEqual("images\\0002.jpg",c.filename)


        db.close_db()
        app.stop()

    def _test_update_file(self, app, *args):
        db=self.init_db_with_tags()
        c = self.session.cursor

        new_filename=self.get_user_path('images','test.jpg')

        shutil.copy(self.get_user_path('images','0003.jpg'),new_filename)
        self.assertTrue(os.path.exists(new_filename))
        db.updatedb(sameThread=True)
        db.search_tag()
        self.assertEqual(4,len(c))

        os.remove(new_filename)
        db.updatedb(sameThread=True)
        db.search_tag()
        self.assertEqual(3,len(c))


        db.close_db()
        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_search_all(self):
        self.call_test(self._test_search_all)

    def test_search_tag(self):
        self.call_test(self._test_search_tag)

    def test_update_file(self):
        self.call_test(self._test_update_file)

if __name__ == "__main__":
    unittest.main()
