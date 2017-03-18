import sys
import os
from os import listdir
from os.path import isfile, join
from PIL import Image
from kivy.app import App
from kivy.factory import Factory
from kivy.properties import NumericProperty

from cobiv.common import set_action
from cobiv.modules.component import Component
from cobiv.modules.entity import Entity

import threading
import sqlite3
from cobiv.modules.session.cursor import Cursor

SUPPORTED_IMAGE_FORMATS = ["jpg", "gif", "png"]


class SqliteCursor(Cursor):
    set_detail_id = None
    pos = None
    set_head_key = None
    con = None
    file_key = None
    tablename=None

    def __init__(self, row, backend=None, current=True):
        self.set_detail_id = row['rowid']
        self.pos = row['position']
        self.set_head_key = row['set_head_key']
        self.file_key = row['file_key']
        self.current_set = current
        self.tablename= 'current_set' if self.current_set else 'set_detail'

        self.con = backend

    def get_next(self):
        return self.get(self.pos + 1)

    def get_previous(self):
        return self.get(self.pos - 1)

    def get_tags(self):
        return []

    def filename(self):
        filename = self.con.execute('select name from file where rowid=?', self.file_key).fetchone()
        return filename[0] if filename is not None else None

    def get_first(self):
        return self.get(0)

    def get_last(self):
        last_pos_row = self.con.execute('max(position) from %s where set_head_key=?' % self.tablename,
                                        self.set_head_key).fetchone()
        return self if last_pos_row is None else self.get(last_pos_row[0])

    def get(self, idx):
        row = self.con.execute('select * from %s where set_head_key=? and position=?' % self.tablename,
                                self.set_head_key, idx).fetchone()
        return SqliteCursor(row, self.con, self.current_set) if row is not None else self

    def __len__(self):
        row = self.con.execute('count(1) from %s where set_head_key=?' % self.tablename,
                               self.set_head_key).fetchone()

        return 0 if row is None else row[0]


