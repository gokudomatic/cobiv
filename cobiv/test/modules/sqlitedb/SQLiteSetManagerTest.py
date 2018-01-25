import logging

from modules.core.session.session import Session
from modules.database.datasources.datasource import Datasource
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
        c = conn.execute('PRAGMA temp_store = MEMORY')
        c.execute('PRAGMA locking_mode = EXCLUSIVE')

        fd = open('../../../resources/sql/sqlite_db.sql')
        c.executescript(fd.read())
        fd.close()

        c.execute("insert into catalog (name) values(?) ", ("default",))
        c.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)',
                  ('default', 'memory', 0))

        c.execute('create temporary table marked (file_key int)')
        c.execute('create temporary table current_set as select * from set_detail where 1=2')

        # fill values
        c.execute('insert into catalog (name) values (?)', ('test',))
        c.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)', (c.lastrowid, '/', True))

        repo_key = c.lastrowid

        data = [(repo_key, 'file{}.png'.format(i)) for i in range(10000)]
        c.executemany('insert into file (repo_key,name) values (?,?)', data)

        return conn


ds = TestDatasource()


class TestApp(App):
    configuration = {
        'thumbnails.path': ''
    }

    def build(self):
        self.session=Session()
        self.datasource = ds
        return TestMainWidget()

    def get_config_value(self, key, default=""):
        if key in self.configuration:
            return self.configuration[key]
        else:
            return default

    def lookup(self, name, category):
        if name=="session":
            return self.session
        else:
            return self.datasource

    def fire_event(self,*args,**kwargs):
        pass

