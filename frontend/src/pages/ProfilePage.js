import React, { useState, useEffect } from 'react';
import './ProfilePage.css';
import { API_BASE } from '../config';

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState({});
  const [watchlist, setWatchlist] = useState([]);
  const [watchHistory, setWatchHistory] = useState([]);
  const [movieData, setMovieData] = useState({}); // Store full movie data by ID
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);
  const [selectedQuality, setSelectedQuality] = useState('720p');
  const [selectedLangs, setSelectedLangs] = useState(['vi', 'en']);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const [showAllWatchlist, setShowAllWatchlist] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setUser(userData);
      // Always skip cache on mount to get fresh data
      fetchProfile(userData.userId, true);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async (userId, skipCache = false) => {
    // Try cache first for instant display (unless skipCache is true)
    if (!skipCache) {
      try {
        const cacheKey = `profile_${userId}`;
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
          const data = JSON.parse(cached);
          setProfile(data.profile);
          setPreferences(data.preferences || {});
          setWatchlist(data.watchlist || []);
          setWatchHistory(data.history || []);
          setLoading(false);
          setInitialLoad(false);
        }
      } catch (e) {}
    }
    
    try {
      // Fetch user stats from new PostgreSQL API
      const statsResponse = await fetch(`${API_BASE}/user/${userId}/stats`);
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setProfile({
          userId: userId,
          name: stats.name || user?.name,
          email: stats.email || user?.email,
          totalRatings: stats.total_ratings || 0,
          totalWatchlist: stats.total_watchlist || 0,
          totalWatched: stats.total_watched || 0,
          totalReviews: stats.total_reviews || 0,
          favoriteGenres: stats.favorite_genres || [],
          createdAt: stats.created_at
        });
      }
      
      // Get preferences (keep old logic)
      try {
        const prefsRes = await fetch(`${API_BASE}/user/${userId}/preferences`);
        if (prefsRes.ok) {
          const prefs = await prefsRes.json();
          setPreferences(prefs.preferences || {});
        }
      } catch (e) {
        console.warn('Failed to fetch preferences:', e);
      }
      
      // Get watchlist from new PostgreSQL API
      try {
        const watchlistRes = await fetch(`${API_BASE}/user/${userId}/watchlist`);
        if (watchlistRes.ok) {
          const watchlistData = await watchlistRes.json();
          const movies = watchlistData.movies || [];
          
          // Deduplicate by movie ID
          const uniqueMovies = [];
          const seenIds = new Set();
          movies.forEach(movie => {
            const movieId = movie.id || movie.movie_id;
            if (!seenIds.has(movieId)) {
              seenIds.add(movieId);
              uniqueMovies.push({
                ...movie,
                id: movieId,
                poster_url: movie.poster_url || movie.poster_path
              });
            }
          });
          
          setWatchlist(uniqueMovies);
          
          // Build movie data map
          const movieMap = {};
          uniqueMovies.forEach(movie => {
            movieMap[movie.id] = movie;
          });
          setMovieData(prev => ({...prev, ...movieMap}));
        }
      } catch (e) {
        console.warn('Failed to fetch watchlist:', e);
      }
      
      // Get watch history from new PostgreSQL API
      try {
        const historyRes = await fetch(`${API_BASE}/user/${userId}/watched`);
        if (historyRes.ok) {
          const historyData = await historyRes.json();
          const movies = historyData.movies || [];
          
          // Deduplicate by movieId - keep only most recent entry for each movie
          const uniqueHistory = [];
          const seenMovieIds = new Set();
          movies.forEach(movie => {
            const movieId = movie.id || movie.movie_id;
            if (!seenMovieIds.has(movieId)) {
              seenMovieIds.add(movieId);
              uniqueHistory.push({
                movieId: movieId,
                watchedAt: movie.watched_at,
                progress: movie.progress,
                completed: movie.completed,
                ...movie
              });
            }
          });
          
          setWatchHistory(uniqueHistory);
          
          // Build movie data map
          const movieMap = {};
          uniqueHistory.forEach(entry => {
            movieMap[entry.movieId] = {
              id: entry.movieId,
              title: entry.title,
              poster_url: entry.poster_url || entry.poster_path,
              year: entry.year,
              vote_average: entry.vote_average
            };
          });
          setMovieData(prev => ({...prev, ...movieMap}));
        }
      } catch (e) {
        console.warn('Failed to fetch watch history:', e);
      }
      
      // Cache everything for next time
      try {
        const cacheKey = `profile_${userId}`;
        localStorage.setItem(cacheKey, JSON.stringify({
          profile: profile,
          preferences: preferences,
          watchlist: watchlist,
          history: watchHistory
        }));
      } catch (e) {}
      
      setLoading(false);
      setInitialLoad(false);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setLoading(false);
      setInitialLoad(false);
    }
  };

  const updateQuality = async (quality) => {
    setSelectedQuality(quality);
    localStorage.setItem('video_quality', quality);
  };

  const updateLanguages = async (langs) => {
    setSelectedLangs(langs);
    localStorage.setItem('subtitle_languages', JSON.stringify(langs));
  };

  const updateGenrePreferences = async (genres) => {
    try {
      const response = await fetch(`${API_BASE}/user/${user.userId}/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          favorite_genres: genres,
          quality: selectedQuality,
          languages: selectedLangs
        })
      });
      if (response.ok) {
        setPreferences({ ...preferences, favorite_genres: genres });
        // Refresh profile data
        fetchProfile(user.userId);
      }
    } catch (error) {
      console.error('Failed to update preferences:', error);
    }
  };
  
  const removeFromWatchlist = async (movieId) => {
    try {
      // Use new PostgreSQL API endpoint
      const response = await fetch(`${API_BASE}/user/${user.userId}/watchlist/toggle?movie_id=${movieId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.action === 'removed') {
          const updatedWatchlist = watchlist.filter(m => m.id !== movieId);
          setWatchlist(updatedWatchlist);
          
          // Update localStorage cache
          try {
            const cacheKey = `watchlist_${user.userId}`;
            localStorage.setItem(cacheKey, JSON.stringify(updatedWatchlist));
          } catch (e) {
            console.warn('Failed to update watchlist cache:', e);
          }
        }
      } else {
        console.error('Failed to remove from watchlist:', await response.text());
      }
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
  };

  if (initialLoad) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          {/* Skeleton Header */}
          <div className="profile-header">
            <div className="profile-avatar skeleton-avatar">👤</div>
            <div className="profile-info">
              <div className="skeleton-text skeleton-title"></div>
              <div className="skeleton-text skeleton-subtitle"></div>
            </div>
          </div>
          
          {/* Skeleton sections */}
          <div className="settings-section">
            <div className="skeleton-text skeleton-heading"></div>
            <div className="skeleton-box"></div>
          </div>
          
          <div className="watchlist-section">
            <div className="skeleton-text skeleton-heading"></div>
            <div className="movies-grid">
              {Array.from({length: 6}).map((_, i) => (
                <div key={i} className="movie-card-skeleton"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  if (!user) return <div className="profile-page"><p>Please login first</p></div>;

  return (
    <div className="profile-page">
      <div className="profile-container">
        
        {/* Header */}
        <div className="profile-header">
          <div className="profile-avatar">👤</div>
          <div className="profile-info">
            <h1>{user.userId}</h1>
          </div>
        </div>

        {/* Settings */}
        <div className="settings-section">
          <h2>⚙️ Cài Đặt</h2>
          
          {/* Video Quality */}
          <div className="setting-group">
            <h3>Chất Lượng Video</h3>
            <div className="quality-options">
              {['480p', '720p', '1080p', '4K'].map(quality => (
                <button
                  key={quality}
                  className={`quality-btn ${selectedQuality === quality ? 'active' : ''}`}
                  onClick={() => updateQuality(quality)}
                >
                  {quality}
                </button>
              ))}
            </div>
          </div>

          {/* Languages */}
          <div className="setting-group">
            <h3>Ngôn Ngữ Phụ Đề</h3>
            <div className="language-options">
              {[
                { code: 'vi', name: 'Tiếng Việt' },
                { code: 'en', name: 'English' },
                { code: 'zh', name: '中文' }
              ].map(lang => (
                <label key={lang.code} className="language-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedLangs.includes(lang.code)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        updateLanguages([...selectedLangs, lang.code]);
                      } else {
                        updateLanguages(selectedLangs.filter(l => l !== lang.code));
                      }
                    }}
                  />
                  {lang.name}
                </label>
              ))}
            </div>
          </div>

          {/* Favorite Genres */}
          <div className="setting-group">
            <h3>Thể Loại Yêu Thích</h3>
            <div className="genre-options">
              {['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi'].map(genre => (
                <button
                  key={genre}
                  className={`genre-btn ${preferences.favorite_genres?.includes(genre) ? 'active' : ''}`}
                  onClick={() => {
                    const current = preferences.favorite_genres || [];
                    if (current.includes(genre)) {
                      updateGenrePreferences(current.filter(g => g !== genre));
                    } else {
                      updateGenrePreferences([...current, genre]);
                    }
                  }}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="stats-section">
          <h2>📊 Thống Kê</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{profile?.totalRatings || 0}</div>
              <div className="stat-label">Đánh Giá</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{profile?.totalWatchlist || 0}</div>
              <div className="stat-label">Phim Đã Lưu</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{profile?.favoriteGenres?.length || 0}</div>
              <div className="stat-label">Thể Loại Yêu Thích</div>
            </div>
          </div>
        </div>

        {/* Watch History */}
        {watchHistory?.length > 0 && (
          <div className="activity-section">
            <h2>📺 Lịch Sử Xem ({watchHistory.length})</h2>
            <div className="movies-grid">
              {watchHistory.slice(0, showAllHistory ? watchHistory.length : 5).map((entry) => {
                const movie = movieData[entry.movieId];
                if (!movie) return null;
                return (
                  <div key={entry.movieId} className="movie-poster-card">
                    <div className="movie-poster-wrapper">
                      {movie.poster_url ? (
                        <img src={movie.poster_url} alt={movie.title} className="movie-poster" />
                      ) : (
                        <div className="no-poster">Không có poster</div>
                      )}
                    </div>
                    <div className="movie-poster-info">
                      <h4 className="movie-poster-title">{movie.title}</h4>
                      <p className="movie-poster-meta">⭐ {movie.vote_average || 'N/A'}</p>
                      <p className="movie-watch-date">
                        {new Date(entry.viewed_at || entry.timestamp).toLocaleDateString('vi-VN')}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
            {watchHistory.length > 5 && (
              <div className="show-more-container">
                <button 
                  className="show-more-btn"
                  onClick={() => setShowAllHistory(!showAllHistory)}
                >
                  {showAllHistory ? '▲ Thu gọn' : `▼ Xem thêm (${watchHistory.length - 5} phim)`}
                </button>
              </div>
            )}
          </div>
        )}
        
        {/* Watchlist */}
        {watchlist?.length > 0 && (
          <div className="activity-section">
            <h2>❤️ Danh Sách Đã Lưu ({watchlist.length})</h2>
            <div className="movies-grid">
              {watchlist.slice(0, showAllWatchlist ? watchlist.length : 5).map((movie) => (
                <div key={movie.id} className="movie-poster-card">
                  <div className="movie-poster-wrapper">
                    {movie.poster_url ? (
                      <img src={movie.poster_url} alt={movie.title} className="movie-poster" />
                    ) : (
                      <div className="no-poster">Không có poster</div>
                    )}
                  </div>
                  <div className="movie-poster-info">
                    <h4 className="movie-poster-title">{movie.title}</h4>
                    <p className="movie-poster-meta">⭐ {movie.vote_average || 'N/A'}</p>
                    <button 
                      className="remove-btn"
                      onClick={() => removeFromWatchlist(movie.id)}
                    >
                      🗑️ Xóa
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {watchlist.length > 5 && (
              <div className="show-more-container">
                <button 
                  className="show-more-btn"
                  onClick={() => setShowAllWatchlist(!showAllWatchlist)}
                >
                  {showAllWatchlist ? '▲ Thu gọn' : `▼ Xem thêm (${watchlist.length - 5} phim)`}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
