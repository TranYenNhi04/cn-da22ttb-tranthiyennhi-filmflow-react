import React, { useEffect, useState, useRef } from 'react';
import './HomePage.css';
import { API_BASE } from '../config';
import { MovieGridSkeleton, SectionSkeleton } from '../components/MovieSkeleton';

function MovieCard({ movie, commentCounts, onClick }) {
  const poster = movie.poster_url || movie.poster_path || movie.poster;
  return (
    <div className="movie-card" onClick={() => onClick && onClick(movie)}>
      <div className="movie-thumb">
        {poster ? (
          <img 
            src={poster} 
            alt={movie.title} 
            loading="lazy" 
            decoding="async"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = `https://picsum.photos/seed/${movie.id || movie.title}/300/450`;
            }}
          />
        ) : (
          <div className="no-poster">Không có poster</div>
        )}
        <div className="movie-overlay">
          <div className="overlay-content">
            <h3 className="movie-title">{movie.title}</h3>
            <div className="movie-meta">
              <span className="year">{movie.year}</span>
              <span className="rating">⭐ {movie.vote_average || 'N/A'}</span>
              <span className="comments">💬 {commentCounts && (commentCounts[movie.id] || 0)}</span>
            </div>
            <div className="movie-actions">
              <button className="btn-play" onClick={(e) => { e.stopPropagation(); onClick && onClick(movie); }}>
                ▶ Xem phim
              </button>
            </div>
          </div>
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
  const [loading, setLoading] = useState(false);
  const [loadingSections, setLoadingSections] = useState({
    trending: true,
    featured: true,
    topRated: true,
    new: true
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
          const response = await fetch(`${API_BASE}/movies/autocomplete?q=${encodeURIComponent(query)}&n=20`);
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
    'action': ['action', 'hành động'],
    'comedy': ['comedy', 'hài'],
    'drama': ['drama', 'chính kịch'],
    'horror': ['horror', 'kinh dị'],
    'romance': ['romance', 'lãng mạn']
  };

  const filterMovies = (movies) => {
    let filtered = [...movies];
    
    // Genre filter - match both English and Vietnamese names
    if (genreFilter !== 'all') {
      const targetGenres = genreMap[genreFilter.toLowerCase()] || [genreFilter.toLowerCase()];
      filtered = filtered.filter(m => {
        try {
          let genres = m.genres;
          if (typeof genres === 'string') {
            genres = JSON.parse(genres);
          }
          if (Array.isArray(genres)) {
            const genreNames = genres.map(g => {
              if (typeof g === 'string') return g.toLowerCase();
              if (g.name) return g.name.toLowerCase();
              return '';
            });
            // Check if any genre name matches any target genre
            return genreNames.some(gn => 
              targetGenres.some(tg => gn.includes(tg) || tg.includes(gn))
            );
          }
          return false;
        } catch (e) {
          console.warn('Genre parse error:', e);
          return false;
        }
      });
    }
    
    // Year filter
    if (yearFilter !== 'all') {
      if (yearFilter === '2024') {
        filtered = filtered.filter(m => m.year >= 2024);
      } else if (yearFilter === '2023') {
        filtered = filtered.filter(m => m.year === 2023);
      } else if (yearFilter === '2020-2022') {
        filtered = filtered.filter(m => m.year >= 2020 && m.year <= 2022);
      } else if (yearFilter === 'older') {
        filtered = filtered.filter(m => m.year < 2020);
      }
    }
    
    // Sorting
    if (sortBy === 'rating') {
      filtered.sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0));
    } else if (sortBy === 'newest') {
      filtered.sort((a, b) => (b.year || 0) - (a.year || 0));
    } else if (sortBy === 'title') {
      filtered.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    }
    
    return filtered;
  };

  useEffect(() => {
    const fetchMovies = async () => {
      const storedUser = localStorage.getItem('user');
      const userId = storedUser ? JSON.parse(storedUser)?.userId : null;
      
      // INSTANT DISPLAY: Load from cache FIRST, show immediately
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
              setLoadingSections(prev => ({ ...prev, trending: false }));
            }
          } catch (e) {}
        }
        
        // Load featured from cache instantly
        const cacheKey = `cached_recs_collaborative_${userId || 'public'}`;
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
              setLoadingSections(prev => ({ ...prev, featured: false, topRated: false }));
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
              setLoadingSections(prev => ({ ...prev, new: false }));
            }
          } catch (e) {}
        }
      } catch (e) {
        console.warn('Cache load failed:', e);
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
        fetch(`${API_BASE}/recommendations?rec_type=collaborative&n=50`)
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
              
              // Filter out movies that are already in trending to avoid duplicates
              const trendingIds = new Set(trendingMovies.map(m => m.id));
              const uniqueMovies = movies.filter(m => !trendingIds.has(m.id));
              
              // Split into sections ensuring no overlap
              const featured = uniqueMovies.filter(m => m.vote_average >= 7).slice(0, 6);
              const featuredIds = new Set(featured.map(m => m.id));
              
              // Top rated - exclude trending and featured
              const topRated = [...uniqueMovies]
                .filter(m => !featuredIds.has(m.id))
                .sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0))
                .slice(0, 12);
              
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
      // Fetch user data
      if (userId) {
        try {
          const [historyRes, watchlistRes] = await Promise.all([
            fetch(`${API_BASE}/watch-history/${userId}`),
            fetch(`${API_BASE}/watchlist/${userId}`)
          ]);
          
          if (historyRes.ok) {
            const data = await historyRes.json();
            const history = data.movies || data.history || [];
            
            // Deduplicate by movieId - keep only most recent entry for each movie
            const uniqueHistory = [];
            const seenMovieIds = new Set();
            history.forEach(entry => {
              if (!seenMovieIds.has(entry.movieId)) {
                seenMovieIds.add(entry.movieId);
                uniqueHistory.push(entry);
              }
            });
            
            setWatchHistory(uniqueHistory);
          }
          if (watchlistRes.ok) {
            const data = await watchlistRes.json();
            const watchlistData = data.movies || data.watchlist || [];
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
      fetch(`${API_BASE}/movies/new-releases?limit=30`)
        .then(newRes => newRes.ok ? newRes.json() : null)
        .then(data => {
          if (data) {
            const movies = data.movies || [];
            setNewMovies(movies);
            setLoadingSections(prev => ({ ...prev, new: false }));
            
            // Cache for instant display next time
            try {
              localStorage.setItem('cached_new_releases', JSON.stringify({ movies, ts: Date.now() }));
            } catch (e) {}
            
            if (movies.length > 0) {
              fetchCommentCounts(movies);
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
              heroMovies.map((movie, idx) => (
                <div key={idx} className="hero-poster-item" style={{ animationDelay: `${idx * 0.1}s` }}>
                  <img 
                    src={movie.poster_url || movie.poster_path || `https://picsum.photos/seed/${movie.id}/300/450`} 
                    alt={movie.title}
                    loading="lazy"
                  />
                </div>
              ))
            ) : (
              // Placeholder gradient boxes while loading
              Array.from({ length: 20 }).map((_, idx) => (
                <div key={idx} className="hero-poster-item placeholder" style={{ animationDelay: `${idx * 0.1}s` }} />
              ))
            )}
          </div>
          <div className="hero-gradient-overlay" />
        </div>
        
        {/* Hero Content */}
        <div className="hero-overlay">
          <h1 className="hero-title">
            <span className="hero-title-main">Khám phá thế giới điện ảnh</span>
            <span className="hero-title-sub">Không giới hạn</span>
          </h1>
          <p className="hero-subtitle">Hàng nghìn bộ phim, series hot đang chờ bạn</p>
          <p className="hero-description">Chất lượng HD/4K cao cấp • Cập nhật liên tục mỗi ngày • Xem mọi lúc mọi nơi</p>
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
              <option value="action">Hành động</option>
              <option value="comedy">Hài</option>
              <option value="drama">Chính kịch</option>
              <option value="horror">Kinh dị</option>
              <option value="romance">Lãng mạn</option>
            </select>
          </div>

          <div className="filter-group">
            <select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)} className="filter-select">
              <option value="all">Tất cả năm</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2020-2022">2020-2022</option>
              <option value="older">Trước 2020</option>
            </select>
          </div>

          <div className="filter-group">
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="filter-select">
              <option value="rating">Đánh giá cao</option>
              <option value="newest">Mới nhất</option>
              <option value="title">Tên A-Z</option>
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
              {searchResults.map((movie, idx) => (
                <MovieCard 
                  key={idx} 
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
              const movie = allMovies.find(m => m.id === entry.movieId);
              return movie ? (
                <MovieCard 
                  key={entry.movieId} 
                  movie={movie} 
                  commentCounts={commentCounts} 
                  onClick={onMovieClick}
                />
              ) : null;
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
                {filtered.map((movie, idx) => (
                  <MovieCard 
                    key={idx} 
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
                {filtered.map((movie, idx) => (
                  <MovieCard 
                    key={idx} 
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
                {filtered.map((movie, idx) => (
                  <MovieCard 
                    key={idx} 
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
                {filtered.map((movie, idx) => (
                  <MovieCard 
                    key={idx} 
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