class SQLiteCursorTest(unittest.TestCase):

    def setUp(self):
        self.search_manager = SearchManager(None)
        self.conn = ds.get_connection()
        self.clear_data()

    def clear_data(self):
        with self.conn:
            self.conn.execute('delete from set_head').execute('delete from set_detail')

    def _create_set_mgr(self):
        mgr = SqliteSetManager()
        mgr.ready()
        mgr.regenerate_default()
        return mgr

    def _test_initialization(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            self.assertNotEqual(0, c.execute('select count(*) from set_head').fetchone()[0])
            self.assertNotEqual(0, c.execute('select count(*) from set_detail').fetchone()[0])

            self.assertEqual(0,c.execute('select position from set_detail order by position').fetchone()[0])

        app.stop()

    def _test_query_to_current_set(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            mgr.query_to_current_set("select id from file")
            c = self.conn.cursor()
            self.assertNotEqual(0, c.execute('select count(*) from current_set').fetchone()[0])
            mgr.query_to_current_set("select id from file where rowid between 100 and 500")
            self.assertEqual(401, c.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_save(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            mgr.query_to_current_set("select id from file")
            mgr.save('test1')

            c = self.conn.cursor()
            self.assertEqual(2, c.execute(
                'select count(*) from set_head').fetchone()[0])
            count1 = \
                c.execute(
                    'select count(*) from set_detail d inner join set_head h on d.set_head_key=h.id where h.name=?',
                    ('test1',)).fetchone()[0]
            self.assertNotEqual(0, count1)
            mgr.query_to_current_set("select id from file where rowid between 100 and 500")
            self.assertEqual(2, c.execute(
                'select count(*) from set_head').fetchone()[0])

            mgr.save('test2')
            self.assertEqual(3, c.execute(
                'select count(*) from set_head').fetchone()[0])
            self.assertEqual(401, c.execute(
                'select count(*) from set_detail d inner join set_head h on d.set_head_key=h.id where h.name=?',
                ('test2',)).fetchone()[0])

            self.assertEqual(count1, c.execute(
                'select count(*) from set_detail d inner join set_head h on d.set_head_key=h.id where h.name=?',
                ('test1',)).fetchone()[0])

            mgr.query_to_current_set("select id from file where rowid between 7 and 8")
            mgr.save('test1')
            self.assertEqual(3, c.execute(
                'select count(*) from set_head').fetchone()[0])
            self.assertEqual(2, c.execute(
                'select count(*) from set_detail d inner join set_head h on d.set_head_key=h.id where h.name=?',
                ('test1',)).fetchone()[0])

        app.stop()

    def _test_load(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            mgr.save('test1')
            mgr.query_to_current_set("select id from file where rowid between 700 and 800")
            mgr.save('test2')
            mgr.query_to_current_set("select id from file")

            mgr.load('test1')
            self.assertEqual(201, c.execute('select count(*) from current_set').fetchone()[0])

            mgr.load('test2')
            self.assertEqual(101, c.execute('select count(*) from current_set').fetchone()[0])

            mgr.query_to_current_set("select id from file where rowid between 14 and 15")
            mgr.save('test1')
            mgr.load('test2')
            mgr.load('test1')
            self.assertEqual(2, c.execute('select count(*) from current_set').fetchone()[0])

            mgr.load('a')
            self.assertEqual(0, c.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_rename(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            mgr.save('test1')
            mgr.query_to_current_set("select id from file where rowid between 444 and 555")
            mgr.save('test2')
            mgr.query_to_current_set("select id from file")

            mgr.rename('test1', 'aaa')

            mgr.load('aaa')
            self.assertEqual(201, c.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_remove(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            mgr.save('test1')
            mgr.query_to_current_set("select id from file where rowid between 444 and 555")
            mgr.save('test2')
            mgr.query_to_current_set("select id from file")

            mgr.remove('test1')

            mgr.load('test1')
            self.assertEqual(0, c.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_add_to_current(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:

            mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            mgr.save('test1')
            mgr.query_to_current_set("select id from file where rowid between 444 and 555")
            mgr.save('test2')
            mgr.query_to_current_set("select id from file")

            mgr.query_to_current_set("select id from file where rowid between 50 and 55")
            self.assertEqual(6, self.conn.execute('select count(*) from current_set').fetchone()[0])
            mgr.add_to_current('test1')
            self.assertEqual(207, self.conn.execute('select count(*) from current_set').fetchone()[0])
            self.assertEqual(206, self.conn.execute('select position from current_set order by position desc').fetchone()[0])

            mgr.query_to_current_set("select id from file where rowid between 50 and 149")
            self.assertEqual(100, self.conn.execute('select count(*) from current_set').fetchone()[0])
            mgr.add_to_current('test1')
            self.assertEqual(251, self.conn.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_remove_from_current(self, app, *args):
        mgr = self._create_set_mgr()


        mgr.query_to_current_set("select id from file where rowid between 100 and 300")
        mgr.save('test1')
        mgr.query_to_current_set("select id from file where rowid between 444 and 555")
        mgr.save('test2')

        mgr.query_to_current_set("select id from file where rowid between 250 and 350")
        mgr.remove_from_current('test1')
        self.assertEqual(50, self.conn.execute('select count(*) from current_set').fetchone()[0])
        self.assertEqual(49, self.conn.execute('select position from current_set order by position desc').fetchone()[0])


        mgr.query_to_current_set("select id from file where rowid between 50 and 55")
        self.assertEqual(6, self.conn.execute('select count(*) from current_set').fetchone()[0])
        mgr.remove_from_current('test1')
        self.assertEqual(6, self.conn.execute('select count(*) from current_set').fetchone()[0])

        mgr.query_to_current_set("select id from file where rowid between 50 and 149")
        self.assertEqual(100, self.conn.execute('select count(*) from current_set').fetchone()[0])
        self.assertEqual(99, self.conn.execute('select position from current_set order by position desc').fetchone()[0])
        mgr.remove_from_current('test1')
        self.assertEqual(50, self.conn.execute('select count(*) from current_set').fetchone()[0])
        self.assertEqual(49, self.conn.execute('select position from current_set order by position desc').fetchone()[0])

        app.stop()

    def _test_get_list(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            mgr.save('testa')
            mgr.query_to_current_set("select id from file where rowid between 444 and 555")
            mgr.save('test2')

            self.assertCountEqual(['testa','test2'], mgr.get_list())

        app.stop()

    def _test_add_to_set(self, app, *args):
        mgr = self._create_set_mgr()

        with self.conn:
            c = self.conn.cursor()

            mgr.query_to_current_set("select id from file where rowid <= 300")
            mgr.save('testa')

            mgr.add_to_set('testa',444)

            self.assertEqual(301, self.conn.execute('select count(*) from set_detail,set_head where set_head_key=set_head.id and set_head.name="testa"').fetchone()[0])


        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_query_to_current_set(self):
        self.call_test(self._test_query_to_current_set)

    def test_save(self):
        self.call_test(self._test_save)

    def test_load(self):
        self.call_test(self._test_load)

    def test_rename(self):
        self.call_test(self._test_rename)

    def test_remove(self):
        self.call_test(self._test_remove)

    def test_add_to_current(self):
        self.call_test(self._test_add_to_current)

    def test_remove_from_current(self):
        self.call_test(self._test_remove_from_current)

    def test_get_list(self):
        self.call_test(self._test_get_list)

    def test_add_to_set(self):
        self.call_test(self._test_add_to_set)


if __name__ == "__main__":
    unittest.main()
