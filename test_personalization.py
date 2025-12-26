"""
Test personalization features of the recommendation system
Verifies that different users get different personalized recommendations
"""
import requests
import json
from collections import Counter

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

def get_user_recommendations(user_id, n=10):
    """Get personalized recommendations for a user"""
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations",
            params={"rec_type": "personalized", "user_id": user_id, "n": n},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            print(f"❌ Error getting recommendations: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return []

def get_user_behavior(user_id):
    """Analyze user behavior (requires endpoint)"""
    try:
        # This would call a behavior analysis endpoint if available
        # For now, we'll just get watch history
        pass
    except Exception:
        pass

def compare_recommendations(user1_recs, user2_recs):
    """Compare recommendations between two users"""
    if not user1_recs or not user2_recs:
        print("⚠️  Cannot compare - missing recommendations")
        return
    
    user1_ids = {movie.get('id') for movie in user1_recs}
    user2_ids = {movie.get('id') for movie in user2_recs}
    
    common = user1_ids.intersection(user2_ids)
    unique_user1 = user1_ids - user2_ids
    unique_user2 = user2_ids - user1_ids
    
    print(f"\n📊 Recommendation Comparison:")
    print(f"   User 1: {len(user1_ids)} movies")
    print(f"   User 2: {len(user2_ids)} movies")
    print(f"   Common: {len(common)} movies ({len(common)/len(user1_ids)*100:.1f}%)")
    print(f"   Unique to User 1: {len(unique_user1)} movies")
    print(f"   Unique to User 2: {len(unique_user2)} movies")
    
    if len(common) < len(user1_ids) * 0.5:
        print("✅ Good personalization - users get different recommendations!")
    else:
        print("⚠️  Limited personalization - recommendations are similar")

def analyze_genre_preferences(recommendations):
    """Analyze genre distribution in recommendations"""
    genre_counter = Counter()
    for movie in recommendations:
        genres = movie.get('genres', '')
        if genres:
            for genre in str(genres).split('|'):
                genre = genre.strip()
                if genre:
                    genre_counter[genre] += 1
    
    return genre_counter

def main():
    print("=" * 60)
    print("🎬 Testing Movie Recommendation Personalization")
    print("=" * 60)
    
    # 1. Check server health
    if not test_health():
        print("\n⚠️  Please start the backend server first:")
        print("   python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    print("\n" + "=" * 60)
    print("📝 Testing Personalized Recommendations")
    print("=" * 60)
    
    # 2. Test personalized recommendations for different users
    test_users = ["1", "2", "10", "50"]
    user_recommendations = {}
    
    for user_id in test_users:
        print(f"\n🔍 Getting recommendations for User {user_id}...")
        recs = get_user_recommendations(user_id, n=10)
        user_recommendations[user_id] = recs
        
        if recs:
            print(f"✅ Got {len(recs)} recommendations for User {user_id}")
            
            # Show top 3 movies
            print(f"   Top 3 movies:")
            for i, movie in enumerate(recs[:3], 1):
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'N/A')
                rating = movie.get('vote_average', 'N/A')
                genres = movie.get('genres', 'N/A')
                print(f"   {i}. {title} ({year}) - Rating: {rating} - Genres: {genres}")
            
            # Analyze genres
            genre_prefs = analyze_genre_preferences(recs)
            top_genres = genre_prefs.most_common(3)
            if top_genres:
                print(f"   Top genres: {', '.join([f'{g}({c})' for g, c in top_genres])}")
        else:
            print(f"❌ No recommendations returned for User {user_id}")
    
    # 3. Compare recommendations between users
    print("\n" + "=" * 60)
    print("📊 Comparing Personalization")
    print("=" * 60)
    
    if len(user_recommendations) >= 2:
        users = list(user_recommendations.keys())
        compare_recommendations(
            user_recommendations[users[0]], 
            user_recommendations[users[1]]
        )
    
    # 4. Test different recommendation types
    print("\n" + "=" * 60)
    print("🎯 Testing Different Recommendation Types")
    print("=" * 60)
    
    rec_types = ["collaborative", "personalized"]
    for rec_type in rec_types:
        try:
            response = requests.get(
                f"{BASE_URL}/recommendations",
                params={"rec_type": rec_type, "user_id": "1", "n": 5},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"✅ {rec_type}: Got {len(results)} recommendations")
            else:
                print(f"❌ {rec_type}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {rec_type}: Failed - {e}")
    
    print("\n" + "=" * 60)
    print("✅ Personalization Testing Complete!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - Different users should get different recommendations")
    print("   - Recommendations should match user's watch history and preferences")
    print("   - Personalized type uses user behavior analysis for better results")

if __name__ == "__main__":
    main()
