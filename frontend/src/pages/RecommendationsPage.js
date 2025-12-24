import React, { useState, useEffect } from 'react';
import styles from './RecommendationsPage.module.css';
import { API_BASE } from '../config';
import { MovieCardSkeleton } from '../components/MovieSkeleton';

export default function RecommendationsPage({ onBack, initialMovie }) {
    const [recType] = useState('hybrid');
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [movieHistory, setMovieHistory] = useState([]); // Stack of viewed movies
    const [similarMoviesCache, setSimilarMoviesCache] = useState({}); // Cache similar movies by movie ID
    const [likes, setLikes] = useState({}); // Track liked movies
    const [dislikes, setDislikes] = useState({}); // Track disliked movies
    const [watchlist, setWatchlist] = useState({}); // Track watchlist movies
    const [reviewRating, setReviewRating] = useState(0); // Review rating (1-5)
    const [comments, setComments] = useState([]);
    const [commentText, setCommentText] = useState('');
    const [showAllComments, setShowAllComments] = useState(false);
    const [hoverRating, setHoverRating] = useState(0); // Hover rating for preview
    const [videoProgress, setVideoProgress] = useState({}); // Track video progress {movieId: {timestamp, duration}}
    const [player, setPlayer] = useState(null); // YouTube player instance
    const playerRef = React.useRef(null);
    
    const currentMovie = movieHistory.length > 0 ? movieHistory[movieHistory.length - 1] : null;
    const similarMovies = currentMovie ? (similarMoviesCache[currentMovie.id] || []) : [];

    // Load saved video progress from localStorage
    useEffect(() => {
        try {
            const saved = localStorage.getItem('video_progress');
            if (saved) {
                setVideoProgress(JSON.parse(saved));
            }
        } catch (e) {
            console.warn('Failed to load video progress:', e);
        }
    }, []);

    // Load watchlist from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            if (user?.userId) {
                const cacheKey = `watchlist_${user.userId}`;
                const cached = localStorage.getItem(cacheKey);
                if (cached) {
                    const watchlistData = JSON.parse(cached);
                    const watchlistMap = {};
                    watchlistData.forEach(movie => {
                        watchlistMap[movie.id] = true;
                    });
                    setWatchlist(watchlistMap);
                }
                
                // Load likes/dislikes from cache on mount
                const likesCacheKey = `likes_cache_${user.userId}`;
                const likesCache = localStorage.getItem(likesCacheKey);
                if (likesCache) {
                    const likesMap = JSON.parse(likesCache);
                    const newLikes = {};
                    const newDislikes = {};
                    Object.keys(likesMap).forEach(movieId => {
                        const action = likesMap[movieId];
                        if (action === 'like') {
                            newLikes[movieId] = true;
                            newDislikes[movieId] = false;
                        } else if (action === 'dislike') {
                            newDislikes[movieId] = true;
                            newLikes[movieId] = false;
                        }
                    });
                    setLikes(newLikes);
                    setDislikes(newDislikes);
                }
            }
        } catch (e) {
            console.warn('Failed to load user state:', e);
        }
    }, []);

    // Load initial movie if provided (from HomePage click)
    useEffect(() => {
        if (initialMovie) {
            // If history is empty or last movie differs, open the initial movie
            const last = movieHistory.length > 0 ? movieHistory[movieHistory.length - 1] : null;
            if (!last || last.id !== initialMovie.id) {
                openMovie(initialMovie);
            }
        }
    }, [initialMovie]);

    const getYouTubeEmbedUrl = (url) => {
        if (!url) return null;
        
        // Nếu là embed URL, trả về trực tiếp
        if (url.includes('/embed')) {
            // Nếu backend trả về URL embed, chuyển hostname sang youtube-nocookie để giảm khả năng bị block
            try {
                const u = new URL(url);
                u.hostname = u.hostname.replace('www.youtube.com', 'www.youtube-nocookie.com').replace('youtube.com', 'www.youtube-nocookie.com');
                return u.toString();
            } catch (e) {
                return url;
            }
        }
        
        // Nếu là watch URL, extract video ID
        try {
            const urlObj = new URL(url);
            if (urlObj.hostname.includes('youtube.com') || urlObj.hostname.includes('www.youtube.com')) {
                const videoId = urlObj.searchParams.get('v');
                if (videoId) return `https://www.youtube-nocookie.com/embed/${videoId}`;
            }
            if (urlObj.hostname.includes('youtu.be')) {
                const videoId = urlObj.pathname.slice(1).split('?')[0];
                if (videoId) return `https://www.youtube-nocookie.com/embed/${videoId}`;
            }
        } catch (e) {
            console.error('Error parsing YouTube URL:', e);
            return null;
        }
        return null;
    };

    const isSearchEmbed = (url) => {
        if (!url) return false;
        try {
            const u = new URL(url);
            const params = u.searchParams;
            if (params.get('listType') === 'search') return true;
            // if it's an embed without a video id and contains 'list=' it's likely a search/embed playlist
            if (u.pathname && u.pathname.includes('/embed') && params.get('list')) return true;
            return false;
        } catch (e) {
            return false;
        }
    };

    // Save video progress to localStorage and backend
    const saveVideoProgress = async (movieId, timestamp, duration) => {
        if (!movieId || timestamp === null || timestamp === undefined) return;
        
        // Save to state and localStorage
        const newProgress = {
            ...videoProgress,
            [movieId]: { timestamp: Math.floor(timestamp), duration: Math.floor(duration || 0), savedAt: Date.now() }
        };
        setVideoProgress(newProgress);
        
        try {
            localStorage.setItem('video_progress', JSON.stringify(newProgress));
        } catch (e) {
            console.warn('Failed to save progress to localStorage:', e);
        }
        
        // Save to backend watch history
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            const userId = user?.userId || 'Anonymous';
            
            await fetch(`${API_BASE}/watch-history`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    movie_id: movieId,
                    timestamp: Math.floor(timestamp),
                    duration: Math.floor(duration || 0)
                })
            });
        } catch (e) {
            console.warn('Failed to save progress to backend:', e);
        }
    };

    const openMovie = async (movie) => {
        console.debug('openMovie called for', movie && movie.id, movie && movie.title);

        // Create a unique id for this history entry so we can update it later
        const historyId = `${Date.now()}-${Math.floor(Math.random() * 100000)}`;

        // Push a placeholder entry into history immediately so UI shows right away
        const placeholder = {
            ...movie,
            video_url: movie.video_url || null,
            poster_url: movie.poster_url || null,
            loadingTrailer: !movie.video_url,
            historyId,
        };

        setMovieHistory(prev => ([...prev, placeholder]));

        // Record a view interaction for personalization (best-effort)
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            if (user && user.userId) {
                fetch(`${API_BASE}/interactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ userId: user.userId, movieId: movie.id, action: 'view' })
                }).catch(()=>{});
            }
        } catch (e) {}

        // Fetch user's last interaction for this movie to restore like/dislike state
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            if (user && user.userId) {
                // Check watchlist status from localStorage
                try {
                    const cacheKey = `watchlist_${user.userId}`;
                    const cached = localStorage.getItem(cacheKey);
                    if (cached) {
                        const watchlistData = JSON.parse(cached);
                        const isInWatchlist = watchlistData.some(m => m.id === movie.id);
                        setWatchlist(prev => ({ ...prev, [movie.id]: isInWatchlist }));
                    }
                } catch (e) {
                    console.warn('Failed to check watchlist status:', e);
                }

                // Check local cache first
                try {
                    const cacheKey = `likes_cache_${user.userId}`;
                    const raw = localStorage.getItem(cacheKey);
                    if (raw) {
                        const map = JSON.parse(raw);
                        if (map && map[movie.id]) {
                            const action = map[movie.id];
                            if (action === 'like') {
                                setLikes(prev => ({ ...prev, [movie.id]: true }));
                                setDislikes(prev => ({ ...prev, [movie.id]: false }));
                            } else if (action === 'dislike') {
                                setDislikes(prev => ({ ...prev, [movie.id]: true }));
                                setLikes(prev => ({ ...prev, [movie.id]: false }));
                            }
                            // skip remote fetch when cached
                            return;
                        }
                    }
                } catch (e) {
                    // ignore cache failures
                }

                // remote fetch with limit=1 for speed
                fetch(`${API_BASE}/interactions?user_id=${encodeURIComponent(user.userId)}&movie_id=${movie.id}&limit=1`)
                    .then(res => res.ok ? res.json() : null)
                    .then(data => {
                        if (data && data.results && data.results.length > 0) {
                            const last = data.results[0];
                            if (last.action === 'like') {
                                setLikes(prev => ({ ...prev, [movie.id]: true }));
                                setDislikes(prev => ({ ...prev, [movie.id]: false }));
                                // update cache
                                try {
                                    const cacheKey = `likes_cache_${user.userId}`;
                                    const raw = localStorage.getItem(cacheKey);
                                    const map = raw ? JSON.parse(raw) : {};
                                    map[movie.id] = 'like';
                                    localStorage.setItem(cacheKey, JSON.stringify(map));
                                } catch (e) {}
                            } else if (last.action === 'dislike') {
                                setDislikes(prev => ({ ...prev, [movie.id]: true }));
                                setLikes(prev => ({ ...prev, [movie.id]: false }));
                                try {
                                    const cacheKey = `likes_cache_${user.userId}`;
                                    const raw = localStorage.getItem(cacheKey);
                                    const map = raw ? JSON.parse(raw) : {};
                                    map[movie.id] = 'dislike';
                                    localStorage.setItem(cacheKey, JSON.stringify(map));
                                } catch (e) {}
                            }
                        }
                    }).catch(()=>{});
            }
        } catch (e) {}

        // Fetch and update trailer/poster asynchronously if we don't already have a video
        if (!movie.video_url) {
            try {
                const resp = await fetch(`${API_BASE}/movies/${movie.id}/trailer`);
                console.debug('trailer endpoint response status', resp.status);
                if (resp.ok) {
                    const data = await resp.json();
                    console.debug('trailer endpoint data', data);
                    // Update the history entry by historyId
                    setMovieHistory(prev => prev.map(entry => {
                        if (entry.historyId === historyId) {
                            return {
                                ...entry,
                                video_url: data?.video_url || entry.video_url,
                                poster_url: data?.poster_url || entry.poster_url,
                                loadingTrailer: false,
                            };
                        }
                        return entry;
                    }));
                } else {
                    // still mark as not loading and provide fallback
                    setMovieHistory(prev => prev.map(entry => entry.historyId === historyId ? ({...entry, loadingTrailer: false}) : entry));
                }
            } catch (err) {
                console.error('Failed to fetch trailer endpoint:', err);
                setMovieHistory(prev => prev.map(entry => entry.historyId === historyId ? ({...entry, loadingTrailer: false}) : entry));
            }

            // If after the fetch there's still no video_url, set a YouTube search URL fallback (but don't embed it)
            setMovieHistory(prev => prev.map(entry => {
                if (entry.historyId !== historyId) return entry;
                if (entry.video_url) return entry;
                try {
                    const title = entry.title || '';
                    const year = entry.year ? ` ${entry.year}` : '';
                    const query = encodeURIComponent(`${title}${year} trailer`);
                    return {
                        ...entry,
                        // store a search URL (we will open it in new tab rather than embedding)
                        video_url: `https://www.youtube.com/results?search_query=${query}`
                    };
                } catch (e) {
                    return entry;
                }
            }));
        }

        // Fetch similar movies in background (non-blocking)
        if (!similarMoviesCache[movie.id]) {
            fetch(`${API_BASE}/recommendations?rec_type=content&movie_id=${movie.id}&n=10`)
                .then(response => response.ok ? response.json() : null)
                .then(data => {
                    if (data && data.results) {
                        setSimilarMoviesCache(prev => ({
                            ...prev,
                            [movie.id]: data.results
                        }));
                    }
                })
                .catch(err => console.error('Failed to fetch similar movies:', err));
        }

        // Fetch latest comments for this movie (background)
        try {
            fetch(`${API_BASE}/movies/${movie.id}/comments?limit=20`)
                .then(res => res.ok ? res.json() : null)
                .then(data => {
                    if (data && data.comments) {
                        setComments(data.comments);
                        setShowAllComments(false);
                    }
                }).catch(()=>{});
        } catch (e) {}
    };

    const handleLike = async () => {
        if (!currentMovie) return;
        try {
            // Persist interaction to server with userId
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            if (user && user.userId) {
                await fetch(`${API_BASE}/interactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ userId: user.userId, movieId: currentMovie.id, action: 'like' })
                });
            } else {
                await fetch(`${API_BASE}/movies/${currentMovie.id}/like`, { method: 'POST' });
            }
            const movieId = currentMovie.id;
            const isCurrentlyLiked = likes[movieId];
            
            setLikes(prev => ({ ...prev, [movieId]: !isCurrentlyLiked }));
            // If clicking like, remove dislike
            if (!isCurrentlyLiked) {
                setDislikes(prev => ({ ...prev, [movieId]: false }));
                
                // Save to cache
                if (user && user.userId) {
                    try {
                        const cacheKey = `likes_cache_${user.userId}`;
                        const raw = localStorage.getItem(cacheKey);
                        const map = raw ? JSON.parse(raw) : {};
                        map[movieId] = 'like';
                        localStorage.setItem(cacheKey, JSON.stringify(map));
                    } catch (e) {
                        console.warn('Failed to save like cache:', e);
                    }
                }
            } else {
                // Remove from cache if toggling off
                if (user && user.userId) {
                    try {
                        const cacheKey = `likes_cache_${user.userId}`;
                        const raw = localStorage.getItem(cacheKey);
                        const map = raw ? JSON.parse(raw) : {};
                        delete map[movieId];
                        localStorage.setItem(cacheKey, JSON.stringify(map));
                    } catch (e) {
                        console.warn('Failed to update like cache:', e);
                    }
                }
            }
        } catch (err) {
            console.error('Failed to like movie:', err);
        }
    };

    const handleDislike = async () => {
        if (!currentMovie) return;
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            if (user && user.userId) {
                await fetch(`${API_BASE}/interactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ userId: user.userId, movieId: currentMovie.id, action: 'dislike' })
                });
            } else {
                await fetch(`${API_BASE}/movies/${currentMovie.id}/dislike`, { method: 'POST' });
            }
            const movieId = currentMovie.id;
            const isCurrentlyDisliked = dislikes[movieId];
            
            setDislikes(prev => ({ ...prev, [movieId]: !isCurrentlyDisliked }));
            // If clicking dislike, remove like
            if (!isCurrentlyDisliked) {
                setLikes(prev => ({ ...prev, [movieId]: false }));
                
                // Save to cache
                if (user && user.userId) {
                    try {
                        const cacheKey = `likes_cache_${user.userId}`;
                        const raw = localStorage.getItem(cacheKey);
                        const map = raw ? JSON.parse(raw) : {};
                        map[movieId] = 'dislike';
                        localStorage.setItem(cacheKey, JSON.stringify(map));
                    } catch (e) {
                        console.warn('Failed to save dislike cache:', e);
                    }
                }
            } else {
                // Remove from cache if toggling off
                if (user && user.userId) {
                    try {
                        const cacheKey = `likes_cache_${user.userId}`;
                        const raw = localStorage.getItem(cacheKey);
                        const map = raw ? JSON.parse(raw) : {};
                        delete map[movieId];
                        localStorage.setItem(cacheKey, JSON.stringify(map));
                    } catch (e) {
                        console.warn('Failed to update dislike cache:', e);
                    }
                }
            }
        } catch (err) {
            console.error('Failed to dislike movie:', err);
        }
    };

    const handleWatchlist = async () => {
        if (!currentMovie) return;
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            const userId = user?.userId || 'Anonymous';
            
            const isInWatchlist = watchlist[currentMovie.id];
            const action = isInWatchlist ? 'remove_from_watchlist' : 'add_to_watchlist';
            
            await fetch(`${API_BASE}/watchlist`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    userId: userId, 
                    movieId: currentMovie.id, 
                    action: action 
                })
            });
            
            setWatchlist(prev => ({ ...prev, [currentMovie.id]: !isInWatchlist }));
            
            // Update localStorage cache
            try {
                const cacheKey = `watchlist_${userId}`;
                const cached = localStorage.getItem(cacheKey);
                let watchlistData = cached ? JSON.parse(cached) : [];
                
                if (isInWatchlist) {
                    watchlistData = watchlistData.filter(m => m.id !== currentMovie.id);
                } else {
                    watchlistData.push(currentMovie);
                }
                
                localStorage.setItem(cacheKey, JSON.stringify(watchlistData));
            } catch (e) {
                console.warn('Failed to update watchlist cache:', e);
            }
        } catch (err) {
            console.error('Failed to update watchlist:', err);
        }
    };

    // Quick submit rating (1-5 sao) without opening modal
    const handleRate = async (star) => {
        if (!currentMovie) return;
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            const payload = {
                rating: star,
                review_text: '',
                username: user && user.userId ? user.userId : 'Anonymous'
            };
            const response = await fetch(`${API_BASE}/movies/${currentMovie.id}/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (response.ok) {
                setReviewRating(star);
                alert('Cảm ơn bạn đã đánh giá!');
            } else {
                alert('Gửi đánh giá thất bại');
            }
        } catch (err) {
            console.error('Failed to submit rating:', err);
            alert('Lỗi khi gửi đánh giá. Vui lòng thử lại!');
        }
    };

    const handleSubmitComment = async () => {
        if (!currentMovie) return;
        try {
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            const payload = {
                userId: user && user.userId ? user.userId : 'Anonymous',
                comment: commentText || ''
            };
            // If we have a registered display name locally, ensure server has the user metadata
            if (user && user.userId && (user.name || user.email)) {
                try {
                    await fetch(`${API_BASE}/users`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ userId: user.userId, metadata: JSON.stringify({ name: user.name, email: user.email }) })
                    });
                } catch (e) {
                    // best-effort - ignore errors
                }
            }
            if (!payload.comment.trim()) {
                alert('Vui lòng nhập bình luận');
                return;
            }
            const resp = await fetch(`${API_BASE}/movies/${currentMovie.id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (resp.ok) {
                const data = await resp.json();
                // prepend local comment to list and include display_name for immediate UI
                const displayName = (user && (user.name || user.displayName)) || payload.userId;
                setComments(prev => ([{ id: Date.now(), movieId: currentMovie.id, userId: payload.userId, display_name: displayName, comment: payload.comment, timestamp: new Date().toISOString() }, ...prev]));
                setCommentText('');
            } else {
                alert('Gửi bình luận thất bại');
            }
        } catch (e) {
            console.error('Failed to submit comment', e);
            alert('Lỗi khi gửi bình luận');
        }
    };

    const goBack = () => {
        if (movieHistory.length > 1) {
            // Remove current movie from history
            const newHistory = [...movieHistory];
            newHistory.pop();
            setMovieHistory(newHistory);
        } else if (movieHistory.length === 1) {
            // Return to recommendations list
            setMovieHistory([]);
        }
    };

    // Movie card component
    const MovieCard = ({ movie, isCompact }) => {
        return (
            <div className={isCompact ? styles.movieCardCompact : styles.movieCard} onClick={() => openMovie(movie)}>
                <div className={styles.moviePosterContainer}>
                    {movie.poster_url ? (
                        <img src={movie.poster_url} alt={movie.title} className={styles.moviePoster} loading="lazy" />
                    ) : (
                        <div className={styles.moviePosterPlaceholder}><p>Không có Poster</p></div>
                    )}
                    <div className={styles.playOverlay}>▶</div>
                </div>
                <div className={styles.movieDetails}>
                    <h3 className={styles.movieTitle}>{movie.title} {movie.year > 0 && `(${movie.year})`}</h3>
                    <p className={styles.rating}>⭐ {movie.vote_average || 'N/A'}/10</p>
                    {!isCompact && <p className={styles.overview}>{movie.overview?.substring(0, 100)}...</p>}
                </div>
            </div>
        );
    };

    const handleGetRecommendations = async () => {
        setLoading(true);
        setError('');
        setRecommendations([]);

        try {
            // Fast-path: load from cache first to render immediately
            const stored = localStorage.getItem('user');
            const user = stored ? JSON.parse(stored) : null;
            const cacheKey = `cached_recs_${recType}_${user && user.userId ? user.userId : 'public'}`;
            try {
                const raw = localStorage.getItem(cacheKey);
                if (raw) {
                    const parsed = JSON.parse(raw);
                    const movies = parsed.results || [];
                    if (movies.length > 0) {
                        setRecommendations(movies);
                        setLoading(false);
                    }
                }
            } catch (e) {}

            const userParam = user && user.userId ? `&user_id=${encodeURIComponent(user.userId)}` : '';
            const url = `${API_BASE}/recommendations?rec_type=${encodeURIComponent(recType)}&n=10${userParam}`;
            const response = await fetch(url);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Lỗi lấy gợi ý: ${response.status} - ${errorText.substring(0, 200)}`);
            }
            const data = await response.json();
            const results = data.results || [];
            // update UI and cache
            setRecommendations(results);
            try {
                localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), results }));
            } catch (e) {}
            if (results.length === 0) setError('Không tìm thấy gợi ý nào.');
        } catch (err) {
            setError(`Thất bại khi kết nối: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { handleGetRecommendations(); }, []);

    // Load YouTube IFrame API
    useEffect(() => {
        if (!window.YT) {
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        }
    }, []);

    // Auto-save progress every 10 seconds when playing
    useEffect(() => {
        if (!currentMovie || !player) return;
        
        const interval = setInterval(() => {
            try {
                if (player && typeof player.getCurrentTime === 'function' && typeof player.getDuration === 'function') {
                    const currentTime = player.getCurrentTime();
                    const duration = player.getDuration();
                    if (currentTime > 0 && duration > 0) {
                        saveVideoProgress(currentMovie.id, currentTime, duration);
                    }
                }
            } catch (e) {
                // Player might not be ready
            }
        }, 10000); // Save every 10 seconds
        
        return () => clearInterval(interval);
    }, [currentMovie, player]);

    // Save progress when user leaves page
    useEffect(() => {
        const handleBeforeUnload = () => {
            if (currentMovie && player) {
                try {
                    const currentTime = player.getCurrentTime();
                    const duration = player.getDuration();
                    if (currentTime > 0) {
                        saveVideoProgress(currentMovie.id, currentTime, duration);
                    }
                } catch (e) {}
            }
        };
        
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [currentMovie, player]);

    return (
        <div className={styles.mainContent}>
            {!currentMovie ? (
                <>
                    <header className={styles.header}>
                        <h1 className={styles.pageHeader}>⭐ Đề Xuất Phim Cho Bạn</h1>
                    </header>

                    {error && <div className={styles.error}>{error}</div>}
                    {loading && recommendations.length === 0 && (
                        <div className={styles.recommendationsContainer}>
                            <div className={styles.skeletonTitle}></div>
                            <div className={styles.movieRow}>
                                {Array.from({length: 6}).map((_, i) => (
                                    <div key={i} className={styles.movieCardSkeleton}>
                                        <div className={styles.skeletonPoster}></div>
                                        <div className={styles.skeletonText}></div>
                                        <div className={styles.skeletonText} style={{width: '60%'}}></div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {recommendations.length > 0 && (
                        <div className={styles.recommendationsContainer}>
                            <h2 className={styles.rowTitle}>🎬 Đề xuất hàng đầu ({recommendations.length})</h2>
                            <div className={styles.movieRow}>
                                {recommendations.map((movie, idx) => (<MovieCard key={idx} movie={movie} />))}
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <div className={styles.moviePlayerContainer}>
                    <button className={styles.backButton} onClick={goBack}>
                        ← Quay lại
                    </button>
                    
                    <div className={styles.playerSection}>
                        <div className={styles.videoPlayer}>
                            {(() => {
                                const embed = currentMovie.video_url ? (getYouTubeEmbedUrl(currentMovie.video_url) || currentMovie.video_url) : null;
                                const searchEmbed = embed ? isSearchEmbed(embed) : false;
                                // If we have a proper embed and it's not a search-type embed, show iframe
                                if (embed && !searchEmbed && embed.includes('/embed')) {
                                    const sep = embed.includes('?') ? '&' : '?';
                                    const savedProgress = videoProgress[currentMovie.id];
                                    const startTime = savedProgress?.timestamp > 5 ? savedProgress.timestamp : 0;
                                    const startParam = startTime > 0 ? `&start=${startTime}` : '';
                                    
                                    return (
                                        <iframe
                                            id={`youtube-player-${currentMovie.id}`}
                                            width="100%"
                                            height="100%"
                                            title={currentMovie.title}
                                            frameBorder="0"
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                                            allowFullScreen
                                            referrerPolicy="strict-origin-when-cross-origin"
                                            src={`${embed}${sep}autoplay=1&mute=0&rel=0&modestbranding=1&enablejsapi=1${startParam}`}
                                            onLoad={() => {
                                                // Wait for YouTube IFrame API to be ready before initializing
                                                const initPlayer = () => {
                                                    if (window.YT && window.YT.Player) {
                                                        try {
                                                            const ytPlayer = new window.YT.Player(`youtube-player-${currentMovie.id}`, {
                                                                events: {
                                                                    'onReady': (event) => {
                                                                        console.log('YouTube player ready');
                                                                        setPlayer(event.target);
                                                                        playerRef.current = event.target;
                                                                        // Seek to saved position if available
                                                                        if (startTime > 5) {
                                                                            setTimeout(() => {
                                                                                try {
                                                                                    event.target.seekTo(startTime, true);
                                                                                } catch (e) {
                                                                                    console.warn('Failed to seek:', e);
                                                                                }
                                                                            }, 1000);
                                                                        }
                                                                        
                                                                        // Auto-save progress every 10 seconds
                                                                        const saveInterval = setInterval(() => {
                                                                            try {
                                                                                const player = playerRef.current;
                                                                                if (player && typeof player.getCurrentTime === 'function') {
                                                                                    const currentTime = player.getCurrentTime();
                                                                                    const duration = player.getDuration();
                                                                                    if (currentTime > 0) {
                                                                                        saveVideoProgress(currentMovie.id, currentTime, duration);
                                                                                    }
                                                                                }
                                                                            } catch (e) {}
                                                                        }, 10000);
                                                                        
                                                                        // Clear interval when player is destroyed
                                                                        return () => clearInterval(saveInterval);
                                                                    },
                                                                    'onStateChange': (event) => {
                                                                        // Save when paused
                                                                        if (event.data === window.YT.PlayerState.PAUSED) {
                                                                            try {
                                                                                const currentTime = event.target.getCurrentTime();
                                                                                const duration = event.target.getDuration();
                                                                                saveVideoProgress(currentMovie.id, currentTime, duration);
                                                                            } catch (e) {}
                                                                        }
                                                                    }
                                                                }
                                                            });
                                                        } catch (e) {
                                                            console.warn('Failed to initialize YouTube player:', e);
                                                        }
                                                    } else {
                                                        // YT API not ready yet, try again in 500ms
                                                        setTimeout(initPlayer, 500);
                                                    }
                                                };
                                                
                                                // Start initialization with slight delay to ensure iframe is ready
                                                setTimeout(initPlayer, 200);
                                            }}
                                        />
                                    );
                                }

                                // Otherwise show poster with message + button to open YouTube search
                                if (currentMovie.poster_url) {
                                    return (
                                        <div className={styles.noPoster}>
                                            <img src={currentMovie.poster_url} alt={currentMovie.title} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
                                            <div className={styles.noVideoOverlay}>
                                                {currentMovie.loadingTrailer ? 'Đang tải phim...' : 'Trailer không khả dụng'}
                                            </div>
                                            <div style={{position: 'absolute', right: 12, bottom: 12}}>
                                                <button className={styles.openYouTubeBtn} onClick={() => window.open(currentMovie.video_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(currentMovie.title || '')}`, '_blank')}>
                                                    Mở trailer trên YouTube
                                                </button>
                                            </div>
                                        </div>
                                    );
                                }

                                return (
                                    <div className={styles.noVideo}>
                                        {currentMovie.loadingTrailer ? 'Đang tải phim...' : 'Không có trailer'}
                                    </div>
                                );
                            })()}
                        </div>
                        
                        <div className={styles.movieInfo}>
                            <h1 className={styles.movieInfoTitle}>{currentMovie.title} {currentMovie.year > 0 && `(${currentMovie.year})`}</h1>
                            <div className={styles.movieMeta}>
                                <span className={styles.movieRating}>⭐ {currentMovie.vote_average || 'N/A'}/10</span>
                                <span className={styles.movieVotes}>({currentMovie.vote_count || 0} votes)</span>
                            </div>
                            <p className={styles.movieDescription}>{currentMovie.overview}</p>

                            {/* Like/Dislike/Watchlist/Review Buttons */}
                            <div className={styles.interactionButtons}>
                                <button 
                                    className={`${styles.likeBtn} ${likes[currentMovie.id] ? styles.active : ''}`}
                                    onClick={handleLike}
                                    title="Thích phim này"
                                >
                                    👍 Thích
                                </button>
                                <button 
                                    className={`${styles.dislikeBtn} ${dislikes[currentMovie.id] ? styles.active : ''}`}
                                    onClick={handleDislike}
                                    title="Không thích"
                                >
                                    👎 Không thích
                                </button>
                                <button 
                                    className={`${styles.watchlistBtn} ${watchlist[currentMovie.id] ? styles.active : ''}`}
                                    onClick={handleWatchlist}
                                    title={watchlist[currentMovie.id] ? "Xóa khỏi danh sách" : "Lưu vào danh sách"}
                                >
                                    {watchlist[currentMovie.id] ? '✓ Đã lưu' : '+ Lưu'}
                                </button>
                                <div className={styles.ratingInline}>
                                    {[1,2,3,4,5].map(star => (
                                        <button
                                            key={star}
                                            className={`${styles.star} ${(hoverRating || reviewRating) >= star ? styles.starActive : ''}`}
                                            onClick={() => handleRate(star)}
                                            onMouseEnter={() => setHoverRating(star)}
                                            onMouseLeave={() => setHoverRating(0)}
                                            title={`Đánh giá ${star} sao`}
                                        >
                                            ⭐
                                        </button>
                                    ))}
                                </div>
                            </div>
                            {/* Comments section */}
                            <div className={styles.commentsSection}>
                                <h3>Bình luận</h3>
                                <div className={styles.commentForm}>
                                    <textarea value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="Viết bình luận..." rows={3} />
                                    <button className={styles.submitBtn} onClick={handleSubmitComment}>Gửi</button>
                                </div>
                                <div className={styles.commentList}>
                                    {comments.length === 0 && <div>Chưa có bình luận nào.</div>}
                                    {comments.length > 0 && (
                                        (showAllComments ? comments : comments.slice(0, 2)).map(c => (
                                            <div key={c.id} className={styles.commentItem}>
                                                <div className={styles.commentMeta}><strong>{c.display_name || c.userId}</strong> • <span className={styles.commentTime}>{new Date(c.timestamp).toLocaleString()}</span></div>
                                                <div className={styles.commentText}>{c.comment}</div>
                                            </div>
                                        ))
                                    )}

                                    {comments.length > 2 && (
                                        <div className={styles.commentToggle}>
                                            <button className={styles.smallBtn} onClick={() => setShowAllComments(prev => !prev)}>
                                                {showAllComments ? `Rút gọn` : `Xem thêm ${comments.length - 2} bình luận`}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Review modal removed: replaced by quick star rating */}

                    <div className={styles.similarMoviesSection}>
                        <h2 className={styles.sectionTitle}>Gợi ý cho bạn</h2>
                        {similarMovies.length > 0 ? (
                            <div className={styles.similarMoviesGrid}>
                                {similarMovies.map((movie, idx) => (
                                    <MovieCard key={idx} movie={movie} isCompact={true} />
                                ))}
                            </div>
                        ) : (
                            <div className={styles.loadingMovies}>Đang tải...</div>
                        )}
                    </div>
                    <div style={{marginTop: 12}}>
                        <button className={styles.openYouTubeBtn} onClick={() => {
                            const title = currentMovie?.title || '';
                            const year = currentMovie?.year ? ` ${currentMovie.year}` : '';
                            const query = encodeURIComponent(`${title}${year} trailer`);
                            window.open(`https://www.youtube.com/results?search_query=${query}`, '_blank');
                        }}>
                            Mở trailer trên YouTube
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}