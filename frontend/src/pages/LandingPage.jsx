import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAuthToken } from '../utils/auth';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!getAuthToken();

  const features = [
    {
      title: 'Site-tegy AI Hub',
      description: '具備「勝負感」的決策建議，將冷冰冰的數據轉化為可執行的戰略指令。',
      icon: '🧠'
    },
    {
      title: '跨平台全景儀表板',
      description: '整合 GSC、GA4 與 Facebook Ads，在一站式介面中對照所有關鍵指標。',
      icon: '📊'
    },
    {
      title: '自動化數據戰報',
      description: '定時排程生成精美週報，讓您與團隊隨時掌握戰場動態。',
      icon: '📩'
    },
    {
      title: '企業級權限管理',
      description: '基於工作區的 RBAC 協作系統，專為成長型團隊與初創公司打造。',
      icon: '🏢'
    }
  ];

  return (
    <div className="landing-container">
      {/* Navigation */}
      <nav className="landing-nav glass-panel">
        <div className="nav-content">
          <div className="logo">
            <span className="logo-text">站略 <span className="logo-sub">Site-tegy</span></span>
          </div>
          <div className="nav-links">
            <a href="#features">功能亮點</a>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn-primary">進入儀表板</Link>
            ) : (
              <Link to="/login" className="btn-primary">立即登入</Link>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="hero-section">
        <div className="hero-content animate-fade-in">
          <h1 className="hero-title">
            終結數據迷航<br />
            讓數字成為可執行的<span className="text-highlight">戰略</span>
          </h1>
          <p className="hero-subtitle">
            專為個人品牌與中小企業打造的 AI 數據決策中心。<br />
            不再只是看報表，而是奪取市場。
          </p>
          <div className="hero-actions">
            {isAuthenticated ? (
              <button onClick={() => navigate('/dashboard')} className="btn-lg">
                開始決策
              </button>
            ) : (
              <button onClick={() => navigate('/login')} className="btn-lg">
                一鍵授權，立即體驗
              </button>
            )}
          </div>
        </div>
        <div className="hero-decoration">
          <div className="blob blob-1"></div>
          <div className="blob blob-2"></div>
        </div>
      </header>

      {/* Problem Section */}
      <section className="problem-section">
        <div className="section-content">
          <div className="comparison-grid">
            <div className="comparison-card legacy">
              <h3>傳統數據分析</h3>
              <ul>
                <li>❌ 分散各平台，整合耗時</li>
                <li>❌ 僅呈現流量與點擊</li>
                <li>❌ 決策依賴直覺或零散資訊</li>
              </ul>
            </div>
            <div className="comparison-card strategy glass-panel">
              <h3>站略 (Site-tegy) 決策</h3>
              <ul>
                <li>✅ 一站式儀表板，即刻對照</li>
                <li>✅ 深度意圖分析與行動建議</li>
                <li>✅ 數據支撐的戰略導向</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2>核心戰略武器</h2>
          <p>整合最強大的數據工具，助您在競爭中取得先機</p>
        </div>
        <div className="features-grid">
          {features.map((f, i) => (
            <div key={i} className="feature-card glass-panel animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="cta-section">
        <div className="glass-panel cta-box">
          <h2>準備好奪取市場了嗎？</h2>
          <p>立即完成授權，讓 AI 成為您的專屬數據分析師。</p>
          <button onClick={() => navigate('/login')} className="btn-lg btn-glow">
            立即開始
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>&copy; 2026 站略 (Site-tegy) 團隊. 讓每一分預算，都成為奪取市場的戰略物資。</p>
      </footer>
    </div>
  );
};

export default LandingPage;
