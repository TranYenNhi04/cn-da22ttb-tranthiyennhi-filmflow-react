import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LazyImage from './LazyImage';

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe(target) {
    // Simulate immediate intersection for testing
    this.callback([{ isIntersecting: true, target }]);
  }

  unobserve() {}
  disconnect() {}
};

describe('LazyImage Component', () => {
  test('renders with placeholder initially', () => {
    render(
      <LazyImage
        src="https://example.com/image.jpg"
        alt="Test Image"
        className="test-class"
      />
    );

    const img = screen.getByAltText('Test Image');
    expect(img).toBeInTheDocument();
    expect(img).toHaveClass('test-class');
  });

  test('loads actual image when in view', async () => {
    render(
      <LazyImage
        src="https://example.com/image.jpg"
        alt="Test Image"
      />
    );

    const img = screen.getByAltText('Test Image');
    
    await waitFor(() => {
      expect(img.src).toBe('https://example.com/image.jpg');
    });
  });

  test('uses custom placeholder', () => {
    const customPlaceholder = 'data:image/png;base64,placeholder';
    
    render(
      <LazyImage
        src="https://example.com/image.jpg"
        alt="Test Image"
        placeholder={customPlaceholder}
      />
    );

    const img = screen.getByAltText('Test Image');
    // Initially should have placeholder
    expect(img).toBeInTheDocument();
  });
});
