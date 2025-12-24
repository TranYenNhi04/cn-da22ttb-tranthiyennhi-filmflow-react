import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def get_movie_data(movie_title: str, year: int = None):
    """
    Tìm thông tin phim từ TMDB bao gồm poster và video trailer.
    Trả về dict với poster_url và video_url hoặc None.
    """
    if not TMDB_API_KEY:
        print("TMDB_API_KEY chưa được set")
        return None

    try:
        # Tìm phim
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": movie_title,
            "include_adult": False,
        }
        if year:
            params["year"] = year
            
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        
        if not data.get("results"):
            return None
            
        movie = data["results"][0]
        movie_id = movie.get("id")
        result = {}
        
        # Lấy poster
        poster_path = movie.get("poster_path")
        if poster_path:
            result["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Lấy videos (trailers)
        if movie_id:
            video_url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
            video_params = {"api_key": TMDB_API_KEY}
            video_resp = requests.get(video_url, params=video_params, timeout=5)
            video_data = video_resp.json()
            
            videos = video_data.get("results", [])
            # Tìm trailer YouTube
            for video in videos:
                if video.get("site") == "YouTube" and video.get("type") in ["Trailer", "Teaser"]:
                    video_key = video.get("key")
                    if video_key:
                        result["video_url"] = f"https://www.youtube.com/watch?v={video_key}"
                        break
        
        return result if result else None
        
    except Exception as e:
        print(f"Error fetching data for {movie_title}: {e}")
        return None

def get_movie_poster(movie_title: str) -> str | None:
    """
    Tìm poster phim từ TMDB.
    Trả về URL poster hoặc None nếu không tìm thấy.
    """
    data = get_movie_data(movie_title)
    return data.get("poster_url") if data else None
