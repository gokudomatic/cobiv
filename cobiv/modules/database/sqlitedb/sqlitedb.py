import logging
import os
import sqlite3
import threading
from os import listdir
from os.path import isfile, join

from PIL import Image
from kivy.app import App
from kivy.factory import Factory

from cobiv.common import set_action
from cobiv.modules.core.entity import Entity
from cobiv.modules.core.session.cursor import CursorInterface
from cobiv.modules.database.sqlitedb.search.searchmanager import SearchManager, TEMP_SORT_TABLE, TEMP_PRESORT_TABLE

SUPPORTED_IMAGE_FORMATS = ["jpg", "gif", "png"]
CURRENT_SET_NAME = '_current'


def is_close(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


#################################################
# Cursor
#################################################

class SqliteCursor(CursorInterface):
    """ Cursor implementation for SQLite.

    """

    core_tags = ["path", "size", "file_date", "ext"]
    logger = logging.getLogger(__name__)

    set_head_key = None
    con = None
    """ SQLite connection instance """
    current_set = True

    def __init__(self, row=None, backend=None, current=True, search_manager=None):
        self.con = backend
        self.current_set = current
        self.search_manager = search_manager
        self.init_row(row)
        self.thumbs_path = App.get_running_app().get_config_value('thumbnails.path')

    def init_row(self, row):
        if row is None:
            self.pos = None
            self.set_head_key = None
            self.filename = ''
            self.file_id = None
        else:
            self.pos = row['position']
            self.set_head_key = row['set_head_key']
            row1 = self.con.execute('select name from file where id=?', (row['file_key'],)).fetchone()
            self.filename = row1['name'] if row is not None else None
            self.file_id = row['file_key']

    def clone(self):
        """
        Create a new copy instance of the cursor.
        :return:
            The new cursor
        """
        new_cursor = SqliteCursor(backend=self.con, current=self.current_set, search_manager=self.search_manager)
        new_cursor.pos = self.pos
        new_cursor.set_head_key = self.set_head_key
        new_cursor.filename = self.filename
        new_cursor.file_id = self.file_id
        return new_cursor

    def go_next(self):
        if self.pos is None:
            return None
        else:
            return self.go(self.pos + 1)

    def go_previous(self):
        if self.pos is None:
            return None
        else:
            return self.go(self.pos - 1)

    def go_first(self):
        return self.go(0)

    def go_last(self):
        if self.pos is None:
            return None
        last_pos_row = self.con.execute('select max(position) from current_set where set_head_key=?',
                                        (self.set_head_key,)).fetchone()
        if last_pos_row is not None:
            return self.go(last_pos_row[0])
        else:
            return None

    def get(self, idx):
        if self.pos is None:
            return None
        row = self.con.execute('select rowid,* from current_set where set_head_key=? and position=?',
                               (self.set_head_key, idx)).fetchone()
        return row

    def get_next_ids(self, amount, self_included=False):
        if self.pos is None:
            return []

        start_pos = self.pos - (1 if self_included else 0)

        rows = self.con.execute(
            'select c.file_key,c.position,f.name from current_set c, file f where f.id=c.file_key and c.set_head_key=? and c.position>=0 and c.position>? and c.position<=? order by position',
            (self.set_head_key, start_pos, start_pos + amount)).fetchall()
        return rows

    def get_previous_ids(self, amount):
        if self.pos is None:
            return []

        rows = self.con.execute(
            'select c.file_key,c.position,f.name from current_set c, file f where f.id=c.file_key and c.set_head_key=? and c.position>=0 and c.position<? and c.position>=? order by position desc',
            (self.set_head_key, self.pos, self.pos - amount)).fetchall()
        return rows

    def go(self, idx):
        if self.pos is None:
            return None
        row = self.con.execute('select rowid,* from current_set where position>=0 and position=?',
                               (idx,)).fetchone()
        if row is not None:
            self.init_row(row)
        return self if row is not None else None

    def mark(self, value=None):
        if self.pos is None:
            return
        with self.con:
            if self.get_mark() and value is None or value == False:
                self.con.execute('delete from marked where file_key=?', (self.file_id,))
            else:
                self.con.execute('insert into marked values (?)', (self.file_id,))

    def get_mark(self):
        if self.pos is None:
            return False
        return self.con.execute('select count(*) from marked where file_key=?', (self.file_id,)).fetchone()[0] > 0

    def get_all_marked(self):
        return [r[0] for r in self.con.execute('select file_key from marked', ).fetchall()]

    def get_marked_count(self):
        return self.con.execute('select count(*) from marked', ).fetchone()[0]

    def __len__(self):
        if self.pos is None:
            return 0
        row = self.con.execute('select count(*) from current_set where position>=0').fetchone()

        return 0 if row is None else row[0]

    def remove(self):
        if self.pos is None:
            return

        new_pos = self.pos
        next = self.get(self.pos + 1)
        if next is None:
            next = self.get(self.pos - 1)
            new_pos = self.pos - 1
        with self.con:
            self.con.execute('delete from current_set where file_key=?', (self.file_id,))
            self.con.execute('delete from marked where file_key=?', (self.file_id,))
            self.con.execute('update current_set set position=position-1 where set_head_key=? and position>?',
                             (self.set_head_key, self.pos))

        self.init_row(next)

        self.pos = new_pos

        return True

    def get_cursor_by_pos(self, pos):
        return SqliteCursor(row=self.get(pos), backend=self.con, search_manager=self.search_manager)

    def get_thumbnail_filename(self, file_id):
        return os.path.join(self.thumbs_path, str(file_id) + '.png')

    def move_to(self, pos):
        if pos == self.pos or self.file_id is None:
            return

        pos = max(0, min(pos, len(self) - 1))

        if pos < self.pos:
            query = 'update current_set set position=position+1 where set_head_key=? and position<? and position>=?'
        else:
            query = 'update current_set set position=position-1 where set_head_key=? and position>? and position<=?'

        with self.con:
            self.con.execute('update current_set set position=-1 where set_head_key=? and position=?',
                             (self.set_head_key, self.pos))
            self.con.execute(query, (self.set_head_key, self.pos, pos))
            self.con.execute('update current_set set position=? where set_head_key=? and position=-1',
                             (pos, self.set_head_key))

        self.pos = pos

    def get_position_mapping(self, file_id_list):
        if file_id_list is None:
            return []

        rows = self.con.execute(
            'select file_key,position from current_set where set_head_key=? and file_key in (%s)' % ','.join(
                '?' * len(file_id_list)),
            (self.set_head_key,) + tuple(file_id_list)).fetchall()

        return rows

    def mark_all(self, value=None):
        with self.con:
            if value is None:
                value = self.con.execute(
                    'select count(*) from current_set c left join marked m on m.file_key=c.file_key' +
                    ' where m.file_key is null and c.position>=0').fetchone()[0] > 0

            self.con.execute('delete from marked')
            if value:
                self.con.execute('insert into marked (file_key) select file_key from current_set where position>=0')

    def _get_tag_key_value(self, tag):
        key = "tag"
        value = tag
        if ':' in tag:
            values = tag.split(':')
            key = values[0]
            value = values[1]
        return (key, value)

    def invert_marked(self):
        with self.con:
            self.con.execute(
                'create temporary table marked1 as select cs.file_key from current_set cs left join marked m on m.file_key=cs.file_key' +
                ' where m.file_key is null and cs.position>=0')
            self.con.execute('delete from marked')
            self.con.execute('insert into marked select file_key from marked1')
            self.con.execute('drop table marked1')

    def add_tag(self, *args):
        if len(args) == 0 or self.file_id is None:
            return

        with self.con:
            for tag in args:
                key, value = self._get_tag_key_value(tag)
                c = self.con.execute(
                    'select category from tag where kind=? and (value=? or category=0) and file_key=? limit 1',
                    (key, value, self.file_id))
                row = c.fetchone()
                if row is None:
                    c.execute('insert into tag values (?,?,?,?,?)', (self.file_id, 1, key, 0, value))
                elif row[0] == 0:
                    c.execute('update tag set value=? where category=0 and kind=? and file_key=?',
                              (value, key, self.file_id))

    def remove_tag(self, *args):
        if len(args) == 0 or self.file_id is None:
            return

        with self.con:
            for tag in args:
                key, value = self._get_tag_key_value(tag)
                self.con.execute('delete from tag where file_key=? and category=1 and kind=? and value=?',
                                 (self.file_id, key, value))

    def get_tags(self):
        if self.file_id is None:
            return []

        c = self.con.cursor()
        c.execute('select t.category,t.kind,t.value from tag t where file_key=?', (self.file_id,))
        tags = [(r['category'], r['kind'], r['value']) for r in c.fetchall()]

        c = c.execute('select %s from core_tags where file_key=?' % ','.join(self.core_tags), (self.file_id,))
        row = c.fetchone()
        if row is not None:
            for t in self.core_tags:
                tags.append((0, t, row[t]))

        return tags

    def is_changed(self):
        if self.file_id is None:
            return False

        tags = self.get_tags()
        for tag in tags:
            if tag[0] != 0:
                continue

            if tag[1] == 'modification_date':
                if tag[2] != os.path.getmtime(self.filename):
                    return True
            elif tag[1] == 'size':
                if tag[2] != os.path.getsize(self.filename):
                    return True

        return False

    def cut_marked(self):
        with self.con:
            self.con.execute('delete from current_set where position<0')
            self.con.execute(
                'create temporary table renum_clip as select c.rowid fkey from current_set c, marked m where c.file_key=m.file_key and c.position>=0 order by c.position')
            self.con.execute('create unique index renum_clip_idx on renum_clip(fkey)')  # improve performance
            self.con.execute(
                'update current_set set position=(select -1*r.rowid from renum_clip r where r.fkey=current_set.rowid) where exists (select * from renum_clip where renum_clip.fkey=current_set.rowid)')
            self.con.execute('drop table renum_clip')
        self.reenumerate_current_set_positions()
        self.mark_all(False)

    def reenumerate_current_set_positions(self):
        with self.con:
            self.con.execute(
                'create temporary table renum as select rowid fkey from current_set where position>=0 order by position')
            self.con.execute('create unique index renum_idx on renum(fkey)')  # improve performance
            self.con.execute(
                'update current_set set position=(select r.rowid-1 from renum r where r.fkey=current_set.rowid) where exists (select * from renum where renum.fkey=current_set.rowid)')
            self.con.execute('drop table renum')

    def paste_marked(self, new_pos=None, append=False):
        if new_pos is None:
            new_pos = self.pos

        with self.con:
            # get clipboard size
            size = self.con.execute('select count(*) from current_set where position<0').fetchone()[0]
            if size == 0:
                return

            if append:
                new_pos = len(self)

            else:
                # make the place
                self.con.execute('update current_set set position=position+' + str(size) + ' where position>=?',
                                 (new_pos,))
            # update the negative positions
            self.con.execute(
                'update current_set set position=-1*position+' + str(new_pos - 1) + ' where position<0')

    def get_clipboard_size(self):
        if self.pos is None:
            return 0
        row = self.con.execute('select count(*) from current_set where position<0').fetchone()

        return 0 if row is None else row[0]

    def sort(self, *fields):
        """
            Sort the current set with various criteria
        :param fields: list of sort criteria
        """
        with self.con:
            # step 1
            c = self.con.execute('drop table if exists %s' % TEMP_SORT_TABLE)
            c.execute('drop table if exists %s' % TEMP_PRESORT_TABLE)
            # step 2
            query, sort_query = self.search_manager.generate_sort_query(fields)
            c.execute(query)
            c.execute(sort_query)

            c.execute('create index temp_sort_index1 on %s(file_key)' % TEMP_SORT_TABLE)

            # step 3
            update_query = 'update current_set set position=(select r.rowid-1 from %s r where r.file_key=current_set.file_key) where exists (select * from %s r where r.file_key=current_set.file_key)' % (
                TEMP_SORT_TABLE, TEMP_SORT_TABLE)
            self.logger.debug(update_query)
            self.con.execute(update_query)


##############################
# DB connector
################################

class SqliteDb(Entity):
    logger = logging.getLogger(__name__)

    cancel_operation = False
    session = None

    def init_test_db(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA temp_store = MEMORY')
        self.conn.execute('PRAGMA locking_mode = EXCLUSIVE')
        self.create_database(sameThread=True)
        with self.conn:
            self.conn.execute('create temporary table marked (file_key int)')
            self.conn.execute('create temporary table if not exists current_set as select * from set_detail where 1=2')

        self.search_manager = SearchManager(self.session)

    def close_db(self):
        self.conn.close()

    def ready(self):
        if not os.path.exists(self.get_app().get_user_path('thumbnails')):
            os.makedirs(self.get_app().get_user_path('thumbnails'))

        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()
        self.search_manager = SearchManager(self.session)

        # add actions
        set_action("search", self.search_tag, "viewer")
        set_action("search", self.search_tag, "browser")
        set_action("add-tag", self.add_tag, "viewer")
        set_action("add-tag", self.add_tag, "browser")
        set_action("rm-tag", self.remove_tag, "viewer")
        set_action("rm-tag", self.remove_tag, "browser")
        set_action("ls-tag", self.list_tags, "viewer")
        set_action("ls-tag", self.list_tags, "browser")
        set_action("updatedb", self.updatedb)
        set_action("mark-all", self.mark_all)
        set_action("mark-invert", self.invert_marked)
        set_action("rnc", self.reenumerate_current_set_positions)
        set_action("cut-marked", self.cut_marked)
        set_action("paste-marked", self.paste_marked)

        self.session = self.get_app().lookup("session", "Entity")

        must_initialize = True
        try:
            must_initialize = self.conn.execute('select 1 from catalog limit 1').fetchone() is None
        except sqlite3.OperationalError:
            pass

        if must_initialize:
            self.create_database()
        with self.conn:
            self.conn.execute('create temporary table marked (file_key int)')
            self.conn.execute('create temporary table current_set as select * from set_detail where 1=2')

    def create_database(self, sameThread=False):
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
            self.conn.execute('create index tag_idx2 on tag(kind,value)')
            self.conn.execute('create index tag_idx3 on tag(value)')
            self.conn.execute('create unique index core_tags_idx1 on core_tags(file_key)')
            self.conn.execute('create unique index core_tags_idx2 on core_tags(path,size,file_date,ext)')
            self.conn.execute('create unique index set_detail_pos_idx on set_detail(set_head_key,position)')
            self.conn.execute('create unique index set_detail_file_idx on set_detail(set_head_key,file_key)')

        self.create_catalogue("default")

        repos = self.get_global_config_value('repository', self.get_app().get_user_path('Pictures'))
        self.add_repository("default", repos)
        self.updatedb(sameThread=sameThread)

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

    def updatedb(self, sameThread=False):
        if sameThread:
            self._threaded_updatedb()
        else:
            threading.Thread(target=self._threaded_updatedb).start()

    def _threaded_updatedb(self):
        self.start_progress("Initializing update...")
        c = self.conn.execute('select id, path, recursive from repository')
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
                self.update_tags(diff[0], diff[1])
                if self.cancel_operation:
                    break

            self.regenerate_set('*', "select id from file", caption="Creating default set...")

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
                query_to_rem = [(n,) for n in to_rem]
                self.conn.executemany('delete from file where name=?', query_to_rem)
                self.tick_progress()

            query_to_add = []
            query_tag_to_add = []
            # add new ones
            for f in to_add:
                if self.cancel_operation:
                    return
                query_to_add.append((repo_id, f))
                query_tag_to_add.append(
                    (repo_id, f, os.path.getsize(f), os.path.getmtime(f), os.path.splitext(f)[1][1:],
                     os.path.dirname(f)))

                self.tick_progress()

            c.executemany('insert into file(repo_key, name) values(?,?)', query_to_add)

            c.execute('create temporary table t1(repo int,file text,size int,cdate float,ext text, path text)')

            c.executemany('insert into t1(repo,file,size,cdate,ext,path) values(?,?,?,?,?,?)', query_tag_to_add)
            c.execute(
                'insert into core_tags (file_key, path, size, file_date, ext) select f.rowid,t.path,t.size,t.cdate,t.ext from file f,t1 t where f.repo_key=t.repo and f.name=t.file')

            c.execute('drop table t1')
            self.tick_progress()
            tags_to_add = []
            for f in to_add:
                id = c.execute('select id from file where repo_key=? and name=? limit 1', (repo_id, f)).fetchone()[0]
                lines = self.read_tags(id, f)
                if len(lines) > 0:
                    tags_to_add.extend(lines)
                self.tick_progress()

            if len(tags_to_add) > 0:
                c.executemany('insert into tag values (?,?,?,?,?)', tags_to_add)
                self.tick_progress()

    def update_tags(self, repo_id, to_ignore=[]):
        with self.conn:
            c = self.conn.cursor()

            modified_file_ids = self._check_modified_files(repo_id, to_ignore=to_ignore)
            for file_id, filename in modified_file_ids:
                c.execute('update core_tags set size=?,file_date=?,ext=?,path=? where file_key=?',
                          (os.path.getsize(filename), os.path.getmtime(filename), os.path.splitext(filename)[1][1:],
                           os.path.dirname(filename), file_id))

                tags_to_add = self.read_tags(file_id, filename)

                c.executemany('update tag set value=?,type=? where file_key=? and category=0 and kind=?',
                              [(tag[4], tag[3], tag[0], tag[2]) for tag in tags_to_add if tag[1] == 0])
                c.executemany('insert or ignore into tag values (?,?,?,?,?)',
                              [tag for tag in tags_to_add if tag[1] == 1])

                self.get_app().fire_event('on_file_content_change', file_id)

    def _check_modified_files(self, repo_id, to_ignore=[]):
        result = []

        with self.conn:
            c = self.conn.execute(
                'select f.id,f.name,t.file_date,t.size from file f,core_tags t where repo_key=? and f.id=t.file_key order by f.id',
                (repo_id,))

            for file_id, filename, file_date, size in c.fetchall():
                if file_id in to_ignore:
                    continue

                if int(size) != os.path.getsize(filename) or not is_close(float(file_date),
                                                                          os.path.getmtime(filename),
                                                                          abs_tol=1e-05, rel_tol=0):
                    result.append((file_id, filename))

        return result

    def read_tags(self, node_id, name):
        to_add = []
        img = Image.open(name)

        to_add.append((node_id, 0, 'width', 1, str(img.size[0])))
        to_add.append((node_id, 0, 'height', 1, str(img.size[1])))
        to_add.append((node_id, 0, 'format', 0, img.format))

        if img.info:
            for i, v in img.info.iteritems():
                if i == "tags":
                    tag_list = v.split(",")
                    for tag in tag_list:
                        to_add.append((node_id, 1, 'tag', 0, tag.strip()))

        for reader in self.get_app().lookups("TagReader"):
            reader.read_file_tags(node_id, name, to_add)

        return to_add

    def regenerate_set(self, set_name, query, caption=None):

        is_current = set_name == "_current"

        with self.conn:
            c = self.conn.cursor()

            if is_current:
                c.execute('drop table if exists current_set') \
                    .execute(
                    'create temporary table current_set as select * from set_detail where 1=2') \
                    .execute('create index cs_index1 on current_set(file_key)')
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
            self.set_progress_max_count(len(resultset) + 1)
            self.reset_progress(caption)
            lines = []
            thread_count = 0
            for row in resultset:
                lines.append((head_key, thread_count, row['id']))
                self.tick_progress()
                thread_count += 1

            query = 'insert into %s (set_head_key, position, file_key) values (?,?,?)' % (
                'current_set' if is_current else 'set_detail')
            c.executemany(query, lines)
            self.tick_progress()

    def copy_set_to_current(self, set_name):
        with self.conn:
            c = self.conn.execute('drop table if exists current_set').execute(
                'create temporary table current_set as select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? order by d.position',
                set_name).execute('create index cs_index1 on current_set(file_key)')

    def search_tag(self, *args):
        if len(args) == 0:
            self.copy_set_to_current('*')
        else:
            query = self.search_manager.generate_search_query(*args)
            self.logger.debug(query)
            self.regenerate_set(CURRENT_SET_NAME, query)

        row = self.conn.execute('select rowid, * from current_set where position=0 limit 1').fetchone()
        self.session.cursor.set_implementation(
            None if row is None else SqliteCursor(row=row, backend=self.conn, search_manager=self.search_manager))

        self.execute_cmd("load-set")

    def add_tag(self, *args):
        self.session.cursor.add_tag(*args)
        self.execute_cmd("refresh-info")

    def remove_tag(self, *args):
        self.session.cursor.remove_tag(*args)
        self.execute_cmd("refresh-info")

    def list_tags(self):
        tags = self.session.cursor.get_tags()
        text = '\n'.join([value for kind, value in tags[1]])
        App.get_running_app().root.notify(text)

    def on_application_quit(self):
        self.cancel_operation = True

    def mark_all(self, value=None):
        self.session.cursor.mark_all(value)
        self.execute_cmd("refresh-marked")

    def invert_marked(self):
        self.session.cursor.invert_marked()
        self.execute_cmd("refresh-marked")

    def reenumerate_current_set_positions(self):
        self.session.cursor.reenumerate_current_set_positions()

    def cut_marked(self):
        self.session.cursor.cut_marked()

    def paste_marked(self, new_pos):
        self.session.cursor.paste_marked()


Factory.register('Cursor', module=SqliteCursor)
