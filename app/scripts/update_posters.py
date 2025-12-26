"""
Update poster URLs for movies from TMDB API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_postgresql import get_db_session, Movie
from utils.tmdb_api import get_movie_details
import time

def update_posters():
    """Update poster URLs for all movies in database"""
    with get_db_session() as session:
        try:
            # Get all movies without poster_url
            movies = session.query(Movie).filter(
                (Movie.poster_url == None) | (Movie.poster_url == '') | (Movie.poster_url.like('movie_%'))
            ).all()
            
            print(f"Found {len(movies)} movies without posters")
            
            updated = 0
            failed = 0
            
            for movie in movies:
                try:
                    print(f"Fetching poster for: {movie.title} (ID: {movie.movie_id})")
                    
                    # Get movie details from TMDB
                    details = get_movie_details(int(movie.movie_id))
                    
                    if details and 'poster_path' in details and details['poster_path']:
                        poster_path = details['poster_path']
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                        
                        movie.poster_path = poster_path
                        movie.poster_url = poster_url
                        
                        # Also update backdrop if available
                        if 'backdrop_path' in details and details['backdrop_path']:
                            movie.backdrop_path = details['backdrop_path']
                        
                        updated += 1
                        print(f"  ✓ Updated: {poster_url}")
                    else:
                        failed += 1
                        print(f"  ✗ No poster found")
                    
                    # Commit every 10 movies
                    if updated % 10 == 0:
                        session.commit()
                    
                    # Rate limit: TMDB allows 40 requests per 10 seconds
                    time.sleep(0.26)
                    
                except Exception as e:
                    failed += 1
                    print(f"  ✗ Error: {str(e)}")
                    continue
            
            # Final commit
            session.commit()
            
            print(f"\n{'='*50}")
            print(f"Update complete!")
            print(f"Updated: {updated} movies")
            print(f"Failed: {failed} movies")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            session.rollback()

if __name__ == "__main__":
    update_posters()
