#!/usr/bin/env python3
"""
Script để migrate toàn bộ dữ liệu từ SQLite sang PostgreSQL
Chạy: python migrate_sqlite_to_postgresql.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import database as sqlite_db
from data.db_postgresql import get_db_session, init_db
from data.models import User, Rating, Review, Watchlist, WatchHistory
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

def migrate_users():
    """Migrate users table"""
    print("\n📦 Migrating users...")
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, created_at, metadata FROM users")
        rows = cur.fetchall()
        
        with get_db_session() as db:
            migrated = 0
            for row in rows:
                user_id, created_at, metadata_str = row
                
                # Parse metadata
                name = None
                email = None
                if metadata_str:
                    try:
                        metadata = json.loads(metadata_str)
                        name = metadata.get('name') or metadata.get('displayName')
                        email = metadata.get('email')
                    except:
                        pass
                
                # Create or update user
                existing = db.query(User).filter(User.user_id == user_id).first()
                if not existing:
                    user = User(
                        user_id=user_id,
                        name=name,
                        email=email
                    )
                    if created_at:
                        try:
                            user.created_at = datetime.fromisoformat(created_at)
                        except:
                            pass
                    db.add(user)
                    migrated += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} users")
    finally:
        conn.close()

def migrate_ratings():
    """Migrate ratings table"""
    print("\n📦 Migrating ratings...")
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, rating, timestamp FROM ratings")
        rows = cur.fetchall()
        
        with get_db_session() as db:
            migrated = 0
            skipped = 0
            
            for row in rows:
                user_id, movie_id, rating, timestamp = row
                
                # Check if already exists
                existing = db.query(Rating).filter(
                    Rating.user_id == user_id,
                    Rating.movie_id == str(movie_id)
                ).first()
                
                if not existing:
                    rating_obj = Rating(
                        user_id=user_id,
                        movie_id=str(movie_id),
                        rating=rating
                    )
                    if timestamp:
                        try:
                            rating_obj.timestamp = datetime.fromisoformat(timestamp)
                        except:
                            pass
                    db.add(rating_obj)
                    migrated += 1
                else:
                    skipped += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} ratings (skipped {skipped} existing)")
    finally:
        conn.close()

def migrate_reviews():
    """Migrate reviews table"""
    print("\n📦 Migrating reviews...")
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT movieId, userId, rating, review, timestamp FROM reviews")
        rows = cur.fetchall()
        
        with get_db_session() as db:
            migrated = 0
            
            for row in rows:
                movie_id, user_id, rating, review_text, timestamp = row
                
                review_obj = Review(
                    movie_id=str(movie_id),
                    user_id=user_id,
                    username=user_id,  # Use user_id as username if not specified
                    rating=int(rating) if rating else 5,
                    review_text=review_text or ""
                )
                if timestamp:
                    try:
                        review_obj.timestamp = datetime.fromisoformat(timestamp)
                    except:
                        pass
                db.add(review_obj)
                migrated += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} reviews")
    finally:
        conn.close()

def migrate_watchlist():
    """Migrate watchlist table"""
    print("\n📦 Migrating watchlist...")
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, added_at FROM watchlist")
        rows = cur.fetchall()
        
        with get_db_session() as db:
            migrated = 0
            skipped = 0
            
            for row in rows:
                user_id, movie_id, added_at = row
                
                # Check if already exists
                existing = db.query(Watchlist).filter(
                    Watchlist.user_id == user_id,
                    Watchlist.movie_id == str(movie_id)
                ).first()
                
                if not existing:
                    watchlist_obj = Watchlist(
                        user_id=user_id,
                        movie_id=str(movie_id)
                    )
                    if added_at:
                        try:
                            watchlist_obj.added_at = datetime.fromisoformat(added_at)
                        except:
                            pass
                    db.add(watchlist_obj)
                    migrated += 1
                else:
                    skipped += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} watchlist items (skipped {skipped} existing)")
    finally:
        conn.close()

def migrate_watch_history():
    """Migrate watch_history table"""
    print("\n📦 Migrating watch history...")
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, timestamp_watched, duration, viewed_at FROM watch_history")
        rows = cur.fetchall()
        
        with get_db_session() as db:
            migrated = 0
            
            for row in rows:
                user_id, movie_id, timestamp_watched, duration, viewed_at = row
                
                # Calculate progress (if duration available)
                progress = 0.0
                if timestamp_watched and duration and duration > 0:
                    progress = min(timestamp_watched / duration, 1.0)
                
                history_obj = WatchHistory(
                    user_id=user_id,
                    movie_id=str(movie_id),
                    progress=progress,
                    completed=(progress >= 0.9)  # Consider 90%+ as completed
                )
                if viewed_at:
                    try:
                        history_obj.watched_at = datetime.fromisoformat(viewed_at)
                    except:
                        pass
                db.add(history_obj)
                migrated += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} watch history records")
    finally:
        conn.close()

def verify_migration():
    """Verify migration counts"""
    print("\n📊 Verifying migration...")
    
    # SQLite counts
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    sqlite_counts = {}
    
    for table in ['users', 'ratings', 'reviews', 'watchlist', 'watch_history']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_counts[table] = cur.fetchone()[0]
    
    conn.close()
    
    # PostgreSQL counts
    with get_db_session() as db:
        pg_counts = {
            'users': db.query(User).count(),
            'ratings': db.query(Rating).count(),
            'reviews': db.query(Review).count(),
            'watchlist': db.query(Watchlist).count(),
            'watch_history': db.query(WatchHistory).count()
        }
    
    print("\n📈 Migration Summary:")
    print(f"{'Table':<20} {'SQLite':<10} {'PostgreSQL':<10} {'Status'}")
    print("-" * 60)
    
    for table in sqlite_counts:
        sqlite_count = sqlite_counts[table]
        pg_count = pg_counts[table]
        status = "✅" if pg_count >= sqlite_count else "⚠️"
        print(f"{table:<20} {sqlite_count:<10} {pg_count:<10} {status}")

def main():
    print("=" * 80)
    print("🔄 SQLite to PostgreSQL Migration")
    print("=" * 80)
    
    # Initialize PostgreSQL database
    print("\n🔧 Initializing PostgreSQL database...")
    init_db()
    
    # Migrate each table
    try:
        migrate_users()
        migrate_ratings()
        migrate_reviews()
        migrate_watchlist()
        migrate_watch_history()
        
        # Verify
        verify_migration()
        
        print("\n" + "=" * 80)
        print("✅ Migration completed successfully!")
        print("=" * 80)
        print("\n⚠️  Next steps:")
        print("1. Verify data in PostgreSQL")
        print("2. Backup SQLite database: app/data/app.db")
        print("3. Update code to remove SQLite dependencies")
        print("4. Restart backend: docker-compose restart backend")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