class SqliteDb(Entity):
    # current_imageset = None
    cancel_operation = False
    session = None

    def __init__(self):
        # self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn = sqlite3.connect("cobiv.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # add actions
        set_action("search", self.search_tag, "viewer")
        set_action("search", self.search_tag, "browser")
        set_action("add-tag", self.add_tag, "viewer")
        set_action("rem-tag", self.remove_tag, "viewer")
        set_action("ls-tag", self.list_tags, "viewer")
        set_action("updatedb", self.updatedb)

    def ready(self):
        Component.ready(self)
        self.session = self.get_app().lookup("session", "Entity")

        must_initialize = True
        try:
            must_initialize = self.conn.execute('select 1 from catalog limit 1').fetchone() is None
        except sqlite3.OperationalError:
            pass

        if must_initialize:
            self.init_database()

    def init_database(self):
        with self.conn:
            self.conn.execute('create table catalog (name text)')
            self.conn.execute('create table repository (catalog_key int, path text, recursive num)')
            self.conn.execute('create table file (repo_key int, name text, filename text, path text, ext text)')
            self.conn.execute('create table tag (file_key int, kind text, value text)')
            self.conn.execute('create table set_head ( name text, readonly num)')
            self.conn.execute('create table set_detail (set_head_key int, position int, file_key int)')

            # indexes
            self.conn.execute('create unique index file_idx on file(name)')
            self.conn.execute('create unique index tag_idx on tag(file_key,kind,value)')
            self.conn.execute('create unique index set_detail_pos_idx on set_detail(set_head_key,position)')
            self.conn.execute('create unique index set_detail_file_idx on set_detail(set_head_key,file_key)')

        self.create_catalogue("default")
        self.add_repository("default", "C:\\Users\\edwin\\Pictures")
        self.updatedb()

    def create_catalogue(self, name):
        try:
            with self.conn:
                c = self.conn.execute("insert into catalog (name) values(?) ", (name,))
            return c.lastrowid
        except sqlite3.IntegrityError:
            return False

    def add_repository(self, catalogue, path, recursive=True):
        try:
            with self.conn:
                c = self.conn.execute('insert into repository (catalog_key,path,recursive) values (?,?,?)',
                                      (catalogue, path, 1 if recursive else 0))
            return c.lastrowid
        except sqlite3.IntegrityError:
            return False

    def updatedb(self):
        threading.Thread(target=self._threaded_updatedb).start()

    def _threaded_updatedb(self):
        self.start_progress("Initializing update...")
        c = self.conn.execute('select rowid, path, recursive from repository')
        differences = []
        thread_max_files = 0

        rows = c.fetchall()
        self.set_progress_max_count(len(rows))
        for row in rows:
            repo_id = row[0]
            to_add, to_remove = self._update_get_diff(repo_id, row[1], row[2])
            differences.append((repo_id, to_add, to_remove))
            thread_max_files += len(to_add) + len(to_remove) + 1 if len(to_add) > 0 else 0 + 1 if len(
                to_remove) > 0 else 0
            self.tick_progress()

        if thread_max_files > 0:
            self.reset_progress("Updating files...")
            self.set_progress_max_count(thread_max_files)

            for diff in differences:
                self._update_dir(diff[0], diff[1], diff[2])
                if self.cancel_operation:
                    break

            self.regenerate_set('*', "select rowid from file", caption="Creating default set...")

        self.stop_progress()

    def _update_get_diff(self, repo_id, path, recursive):
        if recursive:
            result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if
                      os.path.splitext(f)[1][1:] in SUPPORTED_IMAGE_FORMATS]
        else:
            result = [join(path, f) for f in listdir(path) if
                      isfile(join(path, f)) and f.split('.')[-1] in SUPPORTED_IMAGE_FORMATS]

        c = self.conn.execute('select name from file where repo_key=?', (repo_id,))
        existing = [n['name'] for n in c.fetchall()]

        new_files = set(result) - set(existing)
        removed_files = set(existing) - set(result)
        return new_files, removed_files

    def _update_dir(self, repo_id, to_add, to_rem):
        with self.conn:
            c = self.conn.cursor()

            # remove old ones
            if len(to_rem) > 0:
                query_to_rem=[(n,) for n in to_rem]
                self.conn.executemany('delete from file where name=?', query_to_rem)
                self.tick_progress()

            query_to_add = []
            # add new ones
            for f in to_add:
                if self.cancel_operation:
                    return
                query_to_add.append((repo_id, f, os.path.basename(f), os.path.dirname(f), os.path.splitext(f)[1][1:]))
                self.tick_progress()

            c.executemany('insert into file(repo_key, name, filename, path, ext) values(?,?,?,?,?)', query_to_add)
            self.tick_progress()
            tags_to_add = []
            for f in to_add:
                id=c.execute('select rowid from file where repo_key=? and name=? limit 1', (repo_id,f)).fetchone()[0]
                lines = self.read_tags(id, f)
                if len(lines) > 0:
                    tags_to_add.extend(lines)
                self.tick_progress()

            if len(tags_to_add) > 0:
                c.executemany('insert into tag values (?,?,?)', tags_to_add)
                self.tick_progress()

    def read_tags(self, node_id, name):
        to_add = []
        img = Image.open(name)
        if img.info:
            for i, v in img.info.iteritems():
                if i == "tags":
                    tag_list = v.split(",")
                    for tag in tag_list:
                        to_add.append((node_id, 'tag', tag.strip()))
        return to_add

    def regenerate_set(self, set_name, query, caption=None):

        with self.conn:
            c = self.conn.cursor()

            row = c.execute('select rowid from set_head where name=?', set_name).fetchone()
            if row is not None:
                head_key = row[0]
                c.execute('delete from set_detail where set_head_key=?', (head_key,))
            else:
                c.execute('insert into set_head values (?,?)', (set_name, 0))
                head_key = c.lastrowid

            resultset = c.execute(query).fetchall()
            self.set_progress_max_count(len(resultset) + 1)
            self.reset_progress(caption)
            lines = []
            thread_count = 0
            for row in resultset:
                lines.append((head_key, thread_count, row['rowid']))
                self.tick_progress()
                thread_count += 1
            c.executemany('insert into set_detail (set_head_key, position, file_key) values (?,?,?)',
                          lines)
            self.tick_progress()

    def copy_set_to_current(self, set_name):
        with self.conn:
            self.conn.execute('drop table current_set') \
                .execute('create temporary table current_set as select * from set_detail where name=?', set_name)

    def search_tag(self, *args):
        root = self.get_app().root

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

            query = 'select f.name from file f ,tag t where t.file_key=f.rowid '
            if len(to_include) > 0:
                query += 'and t.value in (' + ', '.join(to_include) + ') '
            if len(to_exclude) > 0:
                query += 'and t.value not in (' + ', '.join(to_exclude) + ') '

            self.regenerate_set('current', self.conn.execute(query).fetchall())

            row = self.conn.execute('select * from current_set limit 1').fetchone()
            if row is None:
                self.session.cursor = Cursor(None)
            else:
                self.session.cursor = SqliteCursor(row, self.conn)

        root.execute_cmd("load-set")

    def add_tag(self, *args):
        c = self.conn.cursor()
        for tag in args:
            c.execute('select count(1) from tag where value=? and file_key=?', tag, self.session.cursor.file_key)
            if c.fetchone()[0] == 0:
                c.execute('insert into tag (?,?,?)', self.session.cursor.file_key, 'tag', tag)
        self.conn.commit()

    def remove_tag(self, *args):
        if len(args) == 0:
            return
        self.conn.execute('delete from tag where file_key=? and value in (?)', self.session.cursor.file_key,
                          ', '.join(args))
        self.conn.commit()

    def list_tags(self):
        c = self.conn.cursor()
        c.execute('select value from tag where file_key=?', self.session.cursor.file_key)
        for row in c.fetchall():
            App.get_running_app().root.notify(row[0])

    def on_application_quit(self):
        self.cancel_operation = True


Factory.register('Cursor', module=SqliteCursor)
