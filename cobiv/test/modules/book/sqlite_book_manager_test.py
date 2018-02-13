import logging

from cobiv.modules.core.book.sqlite.sqlite_book_manager import SqliteBookManager
from cobiv.modules.core.session.session import Session
from cobiv.modules.database.datasources.datasource import Datasource
from cobiv.modules.database.sqlitedb.search.searchmanager import SearchManager
from cobiv.modules.database.sqlitedb.sqlitedb import SqliteCursor
from cobiv.modules.database.sqlitedb.sqlitesetmanager import SqliteSetManager
from cobiv.modules.core.session.cursor import Cursor, CursorInterface

logging.basicConfig(level=logging.DEBUG)

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

        fd = open('resources/sql/sqlite_db.sql')
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

        data = [(repo_key, 'file{}.png'.format(i), 1, 'file') for i in range(10000)]
        c.executemany('insert into file (repo_key,name,searchable,file_type) values (?,?,?,?)', data)

        return conn


ds = TestDatasource()


class TestApp(App):
    configuration = {
        'thumbnails.path': ''
    }

    def build(self):
        self.session = Session()
        self.datasource = ds
        self.set_manager = SqliteSetManager()
        return TestMainWidget()

    def get_config_value(self, key, default=""):
        if key in self.configuration:
            return self.configuration[key]
        else:
            return default

    def lookup(self, name, category):
        if name == "session":
            return self.session
        elif name == "sqlite_ds":
            return self.datasource
        elif name == "sqliteSetManager":
            return self.set_manager
        else:
            return None

    def fire_event(self, *args, **kwargs):
        pass


class SQLiteCursorTest(unittest.TestCase):

    def setUp(self):
        self.search_manager = SearchManager()
        self.conn = ds.get_connection()
        self.clear_data()

    def clear_data(self):
        with self.conn:
            self.conn.execute('delete from set_head').execute('delete from set_detail')
            self.conn.execute('delete from file_map').execute('delete from file where file_type="book"')

    def _create_set_mgr(self):
        self.search_manager.ready()
        mgr = SqliteBookManager()
        mgr.ready()
        mgr.set_manager.ready()
        mgr.set_manager.regenerate_default()
        return mgr

    def _test_initialization(self, app, *args):
        self._create_set_mgr()
        app.stop()

    def _test_add_book(self, app, *args):
        mgr = self._create_set_mgr()
        set_mgr = mgr.set_manager

        with self.conn:
            set_mgr.query_to_current_set("select id from file where rowid=2")
            book1_id=mgr.create_book("book1")
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(book1_id,self.conn.execute('select id from file where name=?',('book1',)).fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file where name=?', ('book1',)).fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from set_detail,file where set_detail.file_key=file.id and file.name=?',
                ('book1',)).fetchone()[0])

            set_mgr.query_to_current_set("select id from file where rowid between 7 and 8")
            book7_id=mgr.create_book("book7")

            self.assertEqual(3, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file where name=?', ('book7',)).fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from set_detail,file where set_detail.file_key=file.id and file.name=?',
                ('book7',)).fetchone()[0])
            self.assertEqual(book7_id,self.conn.execute('select id from file where name=?',('book7',)).fetchone()[0])
            self.assertNotEqual(book1_id,book7_id)

        app.stop()

    def _test_remove_book(self, app, *args):
        mgr = self._create_set_mgr()
        set_mgr = mgr.set_manager

        with self.conn:
            set_mgr.query_to_current_set("select id from file where rowid=2")
            book1_id = mgr.create_book("book1")
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file where name=?', ('book1',)).fetchone()[0])

            mgr.delete_book(book1_id)
            self.assertEqual(0, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(0, self.conn.execute(
                'select count(*) from file where name=?', ('book1',)).fetchone()[0])

            set_mgr.query_to_current_set("select id from file where rowid=2")
            book1_id = mgr.create_book("book1")
            set_mgr.query_to_current_set("select id from file where rowid between 7 and 8")
            book7_id = mgr.create_book("book7")

            mgr.delete_book(book1_id)
            mgr.delete_book(book1_id)
            self.assertEqual(2, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(0, self.conn.execute(
                'select count(*) from file where name=?', ('book1',)).fetchone()[0])
            self.assertEqual(1, self.conn.execute(
                'select count(*) from file where name=?', ('book7',)).fetchone()[0])

            mgr.delete_book(book7_id)
            self.assertEqual(0, self.conn.execute(
                'select count(*) from file_map').fetchone()[0])
            self.assertEqual(0, self.conn.execute(
                'select count(*) from file where name=?', ('book7',)).fetchone()[0])

        app.stop()

    def _test_open_book(self, app, *args):
        mgr = self._create_set_mgr()
        set_mgr = mgr.set_manager

        with self.conn:
            set_mgr.query_to_current_set("select id from file where rowid between 20 and 70")
            book1_id = mgr.create_book("book1")
            set_mgr.query_to_current_set("select id from file where rowid between 100 and 300")
            book2_id = mgr.create_book("book2")

            set_mgr.query_to_current_set("select id from file where rowid = 1 ")
            mgr.open_book(book1_id)
            self.assertEqual(51, self.conn.execute('select count(*) from current_set').fetchone()[0])
            mgr.open_book(book2_id)
            self.assertEqual(201, self.conn.execute('select count(*) from current_set').fetchone()[0])
            mgr.open_book(book1_id)
            self.assertEqual(51, self.conn.execute('select count(*) from current_set').fetchone()[0])

        app.stop()

    def _test_read_tags(self, app, *args):
        c=Cursor()

        mgr = self._create_set_mgr()
        set_mgr = mgr.set_manager

        with self.conn:
            set_mgr.query_to_current_set("select id from file order by id")
            self.assertEqual(1, self.conn.execute('select file_key from current_set where position=0').fetchone()[0])

            self.assertNotEqual(0,self.conn.execute('select count(*) from current_set').fetchone()[0])
            row=self.conn.execute('select rowid, * from current_set where position=1').fetchone()
            c.set_implementation(SqliteCursor(row=row, backend=self.conn, search_manager=self.search_manager))
            self.assertEqual('file',c.get_tag(0,'file_type',0))


            set_mgr.query_to_current_set("select id from file where rowid between 20 and 70")
            book1_id = mgr.create_book("book1")
            self.assertEqual(10001, book1_id)
            self.assertEqual(10001, self.conn.execute('select count(*) from file').fetchone()[0])
            self.assertEqual("book1", self.conn.execute('select name from file where id=10001').fetchone()[0])

            set_mgr.query_to_current_set("select id from file order by id")
            self.assertEqual(10001, self.conn.execute('select count(*) from current_set').fetchone()[0])
            self.assertEqual(10000, self.conn.execute('select position from current_set where file_key=10001').fetchone()[0])

            c.go_last()
            self.assertEqual(book1_id,c.file_id)
            self.assertEqual("book1",c.filename)
            self.assertEqual('book',c.get_tag(0,'file_type',0))

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_add_book(self):
        self.call_test(self._test_add_book)

    def test_remove_book(self):
        self.call_test(self._test_remove_book)

    def test_open_book(self):
        self.call_test(self._test_open_book)

    def test_read_tags(self):
        self.assertTrue(issubclass(SqliteCursor,CursorInterface))
        self.call_test(self._test_read_tags)


if __name__ == "__main__":
    unittest.main()
