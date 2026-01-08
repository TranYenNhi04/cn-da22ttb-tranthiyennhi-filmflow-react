import os
import requests
from time import sleep

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TIMEOUT = 15  # Increased timeout to 15 seconds
MAX_RETRIES = 3  # Retry up to 3 times

def get_movie_data(movie_title: str, year: int = None):
    """
    Tìm thông tin phim từ TMDB bao gồm poster và video trailer.
    Trả về dict với poster_url và video_url hoặc None.
    """
    if not TMDB_API_KEY:
        print("TMDB_API_KEY chưa được set")
        return None

    try:
        # Tìm phim với retry logic
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": movie_title,
            "include_adult": False,
        }
        if year:
            params["year"] = year
        
        # Retry logic for search
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, params=params, timeout=TIMEOUT)
                data = resp.json()
                break
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    print(f"Timeout fetching data for {movie_title} after {MAX_RETRIES} attempts")
                    return None
            except Exception as e:
                print(f"Error in attempt {attempt + 1} for {movie_title}: {e}")
                if attempt < MAX_RETRIES - 1:
                    sleep(1)
                    continue
                return None
        
        if not data.get("results"):
            return None
            
        movie = data["results"][0]
        movie_id = movie.get("id")
        result = {}
        
        # Lấy poster
        poster_path = movie.get("poster_path")
        if poster_path:
            result["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Lấy videos (trailers) với retry
        if movie_id:
            video_url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
            video_params = {"api_key": TMDB_API_KEY}
            
            for attempt in range(MAX_RETRIES):
                try:
                    video_resp = requests.get(video_url, params=video_params, timeout=TIMEOUT)
                    video_data = video_resp.json()
                    break
                except requests.exceptions.Timeout:
                    if attempt < MAX_RETRIES - 1:
                        sleep(1)
                        continue
                    else:
                        print(f"Timeout fetching videos for {movie_title}")
                        video_data = {}
                        break
                except Exception:
                    if attempt < MAX_RETRIES - 1:
                        sleep(1)
                        continue
                    video_data = {}
                    break
            
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

def get_movie_details(movie_id: int):
    """
    Lấy chi tiết phim từ TMDB theo ID.
    Trả về dict với thông tin phim hoặc None.
    """
    if not TMDB_API_KEY:
        print("TMDB_API_KEY chưa được set")
        return None

    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "vi-VN"
        }
        
        # Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, params=params, timeout=TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                return None
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    sleep(1)
                    continue
                else:
                    print(f"Timeout fetching movie {movie_id} after {MAX_RETRIES} attempts")
                    return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    sleep(1)
                    continue
                else:
                    print(f"Error fetching movie {movie_id}: {e}")
                    return None
        
        return None
        
    except Exception as e:
        print(f"Error fetching movie {movie_id}: {e}")
        return None
