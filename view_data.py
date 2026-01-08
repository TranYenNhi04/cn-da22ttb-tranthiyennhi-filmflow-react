#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to view PostgreSQL database data"""

from app.data.db_postgresql import SessionLocal
from app.data.models import User, Rating, Review, WatchHistory, Watchlist, Movie

def main():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("📊 DATABASE OVERVIEW")
        print("=" * 80)
        
        # Users
        users = db.query(User).all()
        print(f"\n👥 USERS: {len(users)} total")
        print("-" * 80)
        for u in users[:10]:
            print(f"  • ID: {u.user_id:<20} | Name: {u.name:<20} | Email: {u.email}")
        
        # Movies
        movies_count = db.query(Movie).count()
        print(f"\n🎬 MOVIES: {movies_count} total")
        movies = db.query(Movie).limit(5).all()
        for m in movies:
            print(f"  • {m.title} ({m.year}) - Rating: {m.vote_average}/10")
        
        # Ratings
        ratings = db.query(Rating).order_by(Rating.timestamp.desc()).limit(10).all()
        ratings_count = db.query(Rating).count()
        print(f"\n⭐ RATINGS: {ratings_count} total (showing latest 10)")
        print("-" * 80)
        for r in ratings:
            print(f"  • User: {r.user_id:<20} | Movie: {r.movie_id:<10} | Rating: {r.rating} | Time: {r.timestamp}")
        
        # Reviews
        reviews = db.query(Review).order_by(Review.timestamp.desc()).limit(10).all()
        reviews_count = db.query(Review).count()
        print(f"\n💬 REVIEWS: {reviews_count} total (showing latest 10)")
        print("-" * 80)
        for r in reviews:
            text = (r.review_text[:50] + '...') if r.review_text and len(r.review_text) > 50 else (r.review_text or "No text")
            print(f"  • User: {r.user_id:<20} | Movie: {r.movie_id:<10} | Rating: {r.rating}/5")
            print(f"    Text: {text}")
        
        # Watch History
        history = db.query(WatchHistory).order_by(WatchHistory.watched_at.desc()).limit(10).all()
        history_count = db.query(WatchHistory).count()
        print(f"\n📺 WATCH HISTORY: {history_count} total (showing latest 10)")
        print("-" * 80)
        for h in history:
            print(f"  • User: {h.user_id:<20} | Movie: {h.movie_id:<10} | Progress: {h.progress:.1f}% | Completed: {h.completed}")
        
        # Watchlist
        watchlist = db.query(Watchlist).order_by(Watchlist.added_at.desc()).limit(10).all()
        watchlist_count = db.query(Watchlist).count()
        print(f"\n📋 WATCHLIST: {watchlist_count} total (showing latest 10)")
        print("-" * 80)
        for w in watchlist:
            print(f"  • User: {w.user_id:<20} | Movie: {w.movie_id:<10} | Added: {w.added_at}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
