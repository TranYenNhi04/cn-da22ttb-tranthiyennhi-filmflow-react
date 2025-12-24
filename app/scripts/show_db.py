import sqlite3
import os

# Path relative to this script: ../data/app.db
db_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db'))
if not os.path.exists(db_path):
    print('DB not found at', db_path)
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print('--- REVIEWS (latest 20) ---')
for r in cur.execute("SELECT id,movieId,userId,rating,review,timestamp FROM reviews ORDER BY id DESC LIMIT 20"):
    print(r)

print('\n--- INTERACTIONS (latest 50) ---')
for r in cur.execute("SELECT id,userId,movieId,action,timestamp FROM interactions ORDER BY id DESC LIMIT 50"):
    print(r)

print('\n--- RATINGS (latest 20) ---')
for r in cur.execute("SELECT id,userId,movieId,rating,timestamp FROM ratings ORDER BY id DESC LIMIT 20"):
    print(r)

conn.close()
