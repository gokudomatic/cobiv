from modules.core.book.book_manager import BookManager


class SqliteBookManager(BookManager):
    conn = None

    def ready(self):
        super().ready()
        self.conn = self.lookup('sqlite_ds', 'Datasource').get_connection()

    def create_book(self, name):
        with self.conn:
            c = self.conn.execute(
                'insert into file(repo_key,name,searchable,file_type) values (?,?,?,?)', (0,name,1,'book'))
            last_id=c.lastrowid

            c.execute(
                'insert into set_detail (set_head_key,position,file_key) select ?,c.position,c.file_key from current_set c',
                (key,))

    def delete_book(self, book_id):
        super().delete_book(book_id)

    def open_book(self, book_id):
        super().open_book(book_id)
