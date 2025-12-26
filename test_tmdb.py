import os
os.environ['TMDB_API_KEY'] = '8265bd1679663a7ea12ac168da84d2e8'

from app.utils.tmdb_api import get_movie_data

print("\n🎬 Testing TMDB API...")
result = get_movie_data('Harry Potter and the Philosopher\'s Stone', 2001)

if result:
    print("✅ TMDB API hoạt động!")
    print(f"   Poster URL: {result.get('poster_url')}")
else:
    print("❌ TMDB API không hoạt động")
    
# Test with search
print("\n🔍 Testing search endpoint...")
import requests
response = requests.get("http://127.0.0.1:8000/movies/search?q=Inception&limit=1")
data = response.json()
if data['results']:
    movie = data['results'][0]
    print(f"✅ Movie: {movie['title']}")
    print(f"   Poster: {movie['poster_url']}")
