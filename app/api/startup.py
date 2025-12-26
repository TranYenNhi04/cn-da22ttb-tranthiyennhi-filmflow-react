# app/api/startup.py
"""
Startup and shutdown events for FastAPI application
Handles database initialization and connection management
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import PostgreSQL database functions
from data.db_postgresql import init_db, close_db, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting FilmFlow API...")
    
    try:
        # Initialize PostgreSQL database
        print("📊 Initializing PostgreSQL database...")
        init_db()
        
        # Test connection
        from data.db_postgresql import get_db_session
        with get_db_session() as db:
            from data.models import Movie, Rating
            movie_count = db.query(Movie).count()
            rating_count = db.query(Rating).count()
            print(f"✅ PostgreSQL connected!")
            print(f"   📊 Movies: {movie_count}, Ratings: {rating_count}")
    
    except Exception as e:
        print(f"❌ PostgreSQL initialization failed: {e}")
        print("💡 Please run migration script: python scripts/migrate_sqlite_to_pg_fixed.py")
        raise
    
    print("✅ FilmFlow API ready!")
    
    yield  # Application runs here
    
    # Shutdown
    print("🛑 Shutting down FilmFlow API...")
    
    try:
        print("📊 Closing PostgreSQL connections...")
        close_db()
        print("✅ PostgreSQL connections closed")
    except Exception as e:
        print(f"⚠️  Error closing database: {e}")
    
    print("👋 FilmFlow API stopped")

def get_database_info():
    """Get information about current database configuration"""
    try:
        from data.db_postgresql import get_db_session
        from data.models import Movie, User, Rating
        with get_db_session() as db:
            return {
                "type": "PostgreSQL",
                "status": "connected",
                "movies": db.query(Movie).count(),
                "users": db.query(User).count(),
                "ratings": db.query(Rating).count()
            }
    except Exception as e:
        return {
            "type": "PostgreSQL",
            "status": "error",
            "error": str(e)
        }
