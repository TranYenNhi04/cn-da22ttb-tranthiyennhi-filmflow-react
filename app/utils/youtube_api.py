import os
import re
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_youtube_video(movie_title: str, year: int = None) -> str:
    """
    Trả về URL embed YouTube trực tiếp cho trailer.
    - Nếu `YOUTUBE_API_KEY` được set, gọi YouTube Data API để tìm video id tốt nhất.
    - Nếu không có API key hoặc gọi API thất bại, fallback về embed-search (cũ).
    """
    # Loại bỏ năm trong ngoặc nếu có
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", movie_title).strip()

    # Chuẩn bị query
    if year:
        query_text = f"{clean_title} {year} official trailer"
    else:
        query_text = f"{clean_title} official trailer"

    # Nếu có API key thì gọi YouTube Data API để lấy videoId
    if YOUTUBE_API_KEY:
        try:
            params = {
                "part": "snippet",
                "q": query_text,
                "type": "video",
                "maxResults": 1,
                "key": YOUTUBE_API_KEY,
            }
            resp = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=5)
            # Nếu response lỗi, raise để vào except
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if items:
                video_id = items[0].get("id", {}).get("videoId")
                if video_id:
                    return f"https://www.youtube-nocookie.com/embed/{video_id}"
        except requests.exceptions.HTTPError as he:
            # HTTP error from YouTube API (403, 400, etc.). Log status and short message, but do NOT print the API key.
            try:
                status = he.response.status_code
                msg = he.response.text[:500]
            except Exception:
                status = 'unknown'
                msg = str(he)
            print(f"YouTube Data API HTTP error: {status} - {msg}")
            # For 403 (forbidden) it's usually API key invalid/restricted or quota/billing issue.
        except Exception as e:
            # Network or parse error — log and fallback silently
            print(f"YouTube Data API error: {str(e)}")

    # Fallback: return a YouTube search results page (opens playable page in new tab)
    # The previous embed-search URL often leads to "video unavailable" in iframes.
    encoded_query = urllib.parse.quote(query_text)
    return f"https://www.youtube.com/results?search_query={encoded_query}"

