import os, sqlite3

conn = sqlite3.connect('jeopardy.db')
cursor = conn.cursor()

cursor.execute('CREATE TABLE CreatedPosts(postId TEXT, questionId TEXT, ts INTEGER)')
cursor.execute('CREATE TABLE Questions(id TEXT, question TEXT, answer TEXT, category TEXT, json TEXT)')
conn.commit()