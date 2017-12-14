from modules.core.sets.setmanager import SetManager


class SqliteSetManager(SetManager):
    def __init__(self) -> None:
        super().__init__()
        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()

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

    def rename(self, id, new_id):
        with self.conn:
            self.conn.execute('update set_head set name=? where name=?', (new_id, id))

    def load(self, id):
        with self.conn:
            c = self.conn.execute('drop table if exists current_set')
            c.execute(
                'create temporary table current_set as select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? order by d.position',
                (id,))
            c.execute('create index cs_index1 on current_set(file_key)')

    def add_to_current(self, id):
        with self.conn:
            self.conn.execute(
                'insert into current_set select d.* from set_detail d,set_head h where d.set_head_key=h.id and h.name=? and not exists(select 1 from current_set c1 where c1.file_key=d.file_key)',
                (id,)
            )

    def remove_from_current(self, id):
        with self.conn:
            self.conn.execute(
                'delete from current_set where file_key in (select file_key from set_detail d, set_head h where d.set_head_key=h.id and h.name=?)',
                (id,))


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
                "insert into set_detail (set_head_key,position,file_key) select ?,rowid,id from map_filekey_pos",
                (head_key,))
            c.execute("drop table map_filekey_pos")

    def query_to_current_set(self, query):
        with self.conn:
            c = self.conn.cursor()

            c.execute("create temporary table map_filekey_pos as " + query)

            c.execute('drop table if exists current_set')
            c.execute(
                'create temporary table current_set as select 0 as set_head_key,rowid as position,id as file_key from map_filekey_pos')
            c.execute('create index cs_index1 on current_set(file_key)')

            c.execute("drop table map_filekey_pos")
