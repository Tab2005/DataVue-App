import React from 'react';
import { FiCpu, FiMessageSquare, FiTrendingUp, FiZap } from 'react-icons/fi';

const tabIcons = {
    facebook: <FiTrendingUp size={14} />,
    ai: <FiZap size={14} />,
    gemini: <FiCpu size={14} />,
    line: <FiMessageSquare size={14} />,
};

const SettingsTabs = ({ activeTab, setActiveTab, setStatus, tabs }) => (
    <div style={{ 
        display: 'flex', 
        marginBottom: '24px', 
        borderBottom: '1px solid var(--glass-border)',
        overflowX: 'auto',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
        position: 'relative'
    }}>
        <style>{`
            .settings-tab-container::-webkit-scrollbar { display: none; }
            .settings-tab-btn {
                padding: 12px 14px;
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: var(--text-secondary);
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.88rem;
                white-space: nowrap;
                display: flex;
                align-items: center;
                gap: 6px;
                flex-shrink: 0;
            }
            .settings-tab-btn.active {
                border-bottom: 2px solid var(--accent-primary);
                color: var(--accent-primary);
                font-weight: 600;
                background: rgba(45, 136, 255, 0.05);
            }
            .settings-tab-btn:hover:not(.active) {
                color: var(--text-primary);
                background: rgba(255, 255, 255, 0.02);
            }
        `}</style>
        
        <div className="settings-tab-container" style={{ display: 'flex', width: '100%', overflowX: 'auto' }}>
            {Object.keys(tabs).map(key => (
                <button
                    key={key}
                    className={`settings-tab-btn ${activeTab === key ? 'active' : ''}`}
                    onClick={() => { setActiveTab(key); setStatus(null); }}
                >
                    {tabIcons[key]}
                    {tabs[key]}
                </button>
            ))}
        </div>
    </div>
);

export default SettingsTabs;
