import React from 'react';
import { FiSearch, FiBell, FiUser, FiGlobe } from 'react-icons/fi';

const Header = ({ language, setLanguage, accounts = [], selectedAccountId, setSelectedAccountId, onGenerateReport, isSidebarCollapsed }) => {
  return (
    <header className="glass-panel" style={{
      height: '70px',
      position: 'fixed',
      top: 0,
      left: isSidebarCollapsed ? '80px' : '240px', // Responsive to sidebar
      transition: 'left 0.3s ease',
      right: 0,
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      borderBottom: '1px solid var(--glass-border)',
      borderLeft: 'none',
      borderRight: 'none',
      borderTop: 'none',
      boxShadow: 'none' // Remove default shadow for cleaner look
    }}>
      <h2 style={{ fontSize: '1.25rem' }}>
        {language === 'zh' ? '儀表板總覽' : 'Dashboard Overview'}
      </h2>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>

        {/* Account Selector & Report Gen */}
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
              maxWidth: '200px'
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
        </div>

        {/* Language Toggle */}
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
          {language === 'zh' ? '中文 / EN' : 'EN / 中文'}
        </button>

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

        <div style={{
          position: 'relative',
          cursor: 'pointer',
          color: 'var(--text-secondary)'
        }}>
          <FiBell size={20} />
          <span style={{
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            width: '8px',
            height: '8px',
            backgroundColor: 'red',
            borderRadius: '50%'
          }}></span>
        </div>

        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: 'var(--bg-hover)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid var(--accent-primary)',
          cursor: 'pointer'
        }}>
          <FiUser />
        </div>
      </div>
    </header>
  );
};

export default Header;
