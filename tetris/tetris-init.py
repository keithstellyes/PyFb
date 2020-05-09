import os, sqlite3

os.remove('tetris.db')
conn = sqlite3.connect('tetris.db')
cursor = conn.cursor()

cursor.execute('CREATE TABLE CreatedPosts(id TEXT, state BLOB, ts int)')
cursor.execute('CREATE TABLE Status(key TEXT, value TEXT)')
conn.commit()