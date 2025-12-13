import React, { useState } from 'react';
import { FiHome, FiBarChart2, FiUsers, FiSettings, FiActivity, FiChevronLeft, FiChevronRight, FiShield } from 'react-icons/fi';
import { Link, useLocation } from 'react-router-dom';
import SettingsModal from './SettingsModal';

const Sidebar = ({ language, isCollapsed, setIsCollapsed, isMobile, selectedTeamId, selectedTeamName }) => {

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const location = useLocation();

    // Mobile: Toggle logic is inverted for visual state (Collapsed = Hidden)
    const showSidebar = isMobile ? !isCollapsed : true;
    const sidebarWidth = isMobile ? '240px' : (isCollapsed ? '80px' : '240px');

    const menuItems = [
        { icon: <FiHome size={20} />, label: 'Overview', path: '/' },
        { icon: <FiBarChart2 size={20} />, label: 'Analytics', path: '/analytics' },
        { icon: <FiUsers size={20} />, label: 'Audience', path: '#' },
        { icon: <FiActivity size={20} />, label: 'Activity', path: '#' },
        { icon: <FiUsers size={20} />, label: 'Members', path: '/settings/users' },
        { icon: <FiSettings size={20} />, label: 'Team Settings', path: '/settings/general' },
        { icon: <FiShield size={20} />, label: 'API Connection', action: () => setIsSettingsOpen(true) },
    ];

    return (
        <>
            {/* Mobile Backdrop */}
            {isMobile && !isCollapsed && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: 'rgba(0,0,0,0.5)',
                        zIndex: 49,
                        backdropFilter: 'blur(2px)'
                    }}
                    onClick={() => setIsCollapsed(true)}
                />
            )}

            <aside style={{
                width: sidebarWidth,
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
                transition: 'all 0.3s ease',
                overflow: 'hidden',
                // Mobile Transform
                transform: isMobile
                    ? (isCollapsed ? 'translateX(-100%)' : 'translateX(0)')
                    : 'none',
                boxShadow: isMobile && !isCollapsed ? '4px 0 20px rgba(0,0,0,0.5)' : 'none'
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: (isCollapsed && !isMobile) ? 'center' : 'flex-start',
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
                        minWidth: '32px',
                        background: 'var(--accent-primary)',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                    }}>
                        F
                    </div>
                    {(!isCollapsed || isMobile) && <span>Facebook DB</span>}
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                    {menuItems.map((item, index) => {
                        const isActive = item.path === location.pathname;

                        // Wrapper styles
                        const itemStyle = {
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: (isCollapsed && !isMobile) ? 'center' : 'flex-start',
                            gap: '12px',
                            padding: '12px',
                            borderRadius: 'var(--radius-md)',
                            cursor: 'pointer',
                            backgroundColor: isActive ? 'rgba(45, 136, 255, 0.1)' : 'transparent',
                            color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                            transition: 'all 0.2s ease',
                            textDecoration: 'none',
                            width: '100%',
                            boxSizing: 'border-box'
                        };

                        const content = (
                            <>
                                {item.icon}
                                {(!isCollapsed || isMobile) && <span style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>{item.label}</span>}
                            </>
                        );

                        if (item.path && item.path !== '#') {
                            return (
                                <Link
                                    key={index}
                                    to={item.path}
                                    style={itemStyle}
                                    onClick={() => isMobile && setIsCollapsed(true)} // Close on navigate (mobile)
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

                        // ... (Action Items)
                        return (
                            <div key={index} style={itemStyle}
                                onClick={() => {
                                    if (item.action) item.action();
                                    if (isMobile) setIsCollapsed(true);
                                }}
                            // ...
                            >
                                {content}
                            </div>
                        );
                    })}
                </nav>

                {/* Collapse Toggle Button (Desktop Only) */}
                {!isMobile && (
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
                )}

            </aside>

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                language={language || 'zh'}
                teamId={selectedTeamId}
                teamName={selectedTeamName}
            />
        </>
    );
};

export default Sidebar;
