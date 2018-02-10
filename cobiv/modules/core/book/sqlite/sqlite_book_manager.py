from cobiv.modules.core.book.book_manager import BookManager
from cobiv.modules.core.entity import Entity


class SqliteBookManager(BookManager):
    conn = None
    set_manager = None

    def ready(self):
        super().ready()
        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()

        self.set_manager = self.lookup('sqliteSetManager', 'SetManager')

        self.set_action("create-book", self.create_book, "browser")
        session = self.get_session()
        session.register_mimetype_action("book", "open", self.open_book)
        session.register_mimetype_action("book", "delete", self.delete_book)

    def create_book(self, name):
        with self.conn:
            c = self.conn.execute(
                'insert into file(repo_key,name,searchable,file_type) values (?,?,?,?)', (0, name, 1, 'book'))
            last_id = c.lastrowid
            c.execute(
                'insert into file_map (parent_key,child_key,position) select ?,c.file_key,c.position from current_set c where c.position>=0',
                (last_id,))

            self.set_manager.add_to_set('*', last_id)
            return last_id

    def delete_book(self, book_id):
        with self.conn:
            c = self.conn.execute('delete from file_map where parent_key=?', (book_id,))
            c.execute('delete from file where id=?', (book_id,))
            c.execute('delete from set_detail where file_key=?', (book_id,))

    def open_book(self, book_id):
        with self.conn:
            c = self.conn.execute('drop table if exists current_set')
            c.execute(
                'create temporary table current_set as select 0 as set_head_key, position, child_key as file_key from file_map where parent_key=? order by position',
                (book_id,))
            c.execute('create index cs_index1 on current_set(file_key)')
