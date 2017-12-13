import logging

from modules.database.datasources.datasource import Datasource
from modules.database.datasources.sqlite.sqliteds import Sqliteds
from modules.database.sqlitedb.sqlitesetmanager import SqliteSetManager

logging.basicConfig(level=logging.DEBUG)

from cobiv.modules.database.sqlitedb.search.searchmanager import SearchManager

import sqlite3
import unittest
from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget



class TestMainWidget(Widget):
    def execute_cmd(self, *args):
        pass

class TestDatasource(Datasource):

    def create_connection(self):
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA temp_store = MEMORY')
        conn.execute('PRAGMA locking_mode = EXCLUSIVE')
        return conn

ds=TestDatasource()

class TestApp(App):
    configuration = {
        'thumbnails.path': ''
    }

    def build(self):
        self.datasource = ds
        return TestMainWidget()

    def get_config_value(self, key, default=""):
        if key in self.configuration:
            return self.configuration[key]
        else:
            return default

    def lookup(self,name,category):
        return self.datasource

class SQLiteCursorTest(unittest.TestCase):
    def setUp(self):
        self.search_manager = SearchManager(None)

        self.conn=ds.get_connection()

        with self.conn:
            self.conn.execute('create table catalog (id INTEGER PRIMARY KEY, name text)')
            self.conn.execute(
                'create table repository (id INTEGER PRIMARY KEY, catalog_key int, path text, recursive num)')
            self.conn.execute(
                'create table file (id INTEGER PRIMARY KEY, repo_key int, name text)')
            self.conn.execute(
                'create table core_tags (file_key int, path text, size int, file_date datetime, ext text)')
            self.conn.execute('create table tag (file_key int, category int, kind text, type int, value)')
            self.conn.execute('create table set_head (id INTEGER PRIMARY KEY,  name text, readonly num)')
            self.conn.execute('create table set_detail (set_head_key int, position int, file_key int)')
            self.conn.execute('create table thumbs (file_key int primary key, data blob)')

            # indexes
            self.conn.execute('create unique index file_idx on file(name)')
            self.conn.execute('create index tag_idx1 on tag(file_key)')
            self.conn.execute('create index tag_idx2 on tag(category,kind,value)')
            self.conn.execute('create index tag_idx3 on tag(value)')
            self.conn.execute('create unique index core_tags_idx1 on core_tags(file_key)')
            self.conn.execute('create unique index core_tags_idx2 on core_tags(path,size,file_date,ext)')
            self.conn.execute('create unique index set_detail_pos_idx on set_detail(set_head_key,position)')
            self.conn.execute('create unique index set_detail_file_idx on set_detail(set_head_key,file_key)')

            c = self.conn.execute("insert into catalog (name) values(?) ", ("default",))
            c = self.conn.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)',
                                  ('default', 'memory', 0))

            self.conn.execute('create temporary table marked (file_key int)')
            self.conn.execute('create temporary table current_set as select * from set_detail where 1=2')

            # fill values
            c.execute('insert into catalog (name) values (?)', ('test',))
            c.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)', (c.lastrowid, '/', True))

            repo_key = c.lastrowid

            for i in range(100):
                c.execute('insert into file (repo_key,name) values (?,?)', (repo_key, 'file{}.png'.format(i)))

    def tearDown(self):
        self.conn.close()

    def clear_data(self):
        with self.conn:
            self.conn.execute('delete from set_head').execute('delete from set_detail')



    def _test_initialization(self, app, *args):
        mgr=SqliteSetManager()

        mgr.regenerate_default()

        with self.conn:
            c=self.conn.cursor()

            self.assertNotEquals(0,c.execute('select count(*) from set_head').fetchone()[0])
            self.assertNotEquals(0,c.execute('select count(*) from set_detail').fetchone()[0])

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
