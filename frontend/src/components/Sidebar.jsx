import React, { useState } from 'react';
import { FiHome, FiBarChart2, FiUsers, FiSettings, FiActivity, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { Link, useLocation } from 'react-router-dom';
import SettingsModal from './SettingsModal';

const Sidebar = ({ language, isCollapsed, setIsCollapsed }) => {
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const location = useLocation();

    const menuItems = [
        { icon: <FiHome size={20} />, label: 'Overview', path: '/' },
        { icon: <FiBarChart2 size={20} />, label: 'Analytics', path: '/analytics' },
        { icon: <FiUsers size={20} />, label: 'Audience', path: '#' },
        { icon: <FiActivity size={20} />, label: 'Activity', path: '#' },
        { icon: <FiSettings size={20} />, label: 'Settings', action: () => setIsSettingsOpen(true) },
    ];

    return (
        <>
            <aside style={{
                width: isCollapsed ? '80px' : '240px',
                height: '100vh',
                backgroundColor: 'var(--bg-secondary)',
                borderRight: '1px solid var(--glass-border)',
                padding: 'var(--spacing-lg) 12px',
                display: 'flex',
                flexDirection: 'column',
                position: 'fixed',
                left: 0,
                top: 0,
                zIndex: 50,
                transition: 'width 0.3s ease',
                overflow: 'hidden' // Prevent text overflow during transition
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: isCollapsed ? 'center' : 'flex-start',
                    gap: 'var(--spacing-sm)',
                    marginBottom: '40px',
                    color: 'var(--accent-primary)',
                    fontWeight: 'bold',
                    fontSize: '1.2rem',
                    whiteSpace: 'nowrap'
                }}>
                    <div style={{
                        width: '32px',
                        height: '32px',
                        minWidth: '32px', // Prevent shrinking
                        background: 'var(--accent-primary)',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                    }}>
                        F
                    </div>
                    {!isCollapsed && <span>Facebook DB</span>}
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                    {menuItems.map((item, index) => {
                        const isActive = item.path === location.pathname;

                        // Wrapper styles
                        const itemStyle = {
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: isCollapsed ? 'center' : 'flex-start',
                            gap: '12px',
                            padding: '12px',
                            borderRadius: 'var(--radius-md)',
                            cursor: 'pointer',
                            backgroundColor: isActive ? 'rgba(45, 136, 255, 0.1)' : 'transparent',
                            color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                            transition: 'all 0.2s ease',
                            textDecoration: 'none', // For Link
                            width: '100%',
                            boxSizing: 'border-box'
                        };

                        const content = (
                            <>
                                {item.icon}
                                {!isCollapsed && <span style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>{item.label}</span>}
                            </>
                        );

                        if (item.path && item.path !== '#') {
                            return (
                                <Link
                                    key={index}
                                    to={item.path}
                                    style={itemStyle}
                                    onMouseEnter={(e) => {
                                        if (!isActive) {
                                            e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                                            e.currentTarget.style.color = 'var(--text-primary)';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isActive) {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                            e.currentTarget.style.color = 'var(--text-secondary)';
                                        }
                                    }}
                                >
                                    {content}
                                </Link>
                            );
                        }

                        // Action Items (Settings, etc.)
                        return (
                            <div key={index} style={itemStyle}
                                onClick={() => {
                                    if (item.action) item.action();
                                }}
                                onMouseEnter={(e) => {
                                    if (!isActive) {
                                        e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                                        e.currentTarget.style.color = 'var(--text-primary)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isActive) {
                                        e.currentTarget.style.backgroundColor = 'transparent';
                                        e.currentTarget.style.color = 'var(--text-secondary)';
                                    }
                                }}
                            >
                                {content}
                            </div>
                        );
                    })}
                </nav>

                {/* Collapse Toggle Button */}
                <div
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    style={{
                        padding: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        color: 'var(--text-secondary)',
                        borderRadius: '8px',
                        marginTop: 'auto',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                    {isCollapsed ? <FiChevronRight size={24} /> : <FiChevronLeft size={24} />}
                </div>

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
