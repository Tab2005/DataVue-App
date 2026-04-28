import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAuthToken } from '../utils/auth';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!getAuthToken();
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      title: 'Site-tegy AI Hub',
      description: '具備「勝負感」的決策建議，將冷冰冰的數據轉化為可執行的戰略指令。',
      icon: '🧠',
      size: 'large'
    },
    {
      title: '跨平台全景',
      description: '整合 GSC、GA4 與 FB Ads。',
      icon: '📊',
      size: 'medium'
    },
    {
      title: '自動化數據戰報',
      description: '定時排程生成精美週報，讓您與團隊隨時掌握戰場動態。',
      icon: '📩',
      size: 'tall'
    },
    {
      title: '企業級權限管理',
      description: '基於工作區的 RBAC 協作系統，專為成長型團隊打造。',
      icon: '🏢',
      size: 'medium'
    },
    {
      title: '即時數據流',
      description: '秒級同步，確保您的決策始終基於最新資訊。',
      icon: '⚡',
      size: 'medium'
    }
  ];

  return (
    <div className="landing-container">
      <div className="grid-background"></div>

      {/* Modern Floating Navigation */}
      <nav className="landing-nav">
        <div className="logo-brand">SITE-TEGY</div>
        <div className="nav-links" style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          {isAuthenticated ? (
            <Link to="/dashboard" className="btn-premium primary" style={{ padding: '8px 20px', fontSize: '0.9rem' }}>Dashboard</Link>
          ) : (
            <Link to="/login" className="btn-premium primary" style={{ padding: '8px 20px', fontSize: '0.9rem' }}>Sign In</Link>
          )}
        </div>
      </nav>

      {/* Impactful Hero Section */}
      <header className="hero-section">
        <div className="hero-badge">✨ Next Generation Analytics</div>
        <h1 className="hero-title">
          <span className="title-reveal">Better Data.</span><br />
          <span style={{ color: '#2d88ff' }}>Better Strategy.</span>
        </h1>
        <p className="hero-subtitle">
          Experience the power of AI-driven decision making. Site-tegy transforms fragmented metrics into clear, actionable battle plans for your brand.
        </p>
        <div className="hero-cta-group">
          <button onClick={() => navigate(isAuthenticated ? '/dashboard' : '/login')} className="btn-premium primary">
            Get Started Free
          </button>
          <button className="btn-premium secondary">
            View Live Demo
          </button>
        </div>
      </header>

      {/* Modern Bento Grid Features */}
      <section id="features" className="bento-section">
        {features.map((f, i) => (
          <div key={i} className={`bento-card ${f.size}`}>
            <div className="card-icon">{f.icon}</div>
            <h3 className="card-title">{f.title}</h3>
            <p className="card-desc">{f.description}</p>
            {/* Subtle glow that follows mouse could be added here with JS */}
          </div>
        ))}
      </section>

      {/* Comparison Section (Condensed) */}
      <section style={{ padding: '100px 24px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '48px' }}>Why Site-tegy?</h2>
        <div style={{ 
          maxWidth: '800px', 
          margin: '0 auto', 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr', 
          gap: '2px', 
          background: 'var(--border-color)',
          borderRadius: '24px',
          overflow: 'hidden'
        }}>
          <div style={{ background: '#0a0a0a', padding: '48px' }}>
            <h4 style={{ color: '#666', marginBottom: '24px' }}>TRADITIONAL</h4>
            <div style={{ color: '#444', textDecoration: 'line-through', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <p>Manual Data Export</p>
              <p>Surface Metrics Only</p>
              <p>Guess-based Decisions</p>
            </div>
          </div>
          <div style={{ background: '#0a0a0a', padding: '48px', borderLeft: '1px solid var(--border-color)' }}>
            <h4 style={{ color: 'var(--accent-primary)', marginBottom: '24px' }}>SITE-TEGY</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontWeight: '500' }}>
              <p>Real-time Sync</p>
              <p>AI Intent Analysis</p>
              <p>Actionable Strategy</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <h2 className="cta-title">Ready to conquer the market?</h2>
        <p style={{ color: '#888', marginBottom: '40px', fontSize: '1.2rem' }}>
          Join elite brands using AI to drive their growth strategy.
        </p>
        <button onClick={() => navigate('/login')} className="btn-premium primary" style={{ padding: '20px 48px', fontSize: '1.25rem' }}>
          Initialize Strategy Hub
        </button>
      </section>

      {/* Minimalist Footer */}
      <footer style={{ padding: '80px 24px', textAlign: 'center', borderTop: '1px solid var(--border-color)', color: '#444' }}>
        <p>&copy; 2026 SITE-TEGY. ALL RIGHTS RESERVED.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
