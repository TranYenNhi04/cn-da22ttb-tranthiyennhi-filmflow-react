# app/scripts/migrate_to_postgresql.py
"""
Script to migrate data from CSV files to PostgreSQL database
Run this after starting PostgreSQL container
"""
import sys
import os
import pandas as pd
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_postgresql import engine, init_db, get_db_session
from data.models import Movie, Rating, Review, User

def migrate_movies(data_dir: str):
    """Migrate movies from CSV to PostgreSQL"""
    csv_path = os.path.join(data_dir, 'movies_processed.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Movies CSV not found: {csv_path}")
        return
    
    print(f"📂 Loading movies from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"✅ Loaded {len(df)} movies")
    
    with get_db_session() as db:
        # Check if movies already exist
        existing_count = db.query(Movie).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} movies. Skipping migration.")
            print("   Delete movies table first if you want to re-migrate.")
            return
        
        batch_size = 1000
        total_inserted = 0
        
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            movies_to_insert = []
            
            for _, row in batch.iterrows():
                try:
                    # Parse genres
                    genres = []
                    if pd.notna(row.get('genres')):
                        try:
                            genres = json.loads(row['genres'])
                        except:
                            genres = str(row['genres']).split(',')
                    
                    # Parse cast
                    cast_data = None
                    if pd.notna(row.get('cast')):
                        try:
                            cast_data = json.loads(row['cast'])
                        except:
                            pass
                    
                    # Extract year from release_date
                    year = None
                    if pd.notna(row.get('release_date')):
                        try:
                            year = int(str(row['release_date'])[:4])
                        except:
                            pass
                    if not year and pd.notna(row.get('year')):
                        try:
                            year = int(row['year'])
                        except:
                            pass
                    
                    # Generate TMDB poster URL if not available
                    poster_url = row.get('poster_url')
                    poster_path = row.get('poster_path')
                    if not poster_url and not poster_path:
                        # Use TMDB poster URL pattern with movie ID
                        # Most TMDB posters are at: https://image.tmdb.org/t/p/w500/{movie_id}.jpg
                        # But we'll use a placeholder that can be updated later
                        poster_url = f"https://image.tmdb.org/t/p/w500/movie_{row['id']}.jpg"
                    
                    movie = Movie(
                        movie_id=str(row['id']),
                        title=row.get('title', 'Unknown'),
                        original_title=row.get('original_title'),
                        overview=row.get('overview'),
                        tagline=row.get('tagline'),
                        genres=genres,
                        keywords=row.get('keywords'),
                        cast_data=cast_data,
                        director=row.get('director'),
                        poster_url=poster_url,
                        poster_path=poster_path,
                        backdrop_path=row.get('backdrop_path'),
                        release_date=str(row.get('release_date')) if pd.notna(row.get('release_date')) else None,
                        year=year,
                        runtime=int(row['runtime']) if pd.notna(row.get('runtime')) else None,
                        budget=float(row['budget']) if pd.notna(row.get('budget')) else None,
                        revenue=float(row['revenue']) if pd.notna(row.get('revenue')) else None,
                        vote_average=float(row['vote_average']) if pd.notna(row.get('vote_average')) else None,
                        vote_count=int(row['vote_count']) if pd.notna(row.get('vote_count')) else None,
                        popularity=float(row['popularity']) if pd.notna(row.get('popularity')) else None,
                        status=row.get('status'),
                        original_language=row.get('original_language')
                    )
                    movies_to_insert.append(movie)
                
                except Exception as e:
                    print(f"⚠️  Error processing movie {row.get('id', 'unknown')}: {e}")
                    continue
            
            # Bulk insert
            if movies_to_insert:
                db.bulk_save_objects(movies_to_insert)
                db.commit()
                total_inserted += len(movies_to_insert)
                print(f"✅ Inserted {total_inserted}/{len(df)} movies...")
        
        print(f"🎉 Successfully migrated {total_inserted} movies!")

def migrate_ratings(data_dir: str):
    """Migrate ratings from CSV to PostgreSQL"""
    csv_path = os.path.join(data_dir, 'ratings_processed.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Ratings CSV not found: {csv_path}")
        return
    
    print(f"📂 Loading ratings from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"✅ Loaded {len(df)} ratings")
    
    with get_db_session() as db:
        # Check if ratings already exist
        existing_count = db.query(Rating).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} ratings. Skipping migration.")
            return
        
        batch_size = 5000
        total_inserted = 0
        
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            ratings_to_insert = []
            
            for _, row in batch.iterrows():
                try:
                    # Convert to int first to remove decimal, then to string
                    user_id = str(int(float(row['userId'])))
                    movie_id = str(int(float(row['movieId'])))
                    
                    rating = Rating(
                        user_id=user_id,
                        movie_id=movie_id,
                        rating=float(row['rating']),
                        timestamp=datetime.fromtimestamp(int(row['timestamp'])) if pd.notna(row.get('timestamp')) else datetime.utcnow()
                    )
                    ratings_to_insert.append(rating)
                
                except Exception as e:
                    print(f"⚠️  Error processing rating: {e}")
                    continue
            
            # Bulk insert
            if ratings_to_insert:
                db.bulk_save_objects(ratings_to_insert)
                db.commit()
                total_inserted += len(ratings_to_insert)
                print(f"✅ Inserted {total_inserted}/{len(df)} ratings...")
        
        print(f"🎉 Successfully migrated {total_inserted} ratings!")

def migrate_reviews(data_dir: str):
    """Migrate reviews from CSV to PostgreSQL"""
    csv_path = os.path.join(data_dir, 'reviews.csv')
    
    if not os.path.exists(csv_path):
        print(f"⚠️  Reviews CSV not found: {csv_path} (skipping)")
        return
    
    print(f"📂 Loading reviews from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"✅ Loaded {len(df)} reviews")
    
    with get_db_session() as db:
        # Check if reviews already exist
        existing_count = db.query(Review).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} reviews. Skipping migration.")
            return
        
        batch_size = 1000
        total_inserted = 0
        
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            reviews_to_insert = []
            
            for _, row in batch.iterrows():
                try:
                    review = Review(
                        movie_id=str(int(float(row['movieId']))),
                        user_id=str(int(float(row['userId']))),
                        username=row.get('username', 'Anonymous'),
                        rating=int(row['rating']),
                        review_text=row.get('review', ''),
                        timestamp=datetime.fromisoformat(row['timestamp']) if pd.notna(row.get('timestamp')) else datetime.utcnow()
                    )
                    reviews_to_insert.append(review)
                
                except Exception as e:
                    print(f"⚠️  Error processing review: {e}")
                    continue
            
            # Bulk insert
            if reviews_to_insert:
                db.bulk_save_objects(reviews_to_insert)
                db.commit()
                total_inserted += len(reviews_to_insert)
                print(f"✅ Inserted {total_inserted}/{len(df)} reviews...")
        
        print(f"🎉 Successfully migrated {total_inserted} reviews!")

def create_sample_users(data_dir: str):
    """Create sample users from existing ratings"""
    print("👥 Creating users from ratings...")
    
    # Read unique user IDs from ratings CSV
    ratings_csv = os.path.join(data_dir, 'ratings_processed.csv')
    if not os.path.exists(ratings_csv):
        print("⚠️  Ratings file not found, skipping user creation")
        return
    
    df = pd.read_csv(ratings_csv)
    # Convert to int to remove decimals
    unique_user_ids = [str(int(float(uid))) for uid in df['userId'].unique()]
    
    with get_db_session() as db:
        users_to_create = []
        for user_id in unique_user_ids:
            # Check if user exists
            existing = db.query(User).filter(User.user_id == user_id).first()
            if not existing:
                user = User(
                    user_id=user_id,
                    name=f"User {user_id}",
                    email=f"user{user_id}@filmflow.com"
                )
                users_to_create.append(user)
        
        if users_to_create:
            db.bulk_save_objects(users_to_create)
            db.commit()
            print(f"✅ Created {len(users_to_create)} users")
        else:
            print("✅ All users already exist")

def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 FilmFlow Data Migration: CSV → PostgreSQL")
    print("=" * 60)
    
    # Get data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    try:
        # Initialize database (create tables)
        print("\n1️⃣  Initializing database schema...")
        init_db()
        
        # Migrate movies
        print("\n2️⃣  Migrating movies...")
        migrate_movies(data_dir)
        
        # Create users from ratings FIRST (before ratings migration)
        print("\n3️⃣  Creating users...")
        create_sample_users(data_dir)
        
        # Migrate ratings (requires users to exist)
        print("\n4️⃣  Migrating ratings...")
        migrate_ratings(data_dir)
        
        # Migrate reviews
        print("\n5️⃣  Migrating reviews...")
        migrate_reviews(data_dir)
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
        # Print statistics
        with get_db_session() as db:
            movie_count = db.query(Movie).count()
            user_count = db.query(User).count()
            rating_count = db.query(Rating).count()
            review_count = db.query(Review).count()
            
            print(f"\n📊 Database Statistics:")
            print(f"   Movies:  {movie_count:,}")
            print(f"   Users:   {user_count:,}")
            print(f"   Ratings: {rating_count:,}")
            print(f"   Reviews: {review_count:,}")
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
