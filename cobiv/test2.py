import sqlite3

def querying(conn):
    with conn:
        conn.execute('drop table if exists b')
        conn.execute('create table b as select * from a')

conn = sqlite3.connect(':memory:')
with conn:
    conn.execute('create table a (f1 int)')
    conn.executemany('insert into a (f1) values (?)', [(i,) for i in range(2)])

    for i in range(5):
        c = conn.cursor()
        querying(conn)
        print(c.execute('select * from b').fetchone()[0])
