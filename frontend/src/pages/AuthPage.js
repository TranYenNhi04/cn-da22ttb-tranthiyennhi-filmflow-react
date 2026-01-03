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
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Calculate password strength
  const getPasswordStrength = (password) => {
    if (!password) return { strength: 0, text: '', color: '' };
    let strength = 0;
    if (password.length >= 6) strength++;
    if (password.length >= 10) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    const levels = [
      { text: 'Rất yếu', color: '#ef4444' },
      { text: 'Yếu', color: '#f59e0b' },
      { text: 'Trung bình', color: '#eab308' },
      { text: 'Mạnh', color: '#84cc16' },
      { text: 'Rất mạnh', color: '#22c55e' }
    ];
    
    return { strength: (strength / 5) * 100, ...levels[Math.min(strength, 4)] };
  };
  
  const passwordStrength = !isLogin ? getPasswordStrength(formData.password) : null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Validate
    if (!formData.email || !formData.password) {
      setError('Vui lòng điền đầy đủ thông tin');
      return;
    }

    if (!isLogin && !formData.name) {
      setError('Vui lòng nhập tên của bạn');
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự');
      return;
    }

    if (isLogin) {
      // LOGIN FLOW
      fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: formData.email, 
          password: formData.password 
        })
      }).then(async (res) => {
        const data = await res.json();
        
        if (res.status === 200) {
          // Login successful
          let user = { 
            userId: data.user.id,
            email: data.user.email,
            name: data.user.name
          };
          localStorage.setItem('user', JSON.stringify(user));
          setIsLoading(false);
          onLogin();
        } else if (res.status === 404) {
          setIsLoading(false);
          setError('Email chưa được đăng ký. Vui lòng đăng ký tài khoản mới.');
          setIsLogin(false);
        } else if (res.status === 401) {
          setIsLoading(false);
          setError('Mật khẩu không chính xác. Vui lòng thử lại.');
        } else if (res.status === 400) {
          setIsLoading(false);
          setError(data.detail || 'Tài khoản chưa có mật khẩu. Vui lòng đăng ký lại.');
        } else {
          setIsLoading(false);
          setError(data.detail || 'Lỗi đăng nhập. Vui lòng thử lại.');
        }
      }).catch(() => {
        setIsLoading(false);
        setError('Không thể kết nối đến server. Vui lòng thử lại sau.');
      });
    } else {
      // REGISTER FLOW
      fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: formData.name,
          email: formData.email, 
          password: formData.password 
        })
      }).then(async (res) => {
        const data = await res.json();
        
        if (res.status === 200) {
          // Registration successful
          let user = {
            userId: data.user.id,
            email: data.user.email,
            name: data.user.name
          };
          localStorage.setItem('user', JSON.stringify(user));
          setIsLoading(false);
          onLogin();
        } else if (res.status === 400) {
          setIsLoading(false);
          setError(data.detail || 'Email đã được đăng ký. Vui lòng đăng nhập.');
          setIsLogin(true);
        } else {
          setIsLoading(false);
          setError(data.detail || 'Lỗi đăng ký. Vui lòng thử lại.');
        }
      }).catch(() => {
        setIsLoading(false);
        setError('Không thể kết nối đến server. Vui lòng thử lại sau.');
      });
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
                <div className={styles.inputWrapper}>
                  <span className={styles.inputIcon}>👤</span>
                  <input
                    type="text"
                    name="name"
                    placeholder="Họ và tên"
                    value={formData.name}
                    onChange={handleChange}
                    className={styles.input}
                    disabled={isLoading}
                  />
                </div>
              </div>
            )}
            
            <div className={styles.inputGroup}>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIcon}>✉️</span>
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                  className={styles.input}
                  disabled={isLoading}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIcon}>🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  placeholder="Mật khẩu (tối thiểu 6 ký tự)"
                  value={formData.password}
                  onChange={handleChange}
                  className={styles.input}
                  disabled={isLoading}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  className={styles.passwordToggle}
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {!isLogin && formData.password && (
                <div className={styles.passwordStrength}>
                  <div className={styles.strengthBar}>
                    <div 
                      className={styles.strengthFill}
                      style={{
                        width: `${passwordStrength.strength}%`,
                        backgroundColor: passwordStrength.color
                      }}
                    />
                  </div>
                  <span 
                    className={styles.strengthText}
                    style={{ color: passwordStrength.color }}
                  >
                    {passwordStrength.text}
                  </span>
                </div>
              )}
            </div>

            <button type="submit" className={styles.submitBtn} disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className={styles.spinner}></span>
                  <span>{isLogin ? 'Đang đăng nhập...' : 'Đang đăng ký...'}</span>
                </>
              ) : (
                <>
                  <span>{isLogin ? '🚀 Đăng nhập' : '✨ Đăng ký'}</span>
                </>
              )}
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
