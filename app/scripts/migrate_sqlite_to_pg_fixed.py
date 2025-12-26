"""
Migration script to transfer data from SQLite to PostgreSQL with proper user ID mapping
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import data.database as sqlite_db
from data.db_postgresql import get_db_session, init_db
from data.models import User, Rating, Review, Watchlist, WatchHistory
from datetime import datetime

def init_database():
    """Initialize PostgreSQL database and create tables"""
    try:
        init_db()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

def migrate_users():
    """
    Migrate users and return a mapping of old user_ids to new user_ids
    Returns: dict mapping str(old_id) -> str(user_id)
    """
    print("\n📦 Migrating users...")
    
    # Get users from SQLite
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, created_at, metadata FROM users")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No users found in SQLite")
            return {}
        
        user_id_map = {}
        
        with get_db_session() as db:
            import json
            for row in rows:
                old_user_id, created_at, metadata = row
                old_user_id_str = str(old_user_id)
                
                # Parse metadata JSON
                user_data = {}
                if metadata:
                    try:
                        user_data = json.loads(metadata)
                    except:
                        pass
                
                # Use old_user_id as user_id in PostgreSQL
                user_id_pg = str(old_user_id)
                name = user_data.get('username', user_data.get('name', f'User {old_user_id}'))
                email = user_data.get('email')
                
                # Check if user already exists in PostgreSQL
                existing = db.query(User).filter(User.user_id == user_id_pg).first()
                
                if existing:
                    user_id_map[old_user_id_str] = existing.user_id
                    continue
                
                # Create new user in PostgreSQL
                new_user = User(
                    user_id=user_id_pg,
                    name=name,
                    email=email
                )
                
                if created_at:
                    try:
                        new_user.created_at = datetime.fromisoformat(created_at)
                    except:
                        pass
                
                db.add(new_user)
                db.flush()  # Ensure it's saved
                
                user_id_map[old_user_id_str] = user_id_pg
            
            db.commit()
        
        print(f"✅ Migrated {len(rows)} users")
        print(f"   User ID mapping: {len(user_id_map)} entries")
        return user_id_map
        
    finally:
        conn.close()

def migrate_ratings(user_id_map):
    """
    Note: Ratings in SQLite mostly come from CSV data with numeric user IDs (1.0, 2.0, etc.)
    These are different from registered users (user_xxxxx_xxxxx).
    We skip migrating these CSV-based ratings since they will be loaded from CSV.
    Only migrate ratings from registered users.
    """
    print("\n📦 Migrating ratings...")
    
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, rating, timestamp FROM ratings")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No ratings found in SQLite")
            return
        
        migrated = 0
        skipped_csv = 0
        skipped_existing = 0
        
        with get_db_session() as db:
            for row in rows:
                old_user_id, movie_id, rating, timestamp = row
                old_user_id_str = str(old_user_id)
                
                # Check if this is a CSV-based rating (numeric user ID like "1.0", "2.0")
                # vs registered user (like "user_1766672896023_xfi32t5")
                if old_user_id_str.replace('.', '').replace('0', '').isdigit() or old_user_id_str.endswith('.0'):
                    # This is from CSV, skip it (will be loaded from CSV in init_db)
                    skipped_csv += 1
                    continue
                
                # Map old user ID to PostgreSQL user_id
                if old_user_id_str not in user_id_map:
                    # User not found, skip
                    continue
                
                pg_user_id = user_id_map[old_user_id_str]
                
                # Check if rating already exists
                existing = db.query(Rating).filter(
                    Rating.user_id == pg_user_id,
                    Rating.movie_id == str(movie_id)
                ).first()
                
                if existing:
                    skipped_existing += 1
                    continue
                
                # Create new rating
                rating_obj = Rating(
                    user_id=pg_user_id,
                    movie_id=str(movie_id),
                    rating=float(rating)
                )
                
                if timestamp:
                    try:
                        rating_obj.timestamp = datetime.fromisoformat(timestamp)
                    except:
                        pass
                
                db.add(rating_obj)
                migrated += 1
            
            db.commit()
        
        print(f"✅ Migrated {migrated} ratings from registered users")
        print(f"   (Skipped {skipped_csv} CSV-based ratings, {skipped_existing} existing)")
        
    finally:
        conn.close()

def migrate_reviews(user_id_map):
    """Migrate reviews with proper user ID mapping"""
    print("\n📦 Migrating reviews...")
    
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, review, rating, timestamp FROM reviews")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No reviews found in SQLite")
            return
        
        migrated = 0
        skipped = 0
        errors = 0
        
        with get_db_session() as db:
            for row in rows:
                old_user_id, movie_id, review_text, rating, timestamp = row
                old_user_id_str = str(old_user_id)
                
                # Map old user ID to PostgreSQL user_id
                if old_user_id_str not in user_id_map:
                    errors += 1
                    continue
                
                pg_user_id = user_id_map[old_user_id_str]
                
                # Check if review already exists
                existing = db.query(Review).filter(
                    Review.user_id == pg_user_id,
                    Review.movie_id == str(movie_id)
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create new review
                review_obj = Review(
                    user_id=pg_user_id,
                    movie_id=str(movie_id),
                    review_text=review_text,
                    rating=float(rating) if rating else None
                )
                
                if timestamp:
                    try:
                        review_obj.created_at = datetime.fromisoformat(timestamp)
                    except:
                        pass
                
                db.add(review_obj)
                migrated += 1
            
            db.commit()
        
        print(f"✅ Migrated {migrated} reviews (skipped {skipped}, errors {errors})")
        
    finally:
        conn.close()

def migrate_watchlist(user_id_map):
    """Migrate watchlist with proper user ID mapping"""
    print("\n📦 Migrating watchlist...")
    
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, added_at FROM watchlist")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No watchlist items found in SQLite")
            return
        
        migrated = 0
        skipped = 0
        errors = 0
        
        with get_db_session() as db:
            for row in rows:
                old_user_id, movie_id, added_at = row
                old_user_id_str = str(old_user_id)
                
                # Map old user ID to new user ID
                if old_user_id_str not in user_id_map:
                    errors += 1
                    continue
                
                pg_user_id = user_id_map[old_user_id_str]
                
                # Check if already exists
                existing = db.query(Watchlist).filter(
                    Watchlist.user_id == pg_user_id,
                    Watchlist.movie_id == str(movie_id)
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create new watchlist item
                watchlist_obj = Watchlist(
                    user_id=pg_user_id,
                    movie_id=str(movie_id)
                )
                
                if added_at:
                    try:
                        watchlist_obj.added_at = datetime.fromisoformat(added_at)
                    except:
                        pass
                
                db.add(watchlist_obj)
                migrated += 1
            
            db.commit()
        
        print(f"✅ Migrated {migrated} watchlist items (skipped {skipped}, errors {errors})")
        
    finally:
        conn.close()

def migrate_watch_history(user_id_map):
    """Migrate watch history with proper user ID mapping"""
    print("\n📦 Migrating watch history...")
    
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT userId, movieId, viewed_at FROM watch_history")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No watch history found in SQLite")
            return
        
        migrated = 0
        skipped = 0
        errors = 0
        
        with get_db_session() as db:
            for row in rows:
                old_user_id, movie_id, watched_at = row
                old_user_id_str = str(old_user_id)
                
                # Map old user ID to new user ID
                if old_user_id_str not in user_id_map:
                    errors += 1
                    continue
                
                pg_user_id = user_id_map[old_user_id_str]
                
                # Check if already exists
                existing = db.query(WatchHistory).filter(
                    WatchHistory.user_id == pg_user_id,
                    WatchHistory.movie_id == str(movie_id)
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create new watch history item
                history_obj = WatchHistory(
                    user_id=pg_user_id,
                    movie_id=str(movie_id)
                )
                
                if watched_at:
                    try:
                        history_obj.watched_at = datetime.fromisoformat(watched_at)
                    except:
                        pass
                
                db.add(history_obj)
                migrated += 1
            
            db.commit()
        
        print(f"✅ Migrated {migrated} watch history items (skipped {skipped}, errors {errors})")
        
    finally:
        conn.close()

def verify_migration():
    """Verify migration results"""
    print("\n🔍 Verifying migration...")
    
    # Count records in SQLite
    conn = sqlite_db.get_connection()
    cur = conn.cursor()
    
    sqlite_counts = {}
    cur.execute("SELECT COUNT(*) FROM users")
    sqlite_counts['users'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM ratings")
    sqlite_counts['ratings'] = cur.fetchone()[0]
    
    try:
        cur.execute("SELECT COUNT(*) FROM reviews")
        sqlite_counts['reviews'] = cur.fetchone()[0]
    except:
        sqlite_counts['reviews'] = 0
    
    try:
        cur.execute("SELECT COUNT(*) FROM watchlist")
        sqlite_counts['watchlist'] = cur.fetchone()[0]
    except:
        sqlite_counts['watchlist'] = 0
    
    try:
        cur.execute("SELECT COUNT(*) FROM watch_history")
        sqlite_counts['watch_history'] = cur.fetchone()[0]
    except:
        sqlite_counts['watch_history'] = 0
    
    conn.close()
    
    # Count records in PostgreSQL
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
    """Run all migrations"""
    print("=" * 80)
    print("🔄 SQLite to PostgreSQL Migration (Fixed)")
    print("=" * 80)
    
    try:
        # Initialize PostgreSQL
        print("\n🔧 Initializing PostgreSQL database...")
        init_database()
        
        # Migrate in order, passing user_id_map to dependent migrations
        user_id_map = migrate_users()
        migrate_ratings(user_id_map)
        migrate_reviews(user_id_map)
        migrate_watchlist(user_id_map)
        migrate_watch_history(user_id_map)
        
        # Verify
        verify_migration()
        
        print("\n" + "=" * 80)
        print("✅ Migration completed successfully!")
        print("=" * 80)
        print("\n⚠️  Next steps:")
        print("1. Verify data in PostgreSQL")
        print("2. Update code to remove SQLite dependencies")
        print("3. Restart backend: docker-compose restart backend")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
