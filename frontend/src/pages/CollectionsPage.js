import React, { useState, useEffect } from 'react';
import './CollectionsPage.css';
import { API_BASE } from '../config';
import { MovieCardSkeleton } from '../components/MovieSkeleton';

function MovieCard({ movie, onClick }) {
  const poster = movie.poster_url || movie.poster_path || movie.poster;
  return (
    <div className="collection-movie-card" onClick={() => onClick && onClick(movie)}>
      <div className="collection-movie-thumb">
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
        <div className="collection-overlay">
          <button className="btn-play">▶ Xem ngay</button>
        </div>
      </div>
      <h3>{movie.title}</h3>
      <p className="movie-year">{movie.year}</p>
    </div>
  );
}

export default function CollectionsPage({ onMovieClick }) {
  const [collections] = useState([
    { id: 'best_2024', name: '🏆 Best of 2024', icon: '🏆' },
    { id: 'horror', name: '👻 Horror Collection', icon: '👻' },
    { id: 'action', name: '💥 Action Movies', icon: '💥' },
    { id: 'top_rated', name: '⭐ Top Rated', icon: '⭐' }
  ]);

  const [selectedCollection, setSelectedCollection] = useState('best_2024');
  const [collectionMovies, setCollectionMovies] = useState([]);
  const [collectionInfo, setCollectionInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCollection(selectedCollection);
  }, [selectedCollection]);

  const fetchCollection = async (collectionId) => {
    setLoading(true);
    // Try cache first for instant display
    const cacheKey = `collection_${collectionId}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const data = JSON.parse(cached);
        setCollectionInfo(data);
        setCollectionMovies(data.movies || []);
        setLoading(false);
      } catch (e) {}
    }
    
    try {
      const response = await fetch(`${API_BASE}/collections/${collectionId}?limit=30`);
      if (response.ok) {
        const data = await response.json();
        setCollectionInfo(data);
        setCollectionMovies(data.movies || []);
        // Cache for next time
        try {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        } catch (e) {}
      } else {
        console.error('Failed to fetch collection:', response.status);
        if (!cached) {
          setCollectionInfo(null);
          setCollectionMovies([]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch collection:', error);
      if (!cached) {
        setCollectionInfo(null);
        setCollectionMovies([]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="collections-page">
        {/* Header */}
        <div className="collections-header">
          <h1>🎬 Bộ Sưu Tập Phim</h1>
          <p>Khám phá những bộ sưu tập phim được cố gắng sắp xếp</p>
        </div>

        {/* Collection Tabs */}
        <div className="collections-tabs">
          {collections.map(col => (
            <button
              key={col.id}
              className={`collection-tab ${selectedCollection === col.id ? 'active' : ''}`}
              onClick={() => setSelectedCollection(col.id)}
            >
              <span className="tab-icon">{col.icon}</span>
              <span className="tab-name">{col.name}</span>
            </button>
          ))}
        </div>

        {/* Collection Info */}
        {collectionInfo && (
          <div className="collection-info">
            <h2>{collectionInfo.title}</h2>
            <p>{collectionInfo.description}</p>
          </div>
        )}

        {/* Movies Grid */}
        <div className="collections-grid">
          {loading && collectionMovies.length === 0 ? (
            /* Show skeleton cards during initial load */
            Array.from({ length: 12 }).map((_, i) => (
              <div className="collection-movie-card skeleton" key={`skeleton-${i}`}>
                <div className="collection-movie-thumb" />
                <h3>&nbsp;</h3>
                <p className="movie-year">&nbsp;</p>
              </div>
            ))
          ) : (
            /* Show actual movies */
            collectionMovies.map((movie, idx) => (
              <MovieCard 
                key={movie.id || idx} 
                movie={movie} 
                onClick={onMovieClick}
              />
            ))
          )}
        </div>

        {collectionMovies.length === 0 && !loading && (
          <div className="no-movies">
            <p>Không có phim trong bộ sưu tập này</p>
          </div>
        )}
      </div>
  );
}
