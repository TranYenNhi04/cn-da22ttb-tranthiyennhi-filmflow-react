import React, { useState } from 'react';
import styles from './AuthPage.module.css';
import { API_BASE } from '../config';

function makeUserId() {
  return `user_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
}

export default function AuthPage({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    // Validate
    if (!formData.email || !formData.password) {
      setError('Vui lòng điền đầy đủ thông tin');
      return;
    }

    if (!isLogin && !formData.name) {
      setError('Vui lòng nhập tên của bạn');
      return;
    }

    // Simple validation - in production, check with backend
    if (isLogin) {
      // Attempt login via backend; if not found, prompt to register
      fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, password: formData.password })
      }).then(async (res) => {
        if (res.status === 200) {
          const data = await res.json();
          // store returned user (metadata is JSON string)
          let user = { userId: data.user.id };
          try {
            const md = JSON.parse(data.user.metadata || '{}');
            user.email = md.email || formData.email;
            user.name = md.name || md.email?.split('@')[0] || formData.email.split('@')[0] || 'User';
          } catch (e) {
            user.email = formData.email;
            user.name = formData.name || formData.email.split('@')[0] || 'User';
          }
          localStorage.setItem('user', JSON.stringify(user));
          onLogin();
        } else if (res.status === 404) {
          setError('Tài khoản chưa tồn tại. Vui lòng đăng ký.');
          setIsLogin(false);
        } else {
          setError('Lỗi đăng nhập. Vui lòng thử lại.');
        }
      }).catch(() => {
        setError('Không thể kết nối đến server. Vui lòng thử lại sau.');
      });
    } else {
      // Register flow: create userId and persist
      let user = {
        userId: makeUserId(),
        email: formData.email,
        name: formData.name || (formData.email.split('@')[0] || 'User')
      };
      // call backend to create user (best-effort)
      fetch(`${API_BASE}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user.userId, metadata: JSON.stringify({ name: user.name, email: user.email }) })
      }).catch(() => {});
      localStorage.setItem('user', JSON.stringify(user));
      onLogin();
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className={styles.authPage}>
      <div className={styles.authBackground}></div>
      
      <div className={styles.authHeader}>
        <h1 className={styles.logo}>FilmFlow</h1>
      </div>

      <div className={styles.authContainer}>
        <div className={styles.authBox}>
          <h2 className={styles.authTitle}>{isLogin ? 'Đăng nhập' : 'Đăng ký'}</h2>
          
          {error && <div className={styles.error}>{error}</div>}
          
          <form onSubmit={handleSubmit} className={styles.authForm}>
            {!isLogin && (
              <div className={styles.inputGroup}>
                <input
                  type="text"
                  name="name"
                  placeholder="Tên của bạn"
                  value={formData.name}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>
            )}
            
            <div className={styles.inputGroup}>
              <input
                type="email"
                name="email"
                placeholder="Email hoặc số điện thoại"
                value={formData.email}
                onChange={handleChange}
                className={styles.input}
              />
            </div>

            <div className={styles.inputGroup}>
              <input
                type="password"
                name="password"
                placeholder="Mật khẩu"
                value={formData.password}
                onChange={handleChange}
                className={styles.input}
              />
            </div>

            <button type="submit" className={styles.submitBtn}>
              {isLogin ? 'Đăng nhập' : 'Đăng ký'}
            </button>
          </form>

          <div className={styles.authFooter}>
            <span className={styles.switchText}>
              {isLogin ? 'Bạn mới sử dụng FilmFlow?' : 'Đã có tài khoản?'}
            </span>
            <button 
              onClick={() => setIsLogin(!isLogin)} 
              className={styles.switchBtn}
            >
              {isLogin ? 'Đăng ký ngay' : 'Đăng nhập ngay'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
