import React, { useState, useEffect } from 'react';
import './App.css';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import RecommendationsPage from './pages/RecommendationsPage';
import ProfilePage from './pages/ProfilePage';
import CollectionsPage from './pages/CollectionsPage';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState('home');
  const [pageHistory, setPageHistory] = useState(['home']);
  const [user, setUser] = useState(null);
  const [selectedMovie, setSelectedMovie] = useState(null);

  // Prefetch data for faster page transitions
  const prefetchCollections = () => {
    const cacheKey = 'collection_best_2024';
    if (!localStorage.getItem(cacheKey)) {
      fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000'}/collections/best_2024?limit=30`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            try {
              localStorage.setItem(cacheKey, JSON.stringify(data));
            } catch (e) {}
          }
        })
        .catch(() => {});
    }
  };

  const prefetchRecommendations = () => {
    const userId = user?.userId || 'Anonymous';
    const cacheKey = `cached_recs_hybrid_${userId}`;
    if (!localStorage.getItem(cacheKey)) {
      fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000'}/recommendations?rec_type=hybrid&n=20&user_id=${userId}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            try {
              localStorage.setItem(cacheKey, JSON.stringify(data));
            } catch (e) {}
          }
        })
        .catch(() => {});
    }
  };

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const u = JSON.parse(storedUser);
      // ensure userId exists
      if (!u.userId) {
        u.userId = `user_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
        localStorage.setItem('user', JSON.stringify(u));
        // best-effort notify backend
        try { fetch(`${process.env.REACT_APP_API_BASE || 'http://localhost:8000'}/users`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ userId: u.userId, metadata: JSON.stringify({ name: u.name, email: u.email }) }) }).catch(()=>{}); } catch(e){}
      }
      setUser(u);
      setIsAuthenticated(true);
      
      // Prefetch key data immediately for faster navigation
      setTimeout(() => {
        prefetchCollections();
        prefetchRecommendations();
      }, 500);
    }
  }, []);

  const handleLogin = () => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
    setCurrentPage('home');
    setPageHistory(['home']);
  };

  const navigateTo = (page) => {
    setPageHistory([...pageHistory, page]);
    setCurrentPage(page);
  };

  const handleMovieClick = (movie) => {
    setSelectedMovie(movie);
    navigateTo('watch');
  };

  const goBack = () => {
    if (pageHistory.length > 1) {
      const newHistory = [...pageHistory];
      newHistory.pop(); // Remove current page
      const previousPage = newHistory[newHistory.length - 1];
      setPageHistory(newHistory);
      setCurrentPage(previousPage);
      if (previousPage !== 'watch') {
        setSelectedMovie(null);
      }
    }
  };

  if (!isAuthenticated) {
    return <AuthPage onLogin={handleLogin} />;
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="brand-text">FilmFlow</h1>
        </div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => navigateTo('home')}
          >
            <span className="nav-text">Trang chủ</span>
          </button>
          <button 
            className={`nav-link ${currentPage === 'collections' ? 'active' : ''}`}
            onClick={() => navigateTo('collections')}
            onMouseEnter={prefetchCollections}
          >
            <span className="nav-text">Bộ Sưu Tập</span>
          </button>
          <button 
            className={`nav-link ${currentPage === 'profile' ? 'active' : ''}`}
            onClick={() => navigateTo('profile')}
          >
            <span className="nav-text">Hồ Sơ</span>
          </button>
          <div className="sidebar-footer">
            <div className="user-info">
              <span className="user-name">{user?.name || user?.email}</span>
            </div>
            <button className="nav-link logout-btn" onClick={handleLogout}>
              <span className="nav-text">Đăng xuất</span>
            </button>
          </div>
        </nav>
      </aside>

      <main className="main-content">
        {currentPage === 'home' && <HomePage onMovieClick={handleMovieClick} />}
        {currentPage === 'recommendations' && <RecommendationsPage onBack={goBack} />}
        {currentPage === 'collections' && <CollectionsPage onMovieClick={handleMovieClick} />}
        {currentPage === 'profile' && <ProfilePage />}
        {currentPage === 'watch' && <RecommendationsPage onBack={goBack} initialMovie={selectedMovie} />}
      </main>
    </div>
  );
}
