import logging
from functools import partial

from kivy.clock import Clock

from cobiv.modules.core.sets.setmanager import SetManager


class SqliteSetManager(SetManager):
    logger = logging.getLogger(__name__)

    def ready(self):
        super().ready()

        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()

        session = self.get_session()
        session.set_action("set-add", self.save)
        session.set_action("set-load", self.load)
        session.set_action("set-rm", self.remove)
        session.set_action("set-mv", self.rename)
        session.set_action("set-append", self.add_to_current)
        session.set_action("set-substract", self.remove_from_current)

        view_context = session.get_context('sql')
        view_context.fn = self.replay_query
        view_context.args['current_set_query'] = None
        view_context.args['current_set_id'] = None

    def remove(self, id):
        with self.conn:
            c = self.conn.execute(
                'delete from set_detail where set_head_key = (select id from set_head where name=?)', (id,))
            c.execute('delete from set_head where name=?', (id,))

    def save(self, id):
        with self.conn:
            c = self.conn.execute(
                'delete from set_detail where set_head_key = (select id from set_head where name=?)', (id,))
            c.execute(
                'insert into set_head (name,readonly) select ?,? where not exists(select 1 from set_head where name=?)',
                (id, '0', id))
            row = c.execute('select id from set_head where name=?', (id,)).fetchone()
            key = row[0]
            c.execute(
                'insert into set_detail (set_head_key,position,file_key) select ?,c.position,c.file_key from current_set c',
                (key,))

    def add_to_set(self, set_head_name, file_id):
        with self.conn:
            row = self.conn.execute('select id from set_head where name=?', (set_head_name,)).fetchone()
            if row is not None:
                head_key = row[0]
                self.conn.execute(
                    'insert into set_detail (set_head_key,position,file_key) select ?,max(position)+1 as position,? from set_detail where set_head_key=?',
                    (head_key, file_id, head_key))

    def rename(self, id, new_id):
        with self.conn:
            self.conn.execute('update set_head set name=? where name=?', (new_id, id))

    def add_to_current(self, id):
        with self.conn:
            self.conn.execute(
                'insert into current_set select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? and not exists(select 1 from current_set c1 where c1.file_key=d.file_key)',
                (id,)
            )
        self.reenumerate()

        self.get_app().fire_event("on_current_set_change")

    def remove_from_current(self, id):
        with self.conn:
            self.conn.execute(
                'delete from current_set where file_key in (select file_key from set_detail d, set_head h where d.set_head_key=h.id and h.name=?)',
                (id,))
        self.reenumerate()

        self.get_app().fire_event("on_current_set_change")

    def reenumerate(self):
        with self.conn:
            self.conn.execute(
                'create temporary table renum as select rowid fkey from current_set where position>=0 order by position')
            self.conn.execute('create unique index renum_idx on renum(fkey)')  # improve performance
            self.conn.execute(
                'update current_set set position=(select r.rowid-1 from renum r where r.fkey=current_set.rowid) where exists (select * from renum where renum.fkey=current_set.rowid)')
            self.conn.execute('drop table renum')

    def get_list(self):
        with self.conn:
            rows = self.conn.execute('select name from set_head where not name="*"').fetchall()
            return [r[0] for r in rows]

    def regenerate_default(self):
        with self.conn:
            c = self.conn.cursor()

            row = c.execute('select id from set_head where name="*"').fetchone()
            if row is not None:
                head_key = row[0]
                c.execute('delete from set_detail where set_head_key=?', (head_key,))
            else:
                c.execute('insert into set_head (name, readonly) values ("*","0")')
                head_key = c.lastrowid

            c.execute("create temporary table map_filekey_pos as select id from file")
            c.execute(
                "insert into set_detail (set_head_key,position,file_key) select ?,rowid-1,id from map_filekey_pos",
                (head_key,))
            c.execute("drop table map_filekey_pos")

    def query_to_current_set(self, query):
        view_context = self.get_session().get_context('sql')
        if view_context.args['current_set_query'] is not None or view_context.args['current_set_id'] is not None:
            view_context.args['current_id'] = self.get_session().cursor.file_id
            self.get_session().push_context('sql')
        view_context.args['current_set_query'] = query
        view_context.args['current_set_id'] = None

        c = self.conn.cursor()

        c.execute("create temporary table map_filekey_pos as " + query)

        c.execute('drop table if exists current_set')
        c.execute(
            'create temporary table current_set as select 0 as set_head_key,rowid-1 as position,id as file_key from map_filekey_pos')
        c.execute('create index cs_index1 on current_set(file_key)')

        c.execute("drop table map_filekey_pos")

        self.get_app().fire_event("on_current_set_change")

    def load(self, id):
        view_context = self.get_session().get_context('sql')
        if view_context.args['current_set_query'] is not None or view_context.args['current_set_id'] is not None:
            view_context.args['current_id'] = self.get_session().cursor.file_id
            self.get_session().push_context('sql')
        view_context.args['current_set_query'] = None
        view_context.args['current_set_id'] = id

        with self.conn:
            c = self.conn.execute('drop table if exists current_set')
            c.execute(
                'create temporary table current_set as select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? order by d.position',
                (id,))
            c.execute('create index cs_index1 on current_set(file_key)')

        self.get_app().fire_event("on_current_set_change")

    def replay_query(self, current_set_query, current_set_id, current_id):
        if current_set_query is not None:
            self.query_to_current_set(query=current_set_query)
        elif current_set_id is not None:
            self.load(id=current_set_id)
        else:
            self.logger.error("current_set_query and current_set_id should not be both None!")

        # if current_id is not None:
        #     Clock.schedule_once(lambda dt: self.get_session().cursor.go(idx=current_id, force=True), 0.1)
            # self.get_session().cursor.go(current_id, force=True)

    def test(self):
        with self.conn:
            c = self.conn.cursor()
            c.execute('drop table if exists current_set')
            c.execute("create temporary table current_set as select id from file where rowid between 50 and 149")
