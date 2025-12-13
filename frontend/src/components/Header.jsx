import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiBell, FiUser, FiGlobe, FiSettings, FiLogOut, FiMenu, FiAlertTriangle, FiPlus, FiBriefcase, FiShield } from 'react-icons/fi';
import { FaShieldAlt } from 'react-icons/fa'; // Using FaShieldAlt for better visual

const Header = ({ language, setLanguage, accounts = [], selectedAccountId, setSelectedAccountId, onGenerateReport, isSidebarCollapsed, setIsSidebarCollapsed, onLogout, user, isMobile, teams = [], selectedTeamId, setSelectedTeamId }) => {
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [tokenStatus, setTokenStatus] = useState(null);
  const [hasUnread, setHasUnread] = useState(false);

  // Modal State
  const [openCreateTeam, setOpenCreateTeam] = useState(false);

  // Check Token Status
  useEffect(() => {
    if (user) {
      const checkToken = async () => {
        try {
          const idToken = localStorage.getItem('google_token');
          const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          const res = await fetch(`${apiUrl}/api/auth/token-status`, {
            headers: { 'Authorization': `Bearer ${idToken}` }
          });
          const json = await res.json();
          setTokenStatus(json);
        } catch (err) {
          console.error("Token status check failed", err);
        }
      };
      checkToken();
    }
  }, [user]);

  // Check Read Status
  useEffect(() => {
    if (tokenStatus && tokenStatus.days_remaining !== null && tokenStatus.days_remaining <= 3) {
      const lastRead = localStorage.getItem('token_warning_read_day');
      // If we haven't read this specific day's warning yet, mark as unread
      if (lastRead !== String(tokenStatus.days_remaining)) {
        setHasUnread(true);
      }
    }
  }, [tokenStatus]);

  const handleNotificationClick = () => {
    const newState = !showNotifications;
    setShowNotifications(newState);

    // Mark as read when opening
    if (newState && hasUnread && tokenStatus) {
      setHasUnread(false);
      localStorage.setItem('token_warning_read_day', String(tokenStatus.days_remaining));
    }
  };

  return (
    <header className="glass-panel" style={{
      height: '70px',
      position: 'fixed',
      top: 0,
      left: isMobile ? '0' : (isSidebarCollapsed ? '80px' : '240px'), // Responsive
      transition: 'left 0.3s ease',
      right: 0,
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: isMobile ? '0 16px' : '0 32px', // Reduce padding on mobile
      borderBottom: '1px solid var(--glass-border)',
      borderLeft: 'none',
      borderRight: 'none',
      borderTop: 'none',
      boxShadow: 'none'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Mobile Hamburger */}
        {isMobile && (
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '1.5rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <FiMenu />
          </button>
        )}

        {/* Title: Hidden on Mobile to make room for Selector */}
        {!isMobile && (
          <h2 style={{ fontSize: '1.25rem', whiteSpace: 'nowrap' }}>
            {language === 'zh' ? '儀表板總覽' : 'Dashboard Overview'}
          </h2>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '12px' : '24px' }}>



        {/* Account Selector: Visible on ALL screens now */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <select
            value={selectedAccountId || ''}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--glass-border)',
              color: 'white',
              padding: '6px 12px',
              borderRadius: '6px',
              outline: 'none',
              maxWidth: isMobile ? '160px' : '200px', // Smaller on mobile
              fontSize: isMobile ? '0.9rem' : '1rem'
            }}
          >
            {accounts.length === 0 && <option value="">{language === 'zh' ? '載入中...' : 'Loading...'}</option>}
            {accounts.length > 0 && <option value="" disabled>{language === 'zh' ? '選擇帳號' : 'Select Account'}</option>}
            {accounts.map(acc => (
              <option key={acc.id} value={acc.id} style={{ color: 'black' }}>
                {acc.name}
              </option>
            ))}
          </select>

          {/* Generate Button: Hidden on Mobile (Auto-fetch works on select change) */}
          {!isMobile && (
            <button
              onClick={onGenerateReport}
              disabled={!selectedAccountId}
              style={{
                background: !selectedAccountId ? 'gray' : 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: !selectedAccountId ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem'
              }}
            >
              {language === 'zh' ? '產生報表' : 'Generate Report'}
            </button>
          )}
        </div>

        {/* Language Toggle (Shortened on Mobile) */}
        <button
          onClick={() => setLanguage(l => l === 'zh' ? 'en' : 'zh')}
          style={{
            background: 'transparent',
            border: '1px solid var(--glass-border)',
            color: 'var(--text-secondary)',
            padding: '6px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.85rem'
          }}
        >
          <FiGlobe />
          {!isMobile && (language === 'zh' ? '中文 / EN' : 'EN / 中文')}
        </button>

        {/* Search Bar (Hidden on Mobile for space) */}
        {!isMobile && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'var(--bg-secondary)',
            padding: '8px 16px',
            borderRadius: '20px',
            border: '1px solid var(--glass-border)',
            width: '250px'
          }}>
            <FiSearch style={{ color: 'var(--text-secondary)', marginRight: '8px' }} />
            <input
              placeholder={language === 'zh' ? "搜尋..." : "Search..."}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                outline: 'none',
                width: '100%'
              }}
            />
          </div>
        )}

        {/* Notification Bell */}
        <div style={{ position: 'relative' }}>
          <div
            onClick={handleNotificationClick}
            style={{
              position: 'relative',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex', // Ensure alignment
              alignItems: 'center'
            }}
          >
            <FiBell size={20} />
            {/* Conditional Red Dot */}
            {hasUnread && (
              <span style={{
                position: 'absolute',
                top: '-2px',
                right: '-2px',
                width: '8px',
                height: '8px',
                backgroundColor: '#ef4444',
                borderRadius: '50%',
                border: '1px solid var(--bg-secondary)' // Better contrast
              }}></span>
            )}
          </div>

          {/* Notification Dropdown */}
          {showNotifications && (
            <>
              {/* Backdrop */}
              <div
                style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 998 }}
                onClick={() => setShowNotifications(false)}
              />

              <div className="glass-panel" style={{
                position: 'absolute',
                top: '40px',
                right: '-60px', // Center align roughly with bell or shift left
                width: '300px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                padding: '0',
                zIndex: 999,
                overflow: 'hidden'
              }}>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--glass-border)', fontWeight: 'bold' }}>
                  {language === 'zh' ? '通知' : 'Notifications'}
                </div>

                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {/* Token Warning Item */}
                  {tokenStatus && tokenStatus.days_remaining !== null && tokenStatus.days_remaining <= 3 ? (
                    <div
                      onClick={() => {
                        if (window.confirm(language === 'zh' ? '連結快過期，前往重新登入？' : 'Go to login page to renew?')) {
                          onLogout && onLogout();
                        }
                      }}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid var(--glass-border)',
                        cursor: 'pointer',
                        background: 'rgba(239, 68, 68, 0.05)',
                        transition: 'background 0.2s',
                        display: 'flex',
                        gap: '12px',
                        alignItems: 'start'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)'}
                    >
                      <div style={{
                        color: '#ef4444',
                        marginTop: '2px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        padding: '8px',
                        borderRadius: '50%'
                      }}>
                        <FiAlertTriangle size={16} />
                      </div>
                      <div>
                        <div style={{
                          fontSize: '0.9rem',
                          fontWeight: '600',
                          color: 'var(--text-primary)',
                          marginBottom: '4px'
                        }}>
                          {language === 'zh' ? 'Facebook 授權即將過期' : 'Facebook Token Expiring'}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {language === 'zh'
                            ? `您的授權將於 ${tokenStatus.days_remaining} 天後失效，請點擊此處重新登入更新。`
                            : `Your access token expires in ${tokenStatus.days_remaining} days. Click to renew.`}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {language === 'zh' ? '目前沒有新通知' : 'No new notifications'}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Avatar with Dropdown */}
        <div style={{ position: 'relative' }}>
          <div
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: 'var(--bg-hover)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid var(--accent-primary)',
              cursor: 'pointer',
              overflow: 'hidden'
            }}>
            {user && user.avatar ? (
              <img src={user.avatar} alt="User" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <FiUser />
            )}
          </div>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <>
              {/* Backdrop to close */}
              <div
                style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 998 }}
                onClick={() => setShowUserMenu(false)}
              />

              {/* Menu Card */}
              <div className="glass-panel" style={{
                position: 'absolute',
                top: '48px',
                right: 0,
                width: '280px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                padding: '0',
                zIndex: 999,
                overflow: 'hidden'
              }}>
                {/* User Info Section */}
                <div style={{ padding: '16px', borderBottom: '1px solid var(--glass-border)' }}>
                  <div style={{ fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {user?.name || 'Admin User'}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {user?.email || 'admin@example.com'}
                  </div>
                </div>

                {/* Actions Section */}
                {user?.is_super_admin && (
                  <div style={{ padding: '8px', borderBottom: '1px solid var(--glass-border)' }}>
                    <button
                      onClick={() => navigate('/admin')}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        background: 'rgba(59, 130, 246, 0.1)',
                        color: '#60a5fa',
                        border: 'none',
                        padding: '10px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <FaShieldAlt />
                      {language === 'zh' ? '超級管理員後台' : 'Super Admin Dashboard'}
                    </button>
                  </div>
                )}

                <div style={{ display: 'flex', padding: '8px' }}>
                  {/* Change Password */}
                  <button style={{
                    flex: 1,
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    padding: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    transition: 'background 0.2s'
                  }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    onClick={() => alert(language === 'zh' ? '修改密碼功能即將推出' : 'Change Password Coming Soon')}
                  >
                    <FiSettings />
                    <span style={{ fontSize: '0.9rem' }}>{language === 'zh' ? '修改密碼' : 'Password'}</span>
                  </button>

                  {/* Vertical Divider */}
                  <div style={{ width: '1px', background: 'var(--glass-border)', margin: '4px 0' }}></div>

                  {/* Logout */}
                  <button style={{
                    flex: 1,
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    padding: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    transition: 'background 0.2s'
                  }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    onClick={() => {
                      if (window.confirm(language === 'zh' ? '確定要登出嗎？' : 'Logout?')) {
                        onLogout && onLogout();
                      }
                    }}
                  >
                    <FiLogOut />
                    <span style={{ fontSize: '0.9rem' }}>{language === 'zh' ? '登出' : 'Logout'}</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

      </div>


    </header>
  );
};

export default Header;

