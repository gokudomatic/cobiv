import os
import unittest
from functools import partial
from time import sleep

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.browser.browser import Browser
from cobiv.modules.session.Session import Session


class TestMainWidget(Widget):
    def execute_cmd(self, *args):
        pass


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
        return TestMainWidget()

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


class CursorTest(unittest.TestCase):
    def setUp(self):
        Clock._events = [[] for i in range(256)]

    def _test_initialization(self, app, *args):
        app.session = Session()

        b = Browser()

        app.root.add_widget(b)
        b.ready()
        b.on_switch(loader_thread=False)

        sleep(0.11)
        Clock.tick()

        self.assertEqual(len(b.grid.children), 1)

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)


if __name__ == "__main__":
    unittest.main()
