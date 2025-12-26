#!/usr/bin/env python3
"""
Script để test và debug recommendations
"""
import requests
import json
from collections import Counter

API_BASE = "http://localhost:8000"

def test_recommendations(user_id=None, rec_type="personalized", n=20):
    """Test recommendations và phân tích thể loại"""
    
    url = f"{API_BASE}/recommendations"
    params = {
        "rec_type": rec_type,
        "n": n
    }
    if user_id:
        params["user_id"] = user_id
    
    print(f"\n{'='*80}")
    print(f"Testing {rec_type} recommendations" + (f" for user {user_id}" if user_id else ""))
    print(f"{'='*80}\n")
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    movies = data.get("results", [])
    
    print(f"✓ Got {len(movies)} recommendations\n")
    
    # Phân tích thể loại
    genre_counter = Counter()
    
    print(f"{'#':<4} {'Title':<40} {'Rating':<8} {'Genres'}")
    print("-" * 100)
    
    for i, movie in enumerate(movies, 1):
        title = movie.get("title", "Unknown")[:38]
        rating = movie.get("vote_average", 0)
        genres = movie.get("genres", "")
        
        # Parse genres
        if isinstance(genres, str):
            genre_list = [g.strip() for g in genres.split("|") if g.strip()]
        else:
            genre_list = []
        
        for genre in genre_list:
            genre_counter[genre] += 1
        
        genres_str = ", ".join(genre_list[:3]) if genre_list else "N/A"
        
        print(f"{i:<4} {title:<40} {rating:<8.1f} {genres_str}")
    
    # Thống kê thể loại
    print(f"\n{'='*80}")
    print("Genre Distribution:")
    print(f"{'='*80}")
    
    for genre, count in genre_counter.most_common(10):
        percentage = (count / len(movies)) * 100
        bar = "█" * int(percentage / 5)
        print(f"{genre:<20} {count:>3} ({percentage:>5.1f}%) {bar}")
    
    print()

def test_user_history(user_id):
    """Xem lịch sử xem của user để so sánh"""
    print(f"\n{'='*80}")
    print(f"Watch History for {user_id}")
    print(f"{'='*80}\n")
    
    response = requests.get(f"{API_BASE}/user/{user_id}/watched")
    
    if response.status_code == 200:
        data = response.json()
        movies = data.get("movies", [])
        
        if not movies:
            print("No watch history found")
            return
        
        genre_counter = Counter()
        
        print(f"{'Title':<40} {'Genres'}")
        print("-" * 80)
        
        for movie in movies[:10]:  # Top 10
            title = movie.get("title", "Unknown")[:38]
            genres = movie.get("genres", "")
            
            if isinstance(genres, str):
                genre_list = [g.strip() for g in genres.split("|") if g.strip()]
            else:
                genre_list = []
            
            for genre in genre_list:
                genre_counter[genre] += 1
            
            genres_str = ", ".join(genre_list[:3]) if genre_list else "N/A"
            print(f"{title:<40} {genres_str}")
        
        print(f"\nFavorite Genres (from history):")
        for genre, count in genre_counter.most_common(5):
            print(f"  {genre}: {count}")
    else:
        print(f"❌ Could not fetch history: {response.status_code}")

if __name__ == "__main__":
    import sys
    
    # Test với user có lịch sử nếu có
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        test_user_history(user_id)
        test_recommendations(user_id=user_id, rec_type="personalized", n=20)
    else:
        # Test anonymous
        print("\nTesting anonymous recommendations...")
        test_recommendations(rec_type="personalized", n=20)
        
        print("\n\nTo test with a specific user:")
        print("  python test_recommendations.py <user_id>")
