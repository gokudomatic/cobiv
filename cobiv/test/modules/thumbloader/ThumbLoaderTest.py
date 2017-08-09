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

from cobiv.modules.thumbloader.thumbloader import ThumbLoader


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
            'thumbloader.path': self.get_user_path('thumbs'),
            'thumbloader.image_size': 120
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


class ThumbloaderTest(unittest.TestCase):
    def get_user_path(self, *args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    def setUp(self):
        self.session = Session()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def get_thumbloader(self):
        t = ThumbLoader()
        t.ready()
        t.restart()
        return t

    def _test_initialization(self, app, *args):
        t=self.get_thumbloader()

        t.stop()
        app.stop()

    def _test_enqueue_images(self, app, *args):
        t=self.get_thumbloader()

        t.append((1,self.get_user_path('images', '0001.jpg')))

        print "2"
        path=self.get_user_path('thumbs')
        [os.remove(os.path.join(path,f)) for f in os.listdir(path)]

        t.stop()
        app.stop()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_enqueue_images(self):
        self.call_test(self._test_enqueue_images)


if __name__ == "__main__":
    unittest.main()
