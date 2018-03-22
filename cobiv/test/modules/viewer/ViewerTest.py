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
from cobiv.modules.core.session.session import Session
from cobiv.modules.database.sqlitedb.sqlitedb import SqliteDb
from cobiv.modules.views.browser.browser import Browser
from cobiv.modules.views.browser.eolitem import EOLItem
from cobiv.modules.hud_components.sidebar.sidebar import Sidebar
from cobiv.modules.database.datasources.sqlite.sqliteds import Sqliteds
from cobiv.modules.database.sqlitedb.sqlitesetmanager import SqliteSetManager
from cobiv.modules.views.viewer.viewer import Viewer
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

    def prepare_viewer(self, app):
        app.session = Session()

        db = SqliteDb()
        db.init_test_db(app.session)

        b = Viewer()

        b.ready()

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
        b, db = self.prepare_viewer(app)

        app.stop()


    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_01_initialization(self):
        self.call_test(self._test_initialization)


if __name__ == "__main__":
    unittest.main()
