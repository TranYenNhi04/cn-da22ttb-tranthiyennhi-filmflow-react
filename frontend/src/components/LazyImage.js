import React, { useState, useEffect, useRef } from 'react';

/**
 * LazyImage Component - Lazy load images with placeholder
 * Improves performance by loading images only when they're visible
 */
const LazyImage = ({ src, alt, className, style, placeholder }) => {
  const [imageSrc, setImageSrc] = useState(placeholder || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450"%3E%3Crect fill="%23333" width="300" height="450"/%3E%3C/svg%3E');
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    // Use Intersection Observer for lazy loading
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            setImageSrc(src);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        rootMargin: '50px', // Load images 50px before they become visible
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current);
      }
    };
  }, [src]);

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={className}
      style={{
        ...style,
        opacity: isLoaded ? 1 : 0.6,
        transition: 'opacity 0.3s ease-in-out',
      }}
      onLoad={() => setIsLoaded(true)}
      loading="lazy"
    />
  );
};

export default LazyImage;
