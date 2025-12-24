import React from 'react';
import './MovieSkeleton.css';

export function MovieCardSkeleton() {
  return (
    <div className="movie-card-skeleton">
      <div className="skeleton-thumb"></div>
      <div className="skeleton-info">
        <div className="skeleton-title"></div>
        <div className="skeleton-meta"></div>
      </div>
    </div>
  );
}

export function MovieGridSkeleton({ count = 12 }) {
  return (
    <div className="movie-grid">
      {Array.from({ length: count }).map((_, idx) => (
        <MovieCardSkeleton key={idx} />
      ))}
    </div>
  );
}

export function SectionSkeleton() {
  return (
    <section className="movie-section">
      <div className="section-header">
        <div className="skeleton-section-title"></div>
      </div>
      <MovieGridSkeleton count={6} />
    </section>
  );
}
