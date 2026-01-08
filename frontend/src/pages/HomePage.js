import React, { useEffect, useState, useRef } from 'react';
import './HomePage.css';
import { API_BASE } from '../config';
import { MovieGridSkeleton, SectionSkeleton } from '../components/MovieSkeleton';
import LazyImage from '../components/LazyImage';

function MovieCard({ movie, commentCounts, onClick }) {
  const poster = movie.poster_url || movie.poster_path || movie.poster;
  const rating = parseFloat(movie.vote_average) || 0;
  const ratingColor = rating >= 8 ? '#4caf50' : rating >= 7 ? '#ffc107' : '#ff9800';
  
  return (
    <div className="movie-card-clean" onClick={() => onClick && onClick(movie)}>
      <div className="card-poster-container">
        {poster ? (
          <LazyImage
            src={poster}
            alt={movie.title}
            className="card-poster-img"
            placeholder={`https://via.placeholder.com/300x450/1a1a1a/666?text=${encodeURIComponent(movie.title?.substring(0, 20) || 'Movie')}`}
          />
        ) : (
          <div className="card-no-poster">🎬</div>
        )}
        
        {/* Rating Badge - top right */}
        {rating > 0 && (
          <div className="card-rating" style={{ backgroundColor: ratingColor }}>
            <span className="rating-star">⭐</span>
            <span className="rating-text">{rating.toFixed(1)}</span>
          </div>
        )}
        
        {/* Bottom info bar - always visible */}
        <div className="card-info-bar">
          <div className="card-info-content">
            <h3 className="card-movie-title">{movie.title}</h3>
            <div className="card-movie-meta">
              {movie.year && <span className="card-year">📅 {movie.year}</span>}
              {commentCounts && commentCounts[movie.id] > 0 && (
                <span className="card-comments">💬 {commentCounts[movie.id]}</span>
              )}
            </div>
          </div>
        </div>
        
        {/* Hover overlay with play button */}
        <div className="card-play-overlay">
          <button className="card-play-btn" onClick={(e) => { e.stopPropagation(); onClick && onClick(movie); }}>
            <span className="play-btn-icon">▶</span>
            <span className="play-btn-text">XEM NGAY</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function HomePage({ onMovieClick }) {
  const [allMovies, setAllMovies] = useState([]);
  const [commentCounts, setCommentCounts] = useState({});
  const [featuredMovies, setFeaturedMovies] = useState([]);
  const [newMovies, setNewMovies] = useState([]);
  const [topRatedMovies, setTopRatedMovies] = useState([]);
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [heroMovies, setHeroMovies] = useState([]);
  const [watchHistory, setWatchHistory] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingSections, setLoadingSections] = useState({
    trending: false,  // Start with false, will only show if no cached data
    featured: false,
    topRated: false,
    new: false
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef(null);
  
  // Filter states
  const [genreFilter, setGenreFilter] = useState('all');
  const [yearFilter, setYearFilter] = useState('all');
  const [sortBy, setSortBy] = useState('rating');

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    if (query.trim().length > 0) {
      // Check cache first for instant results
      const cacheKey = `search_${query.toLowerCase().trim()}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          const age = Date.now() - parsed.timestamp;
          if (age < 300000) { // 5 minutes cache
            setSearchResults(parsed.results || []);
            setIsSearching(true);
            return;
          }
        } catch (e) {}
      }
      
      searchTimeoutRef.current = setTimeout(async () => {
        setIsSearching(true);
        try {
          // Save search to history
          const storedUser = localStorage.getItem('user');
          const userId = storedUser ? JSON.parse(storedUser)?.userId : null;
          const userParam = userId ? `&user_id=${encodeURIComponent(userId)}` : '';
          
          const response = await fetch(`${API_BASE}/movies/autocomplete?q=${encodeURIComponent(query)}&n=20${userParam}`);
          if (response.ok) {
            const data = await response.json();
            const results = data.results || [];
            setSearchResults(results);
            
            // Cache results
            try {
              localStorage.setItem(cacheKey, JSON.stringify({
                results: results,
                timestamp: Date.now()
              }));
            } catch (e) {}
          } else {
            setSearchResults([]);
          }
        } catch (error) {
          console.error('Search failed:', error);
          setSearchResults([]);
        }
      }, 150); // Faster debounce
    } else {
      setIsSearching(false);
      setSearchResults([]);
    }
  };

  const fetchCommentCounts = async (movies) => {
    try {
      const ids = movies.map(m => m.id).filter(Boolean);
      if (!ids.length) return;
      const resp = await fetch(`${API_BASE}/movies/comments/counts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movie_ids: ids }),
      });
      if (resp.ok) {
        const d = await resp.json();
        const counts = d.counts || d || {};
        setCommentCounts(prev => ({ ...prev, ...counts }));
      }
    } catch (e) {
      console.error('Failed to fetch comment counts:', e);
    }
  };

  // Map Vietnamese genre names to English equivalents
  const genreMap = {
    'action': ['action', 'hành động', 'hanh dong'],
    'comedy': ['comedy', 'hài', 'hai', 'hài hước'],
    'drama': ['drama', 'chính kịch', 'chinh kich'],
    'horror': ['horror', 'kinh dị', 'kinh di', 'thriller'],
    'romance': ['romance', 'lãng mạn', 'lang man', 'romantic'],
    'sci-fi': ['science fiction', 'sci-fi', 'scifi', 'khoa học viễn tưởng', 'fantasy'],
    'thriller': ['thriller', 'kinh dị', 'hồi hộp'],
    'adventure': ['adventure', 'phiêu lưu', 'phieu luu'],
    'crime': ['crime', 'hình sự', 'tội phạm'],
    'animation': ['animation', 'hoạt hình', 'anime'],
    'family': ['family', 'gia đình'],
    'mystery': ['mystery', 'bí ẩn', 'detective']
  };

  const filterMovies = (movies) => {
    let filtered = [...movies];
    
    // Genre filter - match both English and Vietnamese names
    if (genreFilter !== 'all') {
      const targetGenres = genreMap[genreFilter.toLowerCase()] || [genreFilter.toLowerCase()];
      filtered = filtered.filter(m => {
        try {
          let genres = m.genres;
          
          // Handle string format
          if (typeof genres === 'string') {
            try {
              genres = JSON.parse(genres);
            } catch (e) {
              // If JSON parse fails, treat as comma-separated string
              genres = genres.split(',').map(g => g.trim());
            }
          }
          
          // Handle array format
          if (Array.isArray(genres)) {
            const genreNames = genres.map(g => {
              if (typeof g === 'string') return g.toLowerCase();
              if (g && g.name) return g.name.toLowerCase();
              return '';
            }).filter(Boolean);
            
            // Check if any genre name matches any target genre
            const match = genreNames.some(gn => 
              targetGenres.some(tg => gn.includes(tg) || tg.includes(gn))
            );
            
            return match;
          }
          
          // Handle object with name property
          if (genres && genres.name) {
            const gn = genres.name.toLowerCase();
            return targetGenres.some(tg => gn.includes(tg) || tg.includes(gn));
          }
          
          return false;
        } catch (e) {
          console.warn('Genre parse error for movie:', m.title, e);
          return false;
        }
      });
    }
    
    // Year filter
    if (yearFilter !== 'all') {
      filtered = filtered.filter(m => {
        const year = parseInt(m.year) || parseInt(m.release_date?.substring(0, 4)) || 0;
        
        if (yearFilter === '2024') {
          return year >= 2024;
        } else if (yearFilter === '2023') {
          return year === 2023;
        } else if (yearFilter === '2020-2022') {
          return year >= 2020 && year <= 2022;
        } else if (yearFilter === 'older') {
          return year > 0 && year < 2020;
        }
        return true;
      });
    }
    
    // Sorting
    if (sortBy === 'rating') {
      filtered.sort((a, b) => (parseFloat(b.vote_average) || 0) - (parseFloat(a.vote_average) || 0));
    } else if (sortBy === 'newest') {
      filtered.sort((a, b) => {
        const yearA = parseInt(a.year) || parseInt(a.release_date?.substring(0, 4)) || 0;
        const yearB = parseInt(b.year) || parseInt(b.release_date?.substring(0, 4)) || 0;
        return yearB - yearA;
      });
    } else if (sortBy === 'title') {
      filtered.sort((a, b) => (a.title || '').localeCompare(b.title || '', 'vi'));
    }
    
    return filtered;
  };

  useEffect(() => {
    const fetchMovies = async () => {
      const storedUser = localStorage.getItem('user');
      const userId = storedUser ? JSON.parse(storedUser)?.userId : null;
      // Use recType-specific cache key to ensure personalization
      const recType = userId ? 'personalized' : 'collaborative';
      const cacheKey = `cached_recs_${recType}_${userId || 'public'}`;
      
      // INSTANT DISPLAY: Load from cache FIRST, show immediately
      let hasTrendingCache = false;
      let hasFeaturedCache = false;
      let hasNewCache = false;
      
      try {
        // Load watchlist from cache FIRST
        if (userId) {
          const watchlistCache = localStorage.getItem(`watchlist_${userId}`);
          if (watchlistCache) {
            try {
              const cached = JSON.parse(watchlistCache);
              if (Array.isArray(cached)) {
                setWatchlist(cached);
              }
            } catch (e) {}
          }
        }
        
        // Load trending from cache instantly
        const trendingCache = localStorage.getItem('cached_trending');
        if (trendingCache) {
          try {
            const parsed = JSON.parse(trendingCache);
            if (parsed.movies && parsed.movies.length > 0) {
              setTrendingMovies(parsed.movies);
              setHeroMovies(parsed.movies.slice(0, 20));
              hasTrendingCache = true;
            }
          } catch (e) {}
        }
        
        // Load featured from cache instantly
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
          try {
            const parsed = JSON.parse(cached);
            const movies = parsed.results || [];
            if (movies.length > 0) {
              const featured = movies.filter(m => m.vote_average >= 7).slice(0, 6);
              setFeaturedMovies(featured);
              setAllMovies(movies);
              setTopRatedMovies([...movies].sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0)).slice(0, 12));
              hasFeaturedCache = true;
            }
          } catch (e) {}
        }
        
        // Load new releases from cache
        const newCache = localStorage.getItem('cached_new_releases');
        if (newCache) {
          try {
            const parsed = JSON.parse(newCache);
            if (parsed.movies && parsed.movies.length > 0) {
              setNewMovies(parsed.movies);
              hasNewCache = true;
            }
          } catch (e) {}
        }
        
        // Only show loading for sections without cache
        setLoadingSections({
          trending: !hasTrendingCache,
          featured: !hasFeaturedCache,
          topRated: !hasFeaturedCache,
          new: !hasNewCache
        });
      } catch (e) {
        console.warn('Cache load failed:', e);
        // If cache fails, show loading
        setLoadingSections({
          trending: true,
          featured: true,
          topRated: true,
          new: true
        });
      }
      
      // BACKGROUND FETCH: Update with fresh data without blocking UI
      try {
        // Fetch trending in background
        fetch(`${API_BASE}/movies/trending?limit=12`)
          .then(res => res.ok ? res.json() : null)
          .then(data => {
            if (data && data.movies) {
              const movies = data.movies;
              setTrendingMovies(movies);
              setHeroMovies(movies.slice(0, 20));
              setLoadingSections(prev => ({ ...prev, trending: false }));
              
              // Cache for next time
              try {
                localStorage.setItem('cached_trending', JSON.stringify({ movies, ts: Date.now() }));
              } catch (e) {}
              
              if (movies.length > 0) {
                fetchCommentCounts(movies);
              }
            }
          })
          .catch(e => {
            console.error('Trending fetch failed:', e);
            setLoadingSections(prev => ({ ...prev, trending: false }));
          });

        // Fetch featured recommendations (in background, async, don't wait)
        setLoadingSections(prev => ({ ...prev, featured: true, topRated: true }));
        // Use personalized recommendations if user is logged in, otherwise collaborative
        const userParam = userId ? `&user_id=${encodeURIComponent(userId)}` : '';
        fetch(`${API_BASE}/recommendations?rec_type=${recType}&n=100${userParam}`)
          .then(recResp => {
            if (recResp.ok) {
              return recResp.json();
            }
            setLoadingSections(prev => ({ ...prev, featured: false, topRated: false }));
            return null;
          })
          .then(data => {
            if (data) {
              const movies = data.results || [];
              
              // Create global set of already displayed movie IDs from trending
              const displayedIds = new Set(trendingMovies.map(m => m.id));
              
              // Filter out movies that are already displayed
              const uniqueMovies = movies.filter(m => !displayedIds.has(m.id));
              
              // Split into sections ensuring no overlap between any sections
              const featured = [];
              const topRated = [];
              
              // First pass: get featured movies (high rated, not in trending)
              for (const movie of uniqueMovies) {
                if (featured.length >= 6) break;
                if (movie.vote_average >= 7 && !displayedIds.has(movie.id)) {
                  featured.push(movie);
                  displayedIds.add(movie.id); // Mark as displayed
                }
              }
              
              // Second pass: get top rated movies (exclude already displayed)
              const sortedByRating = [...uniqueMovies]
                .filter(m => !displayedIds.has(m.id))
                .sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0));
              
              for (const movie of sortedByRating) {
                if (topRated.length >= 12) break;
                if (!displayedIds.has(movie.id)) {
                  topRated.push(movie);
                  displayedIds.add(movie.id); // Mark as displayed
                }
              }
              
              setFeaturedMovies(featured);
              setAllMovies(uniqueMovies.slice(0, 12));
              setTopRatedMovies(topRated);
              setLoadingSections(prev => ({ ...prev, featured: false, topRated: false }));
              localStorage.setItem(cacheKey, JSON.stringify({ results: uniqueMovies }));
              
              // Fetch comment counts for all movies
              fetchCommentCounts([...featured, ...topRated]);
            }
          })
          .catch(e => {
            console.warn('Recommendations fetch failed:', e);
            setLoadingSections(prev => ({ ...prev, featured: false, topRated: false }));
          });
      } catch (e) {
        console.warn('Priority fetch failed:', e);
      }

      // PRIORITY 2: Background fetches (don't block UI)
      // Fetch user data from PostgreSQL - ONLY for authenticated users (not Anonymous)
      if (userId && userId !== 'Anonymous') {
        try {
          const [historyRes, watchlistRes] = await Promise.all([
            fetch(`${API_BASE}/user/${userId}/watched`),
            fetch(`${API_BASE}/user/${userId}/watchlist`)
          ]);
          
          if (historyRes.ok) {
            const data = await historyRes.json();
            const history = data.movies || [];
            
            // Deduplicate by movieId - keep only most recent entry for each movie
            const uniqueHistory = [];
            const seenMovieIds = new Set();
            history.forEach(movie => {
              const movieId = movie.id || movie.movie_id;
              if (!seenMovieIds.has(movieId)) {
                seenMovieIds.add(movieId);
                uniqueHistory.push({
                  movieId: movieId,
                  watchedAt: movie.watched_at,
                  progress: movie.progress,
                  ...movie
                });
              }
            });
            
            setWatchHistory(uniqueHistory);
          }
          if (watchlistRes.ok) {
            const data = await watchlistRes.json();
            const watchlistData = data.movies || [];
            setWatchlist(watchlistData);
            
            // Save to cache for next time
            try {
              localStorage.setItem(`watchlist_${userId}`, JSON.stringify(watchlistData));
            } catch (e) {
              console.warn('Failed to cache watchlist:', e);
            }
          }
        } catch (e) {
          console.warn('Failed to fetch user data:', e);
        }
      }

      // Fetch new releases in background
      fetch(`${API_BASE}/movies/new-releases?limit=50`)
        .then(newRes => newRes.ok ? newRes.json() : null)
        .then(data => {
          if (data) {
            const movies = data.movies || [];
            
            // Remove duplicates from new releases - exclude movies already in other sections
            const displayedIds = new Set([
              ...trendingMovies.map(m => m.id),
              ...featuredMovies.map(m => m.id),
              ...topRatedMovies.map(m => m.id)
            ]);
            
            const uniqueNewMovies = movies.filter(m => !displayedIds.has(m.id)).slice(0, 12);
            
            setNewMovies(uniqueNewMovies);
            setLoadingSections(prev => ({ ...prev, new: false }));
            
            // Cache for instant display next time
            try {
              localStorage.setItem('cached_new_releases', JSON.stringify({ movies: uniqueNewMovies, ts: Date.now() }));
            } catch (e) {}
            
            if (uniqueNewMovies.length > 0) {
              fetchCommentCounts(uniqueNewMovies);
            }
          }
        })
        .catch(e => {
          console.warn('Failed to fetch new releases:', e);
          setLoadingSections(prev => ({ ...prev, new: false }));
        });
    };

    fetchMovies();
  }, []);

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        {/* Animated Movie Posters Background */}
        <div className="hero-background">
          <div className="hero-posters-grid">
            {heroMovies.length > 0 ? (
              [...heroMovies, ...heroMovies, ...heroMovies].slice(0, 80).map((movie, idx) => (
                <div key={idx} className="hero-poster-item" style={{ animationDelay: `${idx * 0.04}s` }}>
                  <img 
                    src={movie.poster_url || movie.poster_path || `https://picsum.photos/seed/${movie.id}/300/450`} 
                    alt={movie.title}
                    loading="lazy"
                  />
                </div>
              ))
            ) : (
              // Placeholder gradient boxes while loading
              Array.from({ length: 80 }).map((_, idx) => (
                <div key={idx} className="hero-poster-item placeholder" style={{ animationDelay: `${idx * 0.04}s` }} />
              ))
            )}
          </div>
          <div className="hero-particles">
            {Array.from({ length: 30 }).map((_, i) => (
              <div key={i} className="particle" style={{ 
                left: `${Math.random() * 100}%`, 
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${3 + Math.random() * 4}s`
              }} />
            ))}
          </div>
          <div className="hero-gradient-overlay" />
        </div>
        
        {/* Hero Content */}
        <div className="hero-overlay">
          <div className="hero-glow-effect" />
          <h1 className="hero-title">
            <span className="hero-title-main">
              <span className="text-gradient">Khám phá thế giới điện ảnh</span>
            </span>
            <span className="hero-title-sub">
              <span className="text-shine">Không giới hạn</span>
            </span>
          </h1>
          <p className="hero-subtitle">
            Hàng nghìn bộ phim, series hot đang chờ bạn
          </p>
          <p className="hero-description">
            <span className="feature-badge">Chất lượng HD/4K cao cấp</span>
            <span className="feature-badge">Cập nhật liên tục mỗi ngày</span>
            <span className="feature-badge">Xem mọi lúc mọi nơi</span>
          </p>
          <div className="search-container">
            <input
              type="text"
              className="search-input"
              placeholder="Tìm kiếm phim, diễn viên, đạo diễn..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
            />
            <button className="search-btn">
              Tìm kiếm
            </button>
          </div>
        </div>
      </section>

      {/* Filter Bar */}
      {!isSearching && (
        <div className="filter-bar">
          <div className="filter-group">
            <select value={genreFilter} onChange={(e) => setGenreFilter(e.target.value)} className="filter-select">
              <option value="all">Tất cả thể loại</option>
              <option value="action">⚔️ Hành động</option>
              <option value="comedy">😂 Hài</option>
              <option value="drama">🎭 Chính kịch</option>
              <option value="horror">👻 Kinh dị</option>
              <option value="romance">💕 Lãng mạn</option>
              <option value="sci-fi">🚀 Khoa học viễn tưởng</option>
              <option value="adventure">🗺️ Phiêu lưu</option>
              <option value="thriller">🔪 Thriller</option>
              <option value="crime">🔫 Hình sự</option>
              <option value="animation">🎨 Hoạt hình</option>
              <option value="family">👨‍👩‍👧 Gia đình</option>
              <option value="mystery">🔍 Bí ẩn</option>
            </select>
          </div>

          <div className="filter-group">
            <select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)} className="filter-select">
              <option value="all">📅 Tất cả năm</option>
              <option value="2024">🆕 2024+</option>
              <option value="2023">📆 2023</option>
              <option value="2020-2022">🗓️ 2020-2022</option>
              <option value="older">⏪ Trước 2020</option>
            </select>
          </div>

          <div className="filter-group">
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="filter-select">
              <option value="rating">⭐ Đánh giá cao</option>
              <option value="newest">🆕 Mới nhất</option>
              <option value="title">🔤 Tên A-Z</option>
            </select>
          </div>
        </div>
      )}

      {/* Search Results */}
      {isSearching && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">🔎 Kết quả tìm kiếm "{searchQuery}"</h2>
          </div>
          {searchResults.length > 0 ? (
            <div className="movie-grid">
              {searchResults.map((movie) => (
                <MovieCard 
                  key={`search-${movie.id}`}
                  movie={movie} 
                  commentCounts={commentCounts} 
                  onClick={onMovieClick}
                />
              ))}
            </div>
          ) : (
            <div className="no-results">Không tìm thấy phim</div>
          )}
        </section>
      )}

      {/* Watch History */}
      {!isSearching && watchHistory.length > 0 && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">📺 Tiếp tục xem</h2>
          </div>
          <div className="movie-grid">
            {watchHistory.slice(0, 12).map((entry) => {
              // Use movie data directly from watch history entry
              const movie = {
                id: entry.movieId || entry.id,
                title: entry.title,
                poster_url: entry.poster_url,
                poster_path: entry.poster_path,
                year: entry.year,
                vote_average: entry.vote_average
              };
              
              return (
                <MovieCard 
                  key={entry.movieId || entry.id} 
                  movie={movie} 
                  commentCounts={commentCounts} 
                  onClick={onMovieClick}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Trending */}
      {!isSearching && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">🔥 Đang Hot Nhất</h2>
          </div>
          {loadingSections.trending ? (
            <MovieGridSkeleton count={12} />
          ) : trendingMovies.length === 0 ? (
            <div className="no-results">Chưa có phim trending</div>
          ) : (() => {
            const filtered = filterMovies(trendingMovies).slice(0, 12);
            return filtered.length > 0 ? (
              <div className="movie-grid">
                {filtered.map((movie) => (
                  <MovieCard 
                    key={`trending-${movie.id}`}
                    movie={movie} 
                    commentCounts={commentCounts} 
                    onClick={onMovieClick}
                  />
                ))}
              </div>
            ) : (
              <div className="no-results">Không tìm thấy phim phù hợp với bộ lọc</div>
            );
          })()}
        </section>
      )}

      {/* Featured/Recommendations */}
      {!isSearching && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">🎯 Gợi Ý Dành Riêng Cho Bạn</h2>
          </div>
          {loadingSections.featured ? (
            <MovieGridSkeleton count={6} />
          ) : featuredMovies.length === 0 ? (
            <div className="no-results">Chưa có gợi ý</div>
          ) : (() => {
            const filtered = filterMovies(featuredMovies);
            return filtered.length > 0 ? (
              <div className="movie-grid">
                {filtered.map((movie) => (
                  <MovieCard 
                    key={`featured-${movie.id}`}
                    movie={movie} 
                    commentCounts={commentCounts} 
                    onClick={onMovieClick}
                  />
                ))}
              </div>
            ) : (
              <div className="no-results">Không tìm thấy phim phù hợp với bộ lọc</div>
            );
          })()}
        </section>
      )}

      {/* New Releases */}
      {!isSearching && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">🆕 Phim Mới Cập Nhật</h2>
          </div>
          {loadingSections.new ? (
            <MovieGridSkeleton count={12} />
          ) : newMovies.length === 0 ? (
            <div className="no-results">Chưa có phim mới</div>
          ) : (() => {
            const filtered = filterMovies(newMovies).slice(0, 12);
            return filtered.length > 0 ? (
              <div className="movie-grid">
                {filtered.map((movie) => (
                  <MovieCard 
                    key={`new-${movie.id}`}
                    movie={movie} 
                    commentCounts={commentCounts} 
                    onClick={onMovieClick}
                  />
                ))}
              </div>
            ) : (
              <div className="no-results">Không tìm thấy phim phù hợp với bộ lọc</div>
            );
          })()}
        </section>
      )}

      {/* Top Rated */}
      {!isSearching && (
        <section className="movie-section">
          <div className="section-header">
            <h2 className="section-title">⭐ Điểm Cao Nhất</h2>
          </div>
          {loadingSections.topRated ? (
            <MovieGridSkeleton count={12} />
          ) : topRatedMovies.length === 0 ? (
            <div className="no-results">Chưa có phim</div>
          ) : (() => {
            const filtered = filterMovies(topRatedMovies).slice(0, 12);
            return filtered.length > 0 ? (
              <div className="movie-grid">
                {filtered.map((movie) => (
                  <MovieCard 
                    key={`toprated-${movie.id}`}
                    movie={movie} 
                    commentCounts={commentCounts} 
                    onClick={onMovieClick}
                  />
                ))}
              </div>
            ) : (
              <div className="no-results">Không tìm thấy phim phù hợp với bộ lọc</div>
            );
          })()}
        </section>
      )}
    </div>
  );
}
