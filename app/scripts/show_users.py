import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
db_path = os.path.normpath(db_path)
if not os.path.exists(db_path):
    print('DB not found at', db_path)
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    cur.execute('SELECT COUNT(1) FROM users')
    count = cur.fetchone()[0]
    print('users_count:', count)
    cur.execute('SELECT id,created_at,metadata FROM users LIMIT 10')
    for row in cur.fetchall():
        print(row)
finally:
    conn.close()
