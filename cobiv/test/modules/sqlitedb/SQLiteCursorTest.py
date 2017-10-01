import logging

logging.basicConfig(level=logging.DEBUG)

from cobiv.modules.database.sqlitedb.search.searchmanager import SearchManager

import sqlite3
import unittest
from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from cobiv.modules.database.sqlitedb.sqlitedb import SqliteCursor


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
    def setUp(self):
        # self.session = Session()
        self.search_manager = SearchManager(None)

        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA temp_store = MEMORY')
        self.conn.execute('PRAGMA locking_mode = EXCLUSIVE')

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

    def tearDown(self):
        self.conn.close()

    def regenerate_set(self, set_name, query):

        is_current = set_name == "_current"

        with self.conn:
            c = self.conn.cursor()

            if is_current:
                self.conn.execute('drop table if exists current_set') \
                    .execute(
                    'create temporary table current_set as select * from set_detail where 1=2')
                head_key = 0
            else:
                row = c.execute('select id from set_head where name=?', (set_name,)).fetchone()
                if row is not None:
                    head_key = row[0]
                    c.execute('delete from set_detail where set_head_key=?', (head_key,))
                else:
                    c.execute('insert into set_head (name, readonly) values (?,?)', (set_name, '0'))
                    head_key = c.lastrowid

            resultset = c.execute(query).fetchall()
            lines = []
            thread_count = 0
            for row in resultset:
                lines.append((head_key, thread_count, row['id']))
                thread_count += 1

            query = 'insert into %s (set_head_key, position, file_key) values (?,?,?)' % (
                'current_set' if is_current else 'set_detail')
            c.executemany(query, lines)

    def copy_set_to_current(self, set_name):
        with self.conn:
            self.conn.execute('drop table if exists current_set') \
                .execute(
                'create temporary table current_set as select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? order by cast(d.position as integer)',
                set_name)

    def search(self, *args):
        if len(args) == 0:
            self.copy_set_to_current('*')
        else:
            to_include = []
            to_exclude = []

            for arg in args:
                if arg[0] == "-":
                    to_exclude.append(arg[1:])
                else:
                    to_include.append(arg)

            query = 'select f.id,f.name from file f ,tag t where t.file_key=f.id '
            if len(to_include) > 0:
                query += 'and t.value in ("' + '", "'.join(to_include) + '") '
            if len(to_exclude) > 0:
                query += 'and t.value not in ("' + '", "'.join(to_exclude) + '") '

            query += ' order by CAST(f.name as INTEGER)'
            self.regenerate_set("default", query)

        row = self.conn.execute('select rowid, * from current_set where position=0 limit 1').fetchone()
        return SqliteCursor(row=row, backend=self.conn, search_manager=self.search_manager)

    def add_files(self, amount):
        """Generates N items for testing purpose

        :param amount: Number of items to generate
        :return: None
        """
        c = self.conn.cursor()

        # reset file table
        c.execute('delete from file')
        c.execute('delete from marked')
        c.execute('delete from tag')

        query_to_add = []
        for i in range(amount):
            query_to_add.append((0, 'f' + str(i) + '.png'))

        c.executemany('insert into file(repo_key, name) values(?,?)', query_to_add)

        self.regenerate_set('*', "select id from file order by cast(id as integer)")

    def _test_initialization(self, app, *args):
        c = self.search()
        self.assertIsNone(c.pos)
        self.assertEqual(0, len(c))
        self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        self.assertEqual(0, c.pos)
        self.assertEqual(1, len(c))
        self.assertEqual(1, c.file_id)

        self.add_files(10)
        c = self.search()
        self.assertEqual(0, c.pos)
        self.assertEqual(10, len(c))
        self.assertEqual(1, c.file_id)

        self.add_files(1000)
        c = self.search()
        self.assertEqual(0, c.pos)
        self.assertEqual(1000, len(c))
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_clone(self, app, *args):
        c = self.search()
        c1 = c.clone()
        self.assertIsNone(c1.pos)
        self.assertEqual(0, len(c1))
        self.assertIsNone(c1.file_id)
        c1.go_next()
        c1.go_next()
        c1.go_previous()
        self.assertIsNone(c1.pos)
        self.assertEqual(0, len(c1))
        self.assertIsNone(c1.file_id)

        self.add_files(1)
        c = self.search()
        c1 = c.clone()
        self.assertEqual(0, c1.pos)
        self.assertEqual(1, len(c1))
        self.assertEqual(1, c1.file_id)
        c1.go_next()
        self.assertEqual(0, c1.pos)
        self.assertEqual(1, c1.file_id)
        self.assertEquals(c.pos, c1.pos)
        self.assertEquals(c.file_id, c1.file_id)

        self.add_files(5)
        c = self.search()
        c1 = c.clone()
        self.assertEqual(0, c1.pos)
        self.assertEqual(5, len(c1))
        self.assertEqual(1, c1.file_id)
        c1.go_next()
        self.assertEqual(1, c1.pos)
        self.assertEqual(2, c1.file_id)
        self.assertNotEquals(c.pos, c1.pos)
        self.assertNotEquals(c.file_id, c1.file_id)

        app.stop()

    def _test_go_next(self, app, *args):
        c = self.search()
        for i in range(5):
            self.assertIsNone(c.go_next())
            self.assertIsNone(c.pos)
            self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        for i in range(5):
            self.assertIsNone(c.go_next())
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.add_files(5)
        c = self.search()
        self.assertEqual(c, c.go_next())
        self.assertEqual(1, c.pos)
        self.assertEqual(2, c.file_id)

        for i in range(3):
            self.assertEqual(c, c.go_next())
            self.assertEqual(i + 2, c.pos)
            self.assertEqual(i + 3, c.file_id)
        self.assertIsNone(c.go_next())
        self.assertEqual(4, c.pos)
        self.assertEqual(5, c.file_id)

        app.stop()

    def _test_go_previous(self, app, *args):
        c = self.search()
        for i in range(5):
            self.assertIsNone(c.go_previous())
            self.assertIsNone(c.pos)
            self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        for i in range(5):
            self.assertIsNone(c.go_previous())
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.add_files(5)
        c = self.search()
        for i in range(5):
            self.assertIsNone(c.go_previous())
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        c.go_next()
        c.go_next()
        self.assertEqual(c, c.go_previous())
        self.assertEqual(1, c.pos)
        self.assertEqual(2, c.file_id)
        for i in range(6):
            c.go_next()
        self.assertEqual(c, c.go_previous())
        self.assertEqual(3, c.pos)
        self.assertEqual(4, c.file_id)
        for i in range(6):
            c.go_previous()
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_go_first(self, app, *args):
        c = self.search()
        c.go_first()
        for i in range(5):
            self.assertIsNone(c.go_first())
            self.assertIsNone(c.pos)
            self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        for i in range(5):
            self.assertEqual(c, c.go_first())
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.add_files(10)
        c = self.search()
        c.go(5)
        self.assertEqual(c, c.go_first())
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_go_last(self, app, *args):
        c = self.search()
        c.go_first()
        for i in range(5):
            self.assertIsNone(c.go_last())
            self.assertIsNone(c.pos)
            self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        for i in range(5):
            self.assertEqual(c, c.go_last())
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.add_files(10)
        c = self.search()
        c.go(5)
        self.assertEqual(c, c.go_last())
        self.assertEqual(9, c.pos)
        self.assertEqual(10, c.file_id)

        app.stop()

    def _test_get(self, app, *args):
        c = self.search()
        self.assertIsNone(c.get(0))
        self.assertIsNone(c.get(10))
        self.assertIsNone(c.get(-10))

        self.add_files(1)
        c = self.search()
        self.assertTrue(isinstance(c.get(0), sqlite3.Row))
        self.assertIsNone(c.get(10))
        self.assertIsNone(c.get(-10))

        self.add_files(10)
        c = self.search()
        self.assertTrue(isinstance(c.get(0), sqlite3.Row))
        self.assertTrue(isinstance(c.get(5), sqlite3.Row))
        self.assertIsNone(c.get(10))
        self.assertIsNone(c.get(-2))

        app.stop()

    def _test_get_next_ids(self, app, *args):
        c = self.search()
        self.assertItemsEqual([], c.get_next_ids(5))

        self.add_files(1)
        c = self.search()
        self.assertItemsEqual([], c.get_next_ids(5))
        rows = [(r['file_key'], r['position'], r['name']) for r in c.get_next_ids(5, self_included=True)]
        self.assertItemsEqual([(1, 0, 'f0.png')], rows)

        self.add_files(15)
        c = self.search()

        c.go(8)
        rows = [(r['file_key'], r['position'], r['name']) for r in c.get_next_ids(3)]
        self.assertItemsEqual([(10, 9, 'f9.png'), (11, 10, 'f10.png'), (12, 11, 'f11.png')], rows)
        rows = [(r['file_key'], r['position'], r['name']) for r in c.get_next_ids(3, self_included=True)]
        self.assertItemsEqual([(9, 8, 'f8.png'), (10, 9, 'f9.png'), (11, 10, 'f10.png')], rows)

        app.stop()

    def _test_get_previous_ids(self, app, *args):
        c = self.search()
        self.assertItemsEqual([], c.get_previous_ids(5))

        self.add_files(1)
        c = self.search()
        self.assertItemsEqual([], c.get_previous_ids(5))

        self.add_files(15)
        c = self.search()

        c.go(8)
        rows = [(r['file_key'], r['position'], r['name']) for r in c.get_previous_ids(3)]
        self.assertItemsEqual([(8, 7, 'f7.png'), (7, 6, 'f6.png'), (6, 5, 'f5.png')], rows)

        app.stop()

    def _test_go(self, app, *args):
        c = self.search()
        c.go_first()
        for i in range(5):
            self.assertIsNone(c.go(i))
            self.assertIsNone(c.pos)
            self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        self.assertEqual(c, c.go(0))
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        for i in range(5):
            self.assertIsNone(c.go(i + 1))
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        for i in range(5):
            self.assertIsNone(c.go(-i - 1))
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.add_files(10)
        c = self.search()
        for i in range(10, 0, -1):
            self.assertEqual(c, c.go(i - 1))
            self.assertEqual(i - 1, c.pos)
            self.assertEqual(i, c.file_id)

        for i in range(5):
            self.assertIsNone(c.go(-i - 1))
            self.assertEqual(0, c.pos)
            self.assertEqual(1, c.file_id)

        self.assertIsNone(c.go(10))
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_mark(self, app, *args):
        c = self.search()
        c.mark()
        self.assertFalse(c.get_mark())
        c.mark(True)
        self.assertFalse(c.get_mark())
        c.mark(False)
        self.assertFalse(c.get_mark())

        self.add_files(1)
        c = self.search()
        c.mark()
        self.assertTrue(c.get_mark())
        c.mark()
        self.assertFalse(c.get_mark())
        c.mark(True)
        self.assertTrue(c.get_mark())
        c.mark(False)
        self.assertFalse(c.get_mark())

        self.add_files(10)
        c = self.search()
        c.go(5)
        c.mark()
        self.assertTrue(c.get_mark())
        c.mark()
        self.assertFalse(c.get_mark())
        c.mark(True)
        self.assertTrue(c.get_mark())
        c.mark(False)
        self.assertFalse(c.get_mark())

        app.stop()

    def _test_get_marked_count(self, app, *args):
        c = self.search()
        self.assertEqual(0, c.get_marked_count())
        c.mark()
        self.assertEqual(0, c.get_marked_count())

        self.add_files(1)
        c = self.search()
        self.assertEqual(0, c.get_marked_count())
        c.mark()
        self.assertEqual(1, c.get_marked_count())

        self.add_files(10)
        c = self.search()
        c.go(5)
        self.assertEqual(0, c.get_marked_count())
        c.mark()
        c.go_next()
        c.mark()
        self.assertEqual(2, c.get_marked_count())

        app.stop()

    def _test_get_all_marked(self, app, *args):
        c = self.search()
        self.assertItemsEqual([], c.get_all_marked())
        c.mark()
        self.assertItemsEqual([], c.get_all_marked())

        self.add_files(1)
        c = self.search()
        self.assertItemsEqual([], c.get_all_marked())
        c.mark()
        self.assertItemsEqual([1], c.get_all_marked())

        self.add_files(10)
        c = self.search()
        c.go(5)
        c.mark()
        c.go_next()
        c.mark()
        self.assertItemsEqual([6, 7], c.get_all_marked())

        app.stop()

    def _test_remove(self, app, *args):
        c = self.search()
        self.assertEqual(0, len(c))
        c.remove()
        self.assertEqual(0, len(c))

        self.add_files(1)
        c = self.search()
        self.assertEqual(1, len(c))
        c.remove()
        self.assertEqual(0, len(c))
        c.remove()
        self.assertEqual(0, len(c))

        self.add_files(10)
        c = self.search()
        c.remove()
        c.go(c.pos)
        self.assertEqual(2, c.file_id)
        c.remove()
        c.go(c.pos)
        self.assertEqual(3, c.file_id)

        c.go(5)
        c.remove()
        c.go(5)
        self.assertEqual(9, c.file_id)
        c.go_last()
        c.remove()
        c.go_last()
        self.assertEqual(9, c.file_id)

        app.stop()

    def _test_len(self, app, *args):
        c = self.search()
        self.assertEqual(0, len(c))

        self.add_files(1)
        c = self.search()
        self.assertEqual(1, len(c))

        self.add_files(22)
        c = self.search()
        self.assertEqual(22, len(c))

        app.stop()

    def _test_get_cursor_by_pos(self, app, *args):
        c = self.search()
        c1 = c.get_cursor_by_pos(0)
        self.assertIsNone(c1.pos)
        self.assertEqual(0, len(c1))
        self.assertIsNone(c1.file_id)

        self.add_files(1)
        c = self.search()
        c1 = c.get_cursor_by_pos(0)
        self.assertEqual(0, c1.pos)
        self.assertEqual(1, len(c1))
        self.assertEqual(1, c1.file_id)
        c1 = c.get_cursor_by_pos(1)
        self.assertIsNone(c1.pos)
        self.assertIsNone(c1.file_id)

        self.add_files(5)
        c = self.search()
        c1 = c.get_cursor_by_pos(1)
        self.assertEqual(1, c1.pos)
        self.assertEqual(2, c1.file_id)
        self.assertNotEquals(c.pos, c1.pos)
        self.assertNotEquals(c.file_id, c1.file_id)

        app.stop()

    def _test_move_to(self, app, *args):
        c = self.search()
        c.move_to(3)
        self.assertIsNone(c.pos)
        self.assertEqual(0, len(c))
        self.assertIsNone(c.file_id)

        self.add_files(1)
        c = self.search()
        c.move_to(3)
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        self.add_files(5)
        c = self.search()
        c.move_to(2)
        self.assertEqual(2, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_previous()
        self.assertEqual(1, c.pos)
        self.assertEqual(3, c.file_id)
        c.go_previous()
        self.assertEqual(0, c.pos)
        self.assertEqual(2, c.file_id)
        c.go(2)
        self.assertEqual(2, c.pos)
        self.assertEqual(1, c.file_id)
        c.go_next()
        self.assertEqual(3, c.pos)
        self.assertEqual(4, c.file_id)

        self.add_files(5)
        c = self.search()
        c.go(4)
        c.move_to(-2)
        self.assertEqual(0, c.pos)
        self.assertEqual(5, c.file_id)
        c.go_next()
        self.assertEqual(1, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_get_position_mapping(self, app, *args):

        def get_map(id_list):
            return [(r[0], r[1]) for r in c.get_position_mapping(id_list)]

        c = self.search()
        self.assertItemsEqual([], get_map([]))
        self.assertItemsEqual([], get_map([1]))

        self.add_files(1)
        c = self.search()
        self.assertItemsEqual([], get_map([]))
        self.assertItemsEqual([], get_map([0]))
        self.assertItemsEqual([(1, 0)], get_map([1]))

        self.add_files(5)
        c = self.search()
        c.go_last()
        self.assertItemsEqual([], get_map([]))
        self.assertItemsEqual([], get_map([0]))
        self.assertItemsEqual([(1, 0), (3, 2), (5, 4)], get_map([1, 3, 5]))

        app.stop()

    def _test_cut_marked(self, app, *args):
        c = self.search()
        c.mark()
        c.cut_marked()
        self.assertEqual(0, len(c))

        self.add_files(1)
        c = self.search()
        c.mark()
        self.assertEqual(1, len(c))
        self.assertEqual(1, c.get_marked_count())
        c.cut_marked()
        self.assertEqual(0, len(c))
        self.assertEqual(0, c.get_marked_count())

        self.add_files(10)
        c = self.search()
        c.go(1)
        c.mark()
        c.go(8)
        c.mark()
        c.go_first()
        c.cut_marked()
        self.assertEqual(8, len(c))
        self.assertEqual(2, c.get_clipboard_size())
        c.mark()
        c.cut_marked()
        self.assertEqual(7, len(c))
        self.assertEqual(1, c.get_clipboard_size())

        app.stop()

    def _test_paste_marked(self, app, *args):

        # test empty
        c = self.search()
        c.mark()
        c.cut_marked()
        c.paste_marked(0)
        self.assertEqual(0, len(c))

        # test cut and past 1
        self.add_files(1)
        c = self.search()
        c.mark()
        self.assertEqual(1, len(c))
        self.assertEqual(1, c.get_marked_count())
        c.cut_marked()
        self.assertEqual(0, len(c))
        self.assertEqual(0, c.get_marked_count())
        c.paste_marked(0)
        self.assertEqual(1, len(c))
        self.assertEqual(0, c.pos)
        self.assertEqual(1, c.file_id)

        # test cut and past in the middle
        self.add_files(10)
        c = self.search()
        c.go(1)
        c.mark()
        c.go(8)
        c.mark()
        c.go_first()
        c.cut_marked()
        self.assertEqual(8, len(c))
        c.paste_marked(5)
        self.assertEqual(10, len(c))
        c.go(5)
        self.assertEqual(5, c.pos)
        self.assertEqual(2, c.file_id)
        c.go_next()
        self.assertEqual(6, c.pos)
        self.assertEqual(9, c.file_id)
        c.go_next()
        self.assertEqual(7, c.pos)
        self.assertEqual(7, c.file_id)
        c.go_next()
        self.assertEqual(8, c.pos)
        self.assertEqual(8, c.file_id)
        c.go_next()
        self.assertEqual(9, c.pos)
        self.assertEqual(10, c.file_id)

        # test past empty
        self.add_files(10)
        c = self.search()
        c.paste_marked(3)
        self.assertEqual(10, len(c))
        c.go(3)
        self.assertEqual(4, c.file_id)

        # test past pos=none
        c.mark()
        c.cut_marked()
        c.go(8)
        c.paste_marked()
        c.go(8)
        self.assertEqual(4, c.file_id)

        # test append
        self.add_files(3)
        c = self.search()
        c.mark()
        c.cut_marked()
        c.paste_marked(append=True)
        c.go_last()
        self.assertEqual(2, c.pos)
        self.assertEqual(1, c.file_id)

        app.stop()

    def _test_mark_all(self, app, *args):
        c = self.search()
        c.mark_all()
        self.assertEqual(0, c.get_marked_count())
        c.mark_all(True)
        self.assertEqual(0, c.get_marked_count())
        c.mark_all(False)
        self.assertEqual(0, c.get_marked_count())

        self.add_files(1)
        c = self.search()
        c.mark_all()
        self.assertEqual(1, c.get_marked_count())
        c.mark_all(True)
        self.assertEqual(1, c.get_marked_count())
        c.mark_all(False)
        self.assertEqual(0, c.get_marked_count())
        c.mark_all(True)
        self.assertEqual(1, c.get_marked_count())
        c.mark_all()
        self.assertEqual(0, c.get_marked_count())

        self.add_files(6)
        c = self.search()
        c.mark_all()
        self.assertEqual(6, c.get_marked_count())
        c.mark_all(True)
        self.assertEqual(6, c.get_marked_count())
        c.mark_all(False)
        self.assertEqual(0, c.get_marked_count())
        c.mark_all(True)
        self.assertEqual(6, c.get_marked_count())
        c.mark_all()
        self.assertEqual(0, c.get_marked_count())

        c.mark()
        c.mark_all()
        self.assertEqual(6, c.get_marked_count())
        c.mark_all()
        self.assertEqual(0, c.get_marked_count())

        app.stop()

    def _test_invert_marked(self, app, *args):
        c = self.search()
        c.invert_marked()
        self.assertEqual(0, c.get_marked_count())

        self.add_files(1)
        c = self.search()
        c.invert_marked()
        self.assertEqual(1, c.get_marked_count())
        c.invert_marked()
        self.assertEqual(0, c.get_marked_count())
        c.invert_marked()
        self.assertEqual(1, c.get_marked_count())

        self.add_files(6)
        c = self.search()
        c.invert_marked()
        self.assertEqual(6, c.get_marked_count())
        c.invert_marked()
        self.assertEqual(0, c.get_marked_count())
        c.mark()
        c.go(4)
        c.mark()
        c.invert_marked()
        self.assertEqual(4, c.get_marked_count())
        self.assertFalse(c.get_mark())
        c.invert_marked()
        self.assertEqual(2, c.get_marked_count())
        self.assertTrue(c.get_mark())

        app.stop()

    def _test_tags(self, app, *args):
        c = self.search()
        self.assertItemsEqual(c.get_tags(), [])
        c.add_tag("one")
        self.assertItemsEqual(c.get_tags(), [])

        self.add_files(1)
        c = self.search()
        self.assertItemsEqual(c.get_tags(), [])

        c.add_tag("one")
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "one")])
        c.add_tag("two")
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "one"), (1, 'tag', "two")])
        c.remove_tag("one")
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "two")])
        c.add_tag("three")
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "two"), (1, 'tag', "three")])
        c.remove_tag("three", "two")
        self.assertItemsEqual(c.get_tags(), [])
        c.add_tag("one", "two")
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "one"), (1, 'tag', "two")])

        self.add_files(3)
        c = self.search()
        c.go_last()
        c.add_tag("a")
        c.go_previous()
        c.add_tag("1", "2")
        c.go_first()
        self.assertItemsEqual(c.get_tags(), [])
        c.go_next()
        c.go_next()
        self.assertItemsEqual(c.get_tags(), [(1, 'tag', "a")])

        app.stop()

    def _test_sort(self, app, *args):
        self.add_files(26)
        c = self.search()

        for i in range(26):
            c.add_tag("idx:" + str(i), "abc:" + chr(97 + 25 - i))
            c.go_next()

        c.go_first()
        self.assertItemsEqual(c.get_tags(), [(1, 'idx', "0"), (1, 'abc', "z")])

        c.sort("abc")
        c.go_first()
        self.assertItemsEqual(c.get_tags(), [(1, 'idx', "25"), (1, 'abc', "a")])

        c.sort("#idx")
        c.go_first()
        self.assertItemsEqual(c.get_tags(), [(1, 'idx', "0"), (1, 'abc', "z")])

        c.sort("-#idx")
        c.go_first()
        self.assertItemsEqual(c.get_tags(), [(1, 'idx', "25"), (1, 'abc', "a")])

        c.sort("file_date")

        c.sort("file_date", "-size")

        c.sort("#file_date", "size", "abc")

        app.stop()

    def call_test(self, func):
        a = TestApp()
        p = partial(func, a)
        Clock.schedule_once(p, 0.0001)
        a.run()

    def test_initialization(self):
        self.call_test(self._test_initialization)

    def test_clone(self):
        self.call_test(self._test_clone)

    def test_go_next(self):
        self.call_test(self._test_go_next)

    def test_go_previous(self):
        self.call_test(self._test_go_previous)

    def test_go_first(self):
        self.call_test(self._test_go_first)

    def test_go_last(self):
        self.call_test(self._test_go_last)

    def test_get(self):
        self.call_test(self._test_get)

    def test_get_next_ids(self):
        self.call_test(self._test_get_next_ids)

    def test_get_previous_ids(self):
        self.call_test(self._test_get_previous_ids)

    def test_go(self):
        self.call_test(self._test_go)

    def test_get_tags(self):
        self.call_test(self._test_tags)

    def test_mark(self):
        self.call_test(self._test_mark)

    def test_get_marked_count(self):
        self.call_test(self._test_get_marked_count)

    def test_get_all_marked(self):
        self.call_test(self._test_get_all_marked)

    def test_remove(self):
        self.call_test(self._test_remove)

    def test_len(self):
        self.call_test(self._test_len)

    def test_get_cursor_by_pos(self):
        self.call_test(self._test_get_cursor_by_pos)

    def test_move_to(self):
        self.call_test(self._test_move_to)

    def test_get_position_mapping(self):
        self.call_test(self._test_get_position_mapping)

    def test_cut_marked(self):
        self.call_test(self._test_cut_marked)

    def test_paste_marked(self):
        self.call_test(self._test_paste_marked)

    def test_mark_all(self):
        self.call_test(self._test_mark_all)

    def test_invert_marked(self):
        self.call_test(self._test_invert_marked)

    def test_get_tags(self):
        self.call_test(self._test_tags)

    def test_get_sort(self):
        self.call_test(self._test_sort)


if __name__ == "__main__":
    unittest.main()
