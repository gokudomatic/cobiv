from cobiv.modules.core.entity import Entity
from cobiv.modules.database.backup.db_backup import JsonBackupBody, DbBackup


class SqlitedbBackup(Entity, DbBackup):
    limit = 1000

    def get_name(self=None):
        return 'sqlite_backup'

    def ready(self):
        super().ready()

        session = self.get_session()

        self.limit = int(self.get_config_value('limit', '1000'))

        # add actions
        session.set_action("dump-tags", self.dump)
        session.set_action("load-tags", self.load)

    def dump(self, path):
        body = JsonBackupBody()
        conn = self.lookup('sqlite_ds', 'Datasource').get_connection()
        with conn:
            c = conn.cursor()
            count = c.execute('select count(*) from current_set').fetchone()[0]
            for page in range((count // self.limit) + 1):
                rows = c.execute(
                    'select f.name,t.kind,t.value from file f,tag t,current_set c where c.file_key=f.id and t.file_key=c.file_key and t.category=1 and c.position>=0 order by t.file_key,t.kind limit ? offset ?',
                    (self.limit, page * self.limit)).fetchall()
                current_name = None
                tags = {}
                for name, kind, value in rows:
                    if name != current_name:
                        if current_name is not None:
                            body.files.append({'filename': current_name, 'tags': tags})
                        current_name = name
                    tags.setdefault(kind, []).append(value)
                if current_name is not None:
                    body.files.append({'filename': current_name, 'tags': tags})
        if len(body.files) > 0:
            self.dump_json(path, body)

    def load(self, path):
        body = self.load_json(path)
        if body is not None:
            conn = self.lookup('sqlite_ds', 'Datasource').get_connection()
            with conn:
                c = conn.cursor()
                tags_to_add = []
                files=body['files']
                for file in files:
                    filename = file['filename']
                    tags = file['tags']
                    row = c.execute('select id from file where name=?', (filename,)).fetchone()
                    if row is not None:
                        file_key = row[0]
                        c.execute('delete from tag where file_key=? and category=1',(file_key,))
                        for key, values in tags.items():
                            for value in values:
                                tags_to_add.append((file_key, 1, key, 0, value))

                c.executemany('insert or ignore into tag values (?,?,?,?,?)',
                              tags_to_add)
