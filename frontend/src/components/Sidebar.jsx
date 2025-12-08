import React, { useState } from 'react';
import { FiHome, FiBarChart2, FiUsers, FiSettings, FiActivity } from 'react-icons/fi';
import SettingsModal from './SettingsModal';

const Sidebar = ({ language }) => { // Accept language prop if needed, or manage locally
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    const menuItems = [
        { icon: <FiHome />, label: 'Overview', active: true },
        { icon: <FiBarChart2 />, label: 'Analytics', active: false },
        { icon: <FiUsers />, label: 'Audience', active: false },
        { icon: <FiActivity />, label: 'Activity', active: false },
        { icon: <FiSettings />, label: 'Settings', active: false, action: () => setIsSettingsOpen(true) },
    ];

    return (
        <>
            <aside style={{
                width: '240px',
                height: '100vh',
                backgroundColor: 'var(--bg-secondary)',
                borderRight: '1px solid var(--glass-border)',
                padding: 'var(--spacing-lg)',
                display: 'flex',
                flexDirection: 'column',
                position: 'fixed',
                left: 0,
                top: 0,
                zIndex: 50
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-sm)',
                    marginBottom: '40px',
                    color: 'var(--accent-primary)',
                    fontWeight: 'bold',
                    fontSize: '1.2rem'
                }}>
                    <div style={{
                        width: '32px',
                        height: '32px',
                        background: 'var(--accent-primary)',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                    }}>
                        F
                    </div>
                    Facebook DB
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {menuItems.map((item, index) => (
                        <div key={index} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: '12px 16px',
                            borderRadius: 'var(--radius-md)',
                            cursor: 'pointer',
                            backgroundColor: item.active ? 'rgba(45, 136, 255, 0.1)' : 'transparent',
                            color: item.active ? 'var(--accent-primary)' : 'var(--text-secondary)',
                            transition: 'all 0.2s ease'
                        }}
                            onClick={() => {
                                if (item.action) item.action();
                            }}
                            onMouseEnter={(e) => {
                                if (!item.active) {
                                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                                    e.currentTarget.style.color = 'var(--text-primary)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!item.active) {
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                    e.currentTarget.style.color = 'var(--text-secondary)';
                                }
                            }}
                        >
                            {item.icon}
                            <span style={{ fontWeight: 500 }}>{item.label}</span>
                        </div>
                    ))}
                </nav>
            </aside>

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                language={language || 'zh'} // Fallback if language not passed
            />
        </>
    );
};

export default Sidebar;
