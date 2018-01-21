import sqlite3

from cobiv.modules.database.datasources.datasource import Datasource


class Sqliteds(Datasource):
    def build_yaml_config(self, config):
        config[self.get_name()] = {'url': self.get_app().get_user_path('cobiv.db')}

    def create_connection(self):
        url = self.get_config_value('url', ':memory:')
        conn = sqlite3.connect(url, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        c=conn.execute('PRAGMA cache_spill = off')
        c.execute('PRAGMA temp_store = MEMORY')
        c.execute('PRAGMA synchronous = NORMAL')
        c.execute('PRAGMA journal_mode = wal')
        c.execute('PRAGMA locking_mode = EXCLUSIVE')
        return conn

    def get_name(self):
        return "sqlite"
