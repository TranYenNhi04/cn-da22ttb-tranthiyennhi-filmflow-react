# app/api/startup.py
"""
Startup and shutdown events for FastAPI application
Handles database initialization and connection management
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import database functions
try:
    from data.db_postgresql import init_db, close_db, engine
    USE_POSTGRESQL = True
    print("✅ Using PostgreSQL database")
except Exception as e:
    print(f"⚠️  PostgreSQL not available: {e}")
    print("💡 Falling back to SQLite/CSV")
    from data import database
    USE_POSTGRESQL = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting FilmFlow API...")
    
    if USE_POSTGRESQL:
        try:
            # Initialize PostgreSQL database
            print("📊 Initializing PostgreSQL database...")
            init_db()
            
            # Test connection
            from data.db_postgresql import get_db_session
            with get_db_session() as db:
                from data.models import Movie
                count = db.query(Movie).count()
                print(f"✅ PostgreSQL connected! Movies in database: {count}")
        
        except Exception as e:
            print(f"❌ PostgreSQL initialization failed: {e}")
            print("💡 Please run migration script: python scripts/migrate_to_postgresql.py")
    else:
        # Initialize SQLite database
        print("📊 Initializing SQLite database...")
        try:
            from data import database
            database.init_db()
            print("✅ SQLite database initialized")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")
    
    print("✅ FilmFlow API ready!")
    
    yield  # Application runs here
    
    # Shutdown
    print("🛑 Shutting down FilmFlow API...")
    
    if USE_POSTGRESQL:
        try:
            print("📊 Closing PostgreSQL connections...")
            close_db()
            print("✅ PostgreSQL connections closed")
        except Exception as e:
            print(f"⚠️  Error closing database: {e}")
    
    print("👋 FilmFlow API stopped")

def get_database_info():
    """Get information about current database configuration"""
    if USE_POSTGRESQL:
        try:
            from data.db_postgresql import get_db_session, count_movies, count_users, count_ratings
            with get_db_session() as db:
                return {
                    "type": "PostgreSQL",
                    "status": "connected",
                    "movies": count_movies(db),
                    "users": count_users(db),
                    "ratings": count_ratings(db)
                }
        except Exception as e:
            return {
                "type": "PostgreSQL",
                "status": "error",
                "error": str(e)
            }
    else:
        return {
            "type": "SQLite/CSV",
            "status": "connected"
        }
