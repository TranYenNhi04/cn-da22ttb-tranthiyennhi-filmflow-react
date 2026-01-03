"""
Migration script to add password_hash column to users table
Run this script to update existing database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from data.db_postgresql import engine, init_db

def add_password_column():
    """Add password_hash column to users table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password_hash'
            """))
            
            if result.fetchone() is None:
                print("Adding password_hash column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN password_hash VARCHAR(255)
                """))
                conn.commit()
                print("✅ Successfully added password_hash column!")
            else:
                print("ℹ️  password_hash column already exists")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    print("=" * 50)
    print("Database Migration: Add Password Column")
    print("=" * 50)
    add_password_column()
    print("\n✅ Migration completed!")
