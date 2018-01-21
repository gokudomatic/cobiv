import logging
import sqlite3
import threading

import os, io, time
from fs import open_fs

from PIL import Image
from kivy.app import App
from kivy.factory import Factory

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
            self.filename = ''
            self.file_id = None
            self.repo_key = None
        else:
            self.pos = row['position']
            row1 = self.con.execute('select name, repo_key from file where id=?', (row['file_key'],)).fetchone()
            self.filename = row1['name'] if row is not None else None
            self.file_id = row['file_key']
            self.repo_key = row1['repo_key']

    def clone(self):
        """
        Create a new copy instance of the cursor.
        :return:
            The new cursor
        """
        new_cursor = SqliteCursor(backend=self.con, current=self.current_set, search_manager=self.search_manager)
        new_cursor.pos = self.pos
        new_cursor.filename = self.filename
        new_cursor.file_id = self.file_id
        new_cursor.repo_key = self.repo_key
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
        last_pos_row = self.con.execute('select max(position) from current_set').fetchone()
        if last_pos_row is not None:
            return self.go(last_pos_row[0])
        else:
            return None

    def get(self, idx):
        if self.pos is None:
            return None
        row = self.con.execute('select rowid,* from current_set where position=?',
                               (idx,)).fetchone()
        return row

    def get_next_ids(self, amount, self_included=False):
        if self.pos is None:
            return []

        start_pos = self.pos - (1 if self_included else 0)

        rows = self.con.execute(
            'select c.file_key,c.position,f.name,f.repo_key from current_set c, file f where f.id=c.file_key and c.position>=0 and c.position>? and c.position<=? order by position',
            (start_pos, start_pos + amount)).fetchall()
        return rows

    def get_previous_ids(self, amount):
        if self.pos is None:
            return []

        rows = self.con.execute(
            'select c.file_key,c.position,f.name,f.repo_key from current_set c, file f where f.id=c.file_key and c.position>=0 and c.position<? and c.position>=? order by position desc',
            (self.pos, self.pos - amount)).fetchall()
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
            self.con.execute('update current_set set position=position-1 where position>?',
                             (self.pos,))

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
            query = 'update current_set set position=position+1 where position<? and position>=?'
        else:
            query = 'update current_set set position=position-1 where position>? and position<=?'

        with self.con:
            self.con.execute('update current_set set position=-1 where position=?',
                             (self.pos,))
            self.con.execute(query, (self.pos, pos))
            self.con.execute('update current_set set position=? where position=-1',
                             (pos,))

        self.pos = pos

    def get_position_mapping(self, file_id_list):
        if file_id_list is None:
            return []

        rows = self.con.execute(
            'select file_key,position from current_set where file_key in (%s)' % ','.join(
                '?' * len(file_id_list)),
            tuple(file_id_list)).fetchall()

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
    conn = None
    search_manager = None
    set_manager = None

    def init_test_db(self, session):

        self.get_app().register_event_observer('on_current_set_change', self.on_current_set_change)

        self.session = session
        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()

        self.set_manager = self.lookup('sqliteSetManager', 'Entity')
        self.set_manager.ready()

        self.create_database(sameThread=True)
        with self.conn:
            self.conn.execute('create temporary table marked (file_key int)')
            self.conn.execute('create temporary table if not exists current_set as select * from set_detail where 1=2')

        self.search_manager = SearchManager(self.session)

        # open file systems
        c = self.conn.execute('select id,path from repository')
        for repo_key, path in c.fetchall():
            fs = open_fs(path)
            self.session.add_filesystem(repo_key, fs)

    def close_db(self):
        self.conn.close()

    def ready(self):

        self.get_app().register_event_observer('on_current_set_change', self.on_current_set_change)

        if not os.path.exists(self.get_app().get_user_path('thumbnails')):
            os.makedirs(self.get_app().get_user_path('thumbnails'))

        self.session = self.get_session()

        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()
        self.search_manager = SearchManager(self.session)

        self.set_manager = self.lookup('sqliteSetManager', 'SetManager')

        # add actions
        self.session.set_action("search", self.search_tag, "viewer")
        self.session.set_action("search", self.search_tag, "browser")
        self.session.set_action("add-tag", self.add_tag, "viewer")
        self.session.set_action("add-tag", self.add_tag, "browser")
        self.session.set_action("rm-tag", self.remove_tag, "viewer")
        self.session.set_action("rm-tag", self.remove_tag, "browser")
        self.session.set_action("ls-tag", self.list_tags, "viewer")
        self.session.set_action("ls-tag", self.list_tags, "browser")
        self.session.set_action("updatedb", self.updatedb)
        self.session.set_action("mark-all", self.mark_all)
        self.session.set_action("mark-invert", self.invert_marked)
        self.session.set_action("rnc", self.reenumerate_current_set_positions)
        self.session.set_action("cut-marked", self.cut_marked)
        self.session.set_action("paste-marked", self.paste_marked)

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

        # open file systems
        c = self.conn.execute('select id,path from repository')
        for repo_key, path in c.fetchall():
            fs = open_fs(path)
            self.session.add_filesystem(repo_key, fs)

    def create_database(self, sameThread=False):
        with self.conn:
            fd = open(os.path.abspath(os.path.dirname(__file__)) + '/../../../resources/sql/sqlite_db.sql')
            script = fd.read()
            self.conn.executescript(script)
            fd.close()

        self.create_catalogue("default")

        repos = self.get_global_config_value('repositories', self.get_app().get_user_path('Pictures'))
        self.add_repository("default", repos)
        self.updatedb(sameThread=sameThread)

    def create_catalogue(self, name):
        try:
            with self.conn:
                c = self.conn.execute("insert into catalog (name) values(?) ", (name,))
            return c.lastrowid
        except sqlite3.IntegrityError:
            return False

    def add_repository(self, catalogue, path_list, recursive=True):
        for path in path_list:
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
        for repo_id, repo_path, recursive in rows:
            to_add, to_remove = self._update_get_diff(repo_id, repo_path, recursive)
            differences.append((repo_id, repo_path, to_add, to_remove))
            thread_max_files += len(to_add) + len(to_remove) + 1 if len(to_add) > 0 else 0 + 1 if len(
                to_remove) > 0 else 0
            self.tick_progress()

        if thread_max_files > 0:
            self.reset_progress("Updating files...")
            self.set_progress_max_count(thread_max_files)

            repo_fs, current_repo_id = None, None
            for repo_id, repo_path, to_add, to_remove in differences:
                if repo_id != current_repo_id:
                    if current_repo_id is not None:
                        repo_fs.close()
                    current_repo_id = repo_id
                    repo_fs = open_fs(repo_path)

                self._update_dir(repo_id, repo_fs, to_add, to_remove)
                self.update_tags(repo_id, repo_fs, to_add)
                if self.cancel_operation:
                    break

            if repo_fs is not None:
                repo_fs.close()

            self.set_manager.regenerate_default()

        self.stop_progress()

    def _update_get_diff(self, repo_id, path, recursive):

        repo_fs = open_fs(path)

        if recursive:

            result = [path for path in repo_fs.walk.files(filter=['*.jpg', '*.png'])]
        else:
            result = [f for f in repo_fs.listdir('/') if
                      repo_fs.getinfo(f, namespaces=['details']).is_file and f.split('.')[
                          -1] in SUPPORTED_IMAGE_FORMATS]

        repo_fs.close()

        c = self.conn.execute('select name from file where repo_key=?', (repo_id,))
        existing = [n['name'] for n in c.fetchall()]

        new_files = set(result) - set(existing)
        removed_files = set(existing) - set(result)
        return new_files, removed_files

    def _update_dir(self, repo_id, repo_fs, to_add, to_rem):
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
                query_to_add.append((repo_id, f,1,"file"))
                file_info = repo_fs.getdetails(f)
                modified_date = time.mktime(file_info.modified.timetuple())
                query_tag_to_add.append(
                    (repo_id, f, file_info.size, modified_date, os.path.splitext(f)[1][1:],
                     os.path.dirname(f)))

                self.tick_progress()

            c.executemany('insert into file(repo_key, name,searchable,file_type) values(?,?,?,?)', query_to_add)

            c.execute('create temporary table t1(repo int,file text,size int,cdate float,ext text, path text)')

            c.executemany('insert into t1(repo,file,size,cdate,ext,path) values(?,?,?,?,?,?)', query_tag_to_add)
            c.execute(
                'insert into core_tags (file_key, path, size, file_date, ext) select f.rowid,t.path,t.size,t.cdate,t.ext from file f,t1 t where f.repo_key=t.repo and f.name=t.file')

            c.execute('drop table t1')
            self.tick_progress()
            tags_to_add = []
            for f in to_add:
                id = c.execute('select id from file where repo_key=? and name=? limit 1', (repo_id, f)).fetchone()[0]
                lines = self.read_tags(id, f, repo_fs)
                if len(lines) > 0:
                    tags_to_add.extend(lines)
                self.tick_progress()

            if len(tags_to_add) > 0:
                c.executemany('insert into tag values (?,?,?,?,?)', tags_to_add)
                self.tick_progress()

    def update_tags(self, repo_id, repo_fs, to_ignore=[]):
        with self.conn:
            c = self.conn.cursor()

            modified_file_ids = self._check_modified_files(repo_id, repo_fs, to_ignore=to_ignore)
            for file_id, filename in modified_file_ids:
                file_info = repo_fs.getdetails(filename)

                c.execute('update core_tags set size=?,file_date=?,ext=?,path=? where file_key=?',
                          (file_info.size, file_info.modified, os.path.splitext(filename)[1][1:],
                           os.path.dirname(filename), file_id))

                tags_to_add = self.read_tags(file_id, filename, repo_fs=repo_fs)

                c.executemany('update tag set value=?,type=? where file_key=? and category=0 and kind=?',
                              [(tag[4], tag[3], tag[0], tag[2]) for tag in tags_to_add if tag[1] == 0])
                c.executemany('insert or ignore into tag values (?,?,?,?,?)',
                              [tag for tag in tags_to_add if tag[1] == 1])

                self.get_app().fire_event('on_file_content_change', file_id)

    def _check_modified_files(self, repo_id, repo_fs, to_ignore=[]):
        result = []

        with self.conn:
            c = self.conn.execute(
                'select f.id,f.name,t.file_date,t.size from file f,core_tags t where repo_key=? and f.id=t.file_key order by f.id',
                (repo_id,))

            for file_id, filename, file_date, size in c.fetchall():
                if file_id in to_ignore:
                    continue

                file_info = repo_fs.getdetails(filename)

                modified_date = time.mktime(file_info.modified.timetuple())

                if int(size) != file_info.size or not is_close(float(file_date),
                                                               modified_date,
                                                               abs_tol=1e-05, rel_tol=0):
                    result.append((file_id, filename))

        return result

    def read_tags(self, node_id, name, repo_fs):
        to_add = []

        data = repo_fs.getbytes(name)
        img = Image.open(io.BytesIO(data))

        to_add.append((node_id, 0, 'width', 1, str(img.size[0])))
        to_add.append((node_id, 0, 'height', 1, str(img.size[1])))
        to_add.append((node_id, 0, 'format', 0, img.format))

        if img.info:
            for i, v in img.info.items():
                if i == "tags":
                    tag_list = v.split(",")
                    for tag in tag_list:
                        to_add.append((node_id, 1, 'tag', 0, tag.strip()))

        for reader in self.get_app().lookups("TagReader"):
            reader.read_file_tags(node_id, data, to_add)

        return to_add

    def search_tag(self, *args):
        if len(args) == 0:
            self.set_manager.load('*')
        else:
            query = self.search_manager.generate_search_query(*args)
            self.logger.debug(query)
            self.set_manager.query_to_current_set(query)

    def on_current_set_change(self):
        row = self.conn.execute(
            'select rowid, * from current_set where position=0 order by position limit 1').fetchone()
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
        self.set_manager.reenumerate()

    def cut_marked(self):
        self.session.cursor.cut_marked()

    def paste_marked(self, new_pos):
        self.session.cursor.paste_marked()


Factory.register('Cursor', module=SqliteCursor)
