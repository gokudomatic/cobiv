import unittest
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.sqlitedb.sqlitedb import SqliteCursor

import sqlite3


class TestMainWidget(Widget):
    def execute_cmd(self, *args):
        pass


class TestApp(App):
    configuration = {
        'thumbnails.path': ''
    }

    def build(self):
        return TestMainWidget()

    def get_config_value(self, key):
        if self.configuration.has_key(key):
            return self.configuration[key]
        else:
            return ""


class SQLiteCursorTest(unittest.TestCase):
    db = None

    def setUp(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA temp_store = MEMORY')
        self.conn.execute('PRAGMA locking_mode = EXCLUSIVE')

        with self.conn:
            self.conn.execute('create table catalog (id INTEGER PRIMARY KEY, name text)')
            self.conn.execute(
                'create table repository (id INTEGER PRIMARY KEY, catalog_key int, path text, recursive num)')
            self.conn.execute(
                'create table file (id INTEGER PRIMARY KEY, repo_key int, name text, filename text, path text, ext text)')
            self.conn.execute('create table tag (file_key int, kind text, value text)')
            self.conn.execute('create table set_head (id INTEGER PRIMARY KEY,  name text, readonly num)')
            self.conn.execute('create table set_detail (set_head_key int, position int, file_key int)')
            self.conn.execute('create table thumbs (file_key int primary key, data blob)')

            # indexes
            self.conn.execute('create unique index file_idx on file(name)')
            self.conn.execute('create unique index tag_idx on tag(file_key,kind,value)')
            self.conn.execute('create unique index set_detail_pos_idx on set_detail(set_head_key,position)')
            self.conn.execute('create unique index set_detail_file_idx on set_detail(set_head_key,file_key)')

            c = self.conn.execute("insert into catalog (name) values(?) ", ("default",))
            c = self.conn.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)',
                                  ('default', 'memory', 0))

            self.conn.execute('create temporary table marked (file_key int)')
            self.conn.execute('create temporary table current_set as select * from set_detail where 1=2')

    def tearDown(self):
        self.conn.close()

    def _test_initialization(self, app, *args):
        row = self.conn.execute('select rowid, * from current_set where position=0 limit 1').fetchone()
        c = SqliteCursor(row, self.conn)

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
