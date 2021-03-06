from cobiv.modules.core.book.book_manager import BookManager


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
        query="select child_key as id from file_map where parent_key="+str(book_id)+" order by position"
        self.set_manager.query_to_current_set(query)

    def get_list_detail(self,book_id):
        result=[]
        with self.conn:
            c=self.conn.execute('select child_key,name,position from file_map inner join file on id=child_key where parent_key=? order by position',(book_id,))
            result=[(r[0],r[1],r[2]) for r in c.fetchall()]
        return result