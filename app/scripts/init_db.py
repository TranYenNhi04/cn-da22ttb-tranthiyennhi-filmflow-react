"""Script to initialize the SQLite DB and print basic verification info.

Usage:
  python app/scripts/init_db.py
"""
import os
import sys

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from app.data import database


def main():
    data_dir = os.path.join(ROOT, 'app', 'data')
    print(f"Initializing DB in: {data_dir}")
    conn = None
    try:
        conn = database.init_db(data_dir)
        cur = conn.cursor()

        # List tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", tables)

        # Print row counts for core tables
        for t in ['ratings', 'reviews', 'interactions']:
            try:
                cur.execute(f"SELECT COUNT(1) FROM {t}")
                count = cur.fetchone()[0]
            except Exception:
                count = 'N/A'
            print(f"  - {t}: {count}")

        print("DB initialization complete.")
    except Exception as e:
        print(f"Error during DB init: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
