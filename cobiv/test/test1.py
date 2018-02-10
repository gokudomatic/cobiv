from cobiv.modules.core.session.cursor import CursorInterface
from cobiv.modules.database.sqlitedb.sqlitedb import SqliteCursor

print(issubclass(SqliteCursor, CursorInterface))
