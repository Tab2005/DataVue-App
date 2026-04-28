import React, { useState, useEffect } from 'react';
import { FiHome, FiBarChart2, FiUsers, FiSettings, FiActivity, FiChevronLeft, FiChevronRight, FiShield, FiChevronDown, FiChevronUp, FiPlus, FiSearch, FiTrendingUp, FiFileText } from 'react-icons/fi';
import { Link, useLocation } from 'react-router-dom';
import SettingsModal from './SettingsModal';
import CreateTeamModal from './CreateTeamModal';

const Sidebar = ({ user, language, isCollapsed, setIsCollapsed, isMobile, selectedTeamId, selectedTeamName, teams = [], setSelectedTeamId, onRefresh }) => {

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    // Track expanded submenus by label key
    const [expandedMenus, setExpandedMenus] = useState({ 'Team Settings': true });
    const location = useLocation();

    // Mobile: Toggle logic is inverted for visual state (Collapsed = Hidden)
    const showSidebar = isMobile ? !isCollapsed : true;
    const sidebarWidth = isMobile ? '240px' : (isCollapsed ? '80px' : '240px');

    const toggleSubMenu = (label) => {
        if (isCollapsed && !isMobile) {
            setIsCollapsed(false);
            setExpandedMenus(prev => ({ ...prev, [label]: true }));
        } else {
            setExpandedMenus(prev => ({ ...prev, [label]: !prev[label] }));
        }
    };

    const t = (en, zh) => language === 'zh' ? zh : en;

    const menuItems = [
        { icon: <FiHome size={20} />, label: t('Overview', '總覽'), path: '/dashboard' },
        { icon: <FiBarChart2 size={20} />, label: t('Analytics', '成效分析'), path: '/analytics' },
        { icon: <FiActivity size={20} />, label: t('Metrics Manager', '指標管理'), path: '/metrics' },
        { icon: <FiFileText size={20} />, label: t('Weekly Reports', '週報管理'), path: '/reports' },
        { icon: <FiSearch size={20} />, label: t('Search Console', '搜尋管理'), path: '/gsc' },
        { icon: <FiTrendingUp size={20} />, label: t('Traffic Analytics', '流量分析'), path: '/ga4' },
        // Grouped Team Settings
        {
            icon: <FiSettings size={20} />,
            label: t('Team Settings', '團隊設定'),
            path: '/settings/team'
        },
        { icon: <FiShield size={20} />, label: t('API Connection', 'API 連線'), action: () => setIsSettingsOpen(true) },
    ];

    // --- Admin Menu (Optional) ---
    if (user?.is_super_admin) {
        menuItems.push({
            icon: <FiSettings size={20} />,
            label: t('Admin Panel', '後台管理'),
            path: '/admin',
            style: { color: 'var(--accent-secondary)' } // Distinguished color
        });
    }


    // Switcher State
    const [isSwitcherOpen, setIsSwitcherOpen] = useState(false);
    const [openCreateTeam, setOpenCreateTeam] = useState(false);

    // Click outside to close switcher
    useEffect(() => {
        const closeSwitcher = () => setIsSwitcherOpen(false);
        if (isSwitcherOpen) {
            window.addEventListener('click', closeSwitcher);
        }
        return () => window.removeEventListener('click', closeSwitcher);
    }, [isSwitcherOpen]);

    return (
        <>
            {/* Mobile Backdrop */}
            {isMobile && !isCollapsed && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        backgroundColor: 'rgba(0,0,0,0.5)',
                        zIndex: 149, // z-index > Header (100) but < Sidebar (150)
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
                zIndex: 150, // z-index > Header (100)
                transition: 'all 0.3s ease',
                // Allow dropdown to overflow if needed, but 'fixed' sidebar might clip. 
                // Actually 'overflow: visible' works for absolute children if parent doesn't clip.
                // Sidebar has 'overflow: hidden' usually for content. 
                // Let's change main sidebar overflow to 'visible' ONLY when collapsed? 
                // Or use a Portal? Portal is safer but simpler is inline absolute.
                // Let's try standard absolute first, checking clipping.
                // NOTE: Original code had 'overflow: hidden'. If we want a popout-menu, we might need to change that.
                // However, if we put the menu INSIDE the sidebar padding, it pushes content down (Accordion style)?
                // No, User requested a Dropdown.
                // Let's change overflow to 'visible' temporarily.
                overflow: isCollapsed ? 'visible' : 'hidden',
                // Wait, if it's not collapsed, hidden is fine if menu is inside. 
                // If collapsed, we need it visible to show tooltip/menu.
                // Actually for this top switcher, if expanded, menu can be inside.

                // Mobile Transform
                transform: isMobile
                    ? (isCollapsed ? 'translateX(-100%)' : 'translateX(0)')
                    : 'none',
                boxShadow: isMobile && !isCollapsed ? '4px 0 20px rgba(0,0,0,0.5)' : 'none'
            }}>
                {/* --- WORKSPACE SWITCHER --- */}
                <div
                    onClick={(e) => {
                        e.stopPropagation();
                        setIsSwitcherOpen(!isSwitcherOpen);
                    }}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: (isCollapsed && !isMobile) ? 'center' : 'flex-start',
                        gap: '12px',
                        marginBottom: '24px',
                        padding: '8px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'background 0.2s',
                        position: 'relative', // Anchor for dropdown
                        backgroundColor: isSwitcherOpen ? 'var(--bg-hover)' : 'transparent'
                    }}>
                    <div style={{
                        width: '32px',
                        height: '32px',
                        minWidth: '32px',
                        background: selectedTeamId ? 'var(--accent-primary)' : '#4b5563', // Blue for Team, Gray for Personal
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '1.2rem'
                    }}>
                        {selectedTeamId ? (selectedTeamName ? selectedTeamName.charAt(0).toUpperCase() : 'T') : 'P'}
                    </div>

                    {(!isCollapsed || isMobile) && (
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {selectedTeamId ? selectedTeamName : (language === 'zh' ? '個人工作區' : 'Personal Workspace')}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                {language === 'zh' ? '切換工作區' : 'Switch Workspace'}
                            </div>
                        </div>
                    )}

                    {(!isCollapsed || isMobile) && (
                        <FiChevronDown style={{ color: 'var(--text-secondary)' }} />
                    )}

                    {/* DROPDOWN MENU */}
                    {isSwitcherOpen && (
                        <div style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            width: '220px', // Wider than collapsed sidebar
                            backgroundColor: 'var(--bg-secondary)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '12px',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
                            zIndex: 100,
                            padding: '8px',
                            marginTop: '8px',
                            backdropFilter: 'blur(10px)'
                        }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', padding: '4px 8px', marginBottom: '4px' }}>
                                {language === 'zh' ? '個人' : 'Personal'}
                            </div>
                            <div
                                onClick={() => {
                                    setSelectedTeamId('');
                                    setIsSwitcherOpen(false);
                                    if (isMobile) setIsCollapsed(true);
                                }}
                                style={{
                                    padding: '8px',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '8px',
                                    background: !selectedTeamId ? 'var(--bg-hover)' : 'transparent',
                                    color: !selectedTeamId ? 'var(--accent-primary)' : 'var(--text-primary)'
                                }}
                            >
                                <div style={{ width: '24px', height: '24px', borderRadius: '4px', background: '#4b5563', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', color: 'white' }}>P</div>
                                <span>{language === 'zh' ? '個人工作區' : 'Personal'}</span>
                            </div>

                            <div style={{ height: '1px', background: 'var(--glass-border)', margin: '8px 0' }}></div>

                            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', padding: '4px 8px', marginBottom: '4px' }}>
                                {language === 'zh' ? '團隊' : 'Teams'}
                            </div>

                            {teams.map(team => (
                                <div
                                    key={team.id}
                                    onClick={() => {
                                        setSelectedTeamId(team.id);
                                        setIsSwitcherOpen(false);
                                        if (isMobile) setIsCollapsed(true);
                                    }}
                                    style={{
                                        padding: '8px',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        display: 'flex', alignItems: 'center', gap: '8px',
                                        background: selectedTeamId === team.id ? 'var(--bg-hover)' : 'transparent',
                                        color: selectedTeamId === team.id ? 'var(--accent-primary)' : 'var(--text-primary)',
                                        marginBottom: '2px'
                                    }}
                                >
                                    <div style={{ width: '24px', height: '24px', borderRadius: '4px', background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', color: 'white' }}>
                                        {team.name.charAt(0).toUpperCase()}
                                    </div>
                                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{team.name}</span>
                                </div>
                            ))}

                            <div style={{ height: '1px', background: 'var(--glass-border)', margin: '8px 0' }}></div>

                            <div
                                onClick={() => {
                                    setOpenCreateTeam(true);
                                    setIsSwitcherOpen(false);
                                    if (isMobile) setIsCollapsed(true);
                                }}
                                style={{
                                    padding: '8px',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '8px',
                                    color: 'var(--text-secondary)',
                                    transition: 'color 0.2s'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
                                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                            >
                                <div style={{ width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><FiPlus /></div>
                                <span>{language === 'zh' ? '建立新團隊' : 'Create Team'}</span>
                            </div>
                        </div>
                    )}
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
                    {menuItems.map((item, index) => {
                        // Check if any child is active to highlight parent
                        const isChildActive = item.children?.some(child => child.path === location.pathname);
                        const isActive = item.path === location.pathname || isChildActive;
                        const isExpanded = expandedMenus[item.label];

                        // Wrapper styles
                        const itemStyle = {
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: (isCollapsed && !isMobile) ? 'center' : 'flex-start',
                            gap: '12px',
                            padding: '12px',
                            borderRadius: 'var(--radius-md)',
                            cursor: 'pointer',
                            backgroundColor: isActive && !item.children ? 'rgba(45, 136, 255, 0.1)' : 'transparent',
                            color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                            textDecoration: 'none',
                            width: '100%',
                            boxSizing: 'border-box',
                            position: 'relative',
                            ...item.style // Merge custom styles (e.g. colors)
                        };

                        const content = (
                            <>
                                {item.icon}
                                {(!isCollapsed || isMobile) && (
                                    <>
                                        <span style={{ fontWeight: 500, whiteSpace: 'nowrap', flex: 1 }}>{item.label}</span>
                                        {item.children && (
                                            <span style={{ opacity: 0.6 }}>
                                                {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                                            </span>
                                        )}
                                    </>
                                )}
                            </>
                        );

                        // PARENT WITH CHILDREN
                        if (item.children) {
                            return (
                                <div key={index}>
                                    <div
                                        style={itemStyle}
                                        onClick={() => toggleSubMenu(item.label)}
                                        onMouseEnter={(e) => {
                                            if (!isActive) {
                                                e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                                                e.currentTarget.style.color = 'var(--text-primary)';
                                            }
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!isActive) {
                                                e.currentTarget.style.backgroundColor = 'transparent';
                                                e.currentTarget.style.color = isActive ? 'var(--accent-primary)' : 'var(--text-secondary)';
                                            }
                                        }}
                                    >
                                        {content}
                                    </div>

                                    {/* Children Container */}
                                    <div style={{
                                        maxHeight: isExpanded && (!isCollapsed || isMobile) ? '500px' : '0',
                                        overflow: 'hidden',
                                        transition: 'max-height 0.3s ease',
                                        marginLeft: (isCollapsed && !isMobile) ? '0' : '20px', // Indent
                                    }}>
                                        {item.children.map((child, cIdx) => {
                                            const isChildSelected = child.path === location.pathname;
                                            return (
                                                <Link
                                                    key={cIdx}
                                                    to={child.path}
                                                    onClick={() => isMobile && setIsCollapsed(true)}
                                                    style={{
                                                        display: 'block',
                                                        padding: '10px 12px 10px 36px', // Extra padding for hierarchy
                                                        color: isChildSelected ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                                                        textDecoration: 'none',
                                                        fontSize: '0.9rem',
                                                        borderLeft: isChildSelected ? '2px solid var(--accent-primary)' : '2px solid transparent',
                                                        whiteSpace: 'nowrap'
                                                    }}
                                                    onMouseEnter={(e) => e.target.style.color = 'var(--text-primary)'}
                                                    onMouseLeave={(e) => e.target.style.color = isChildSelected ? 'var(--accent-primary)' : 'var(--text-tertiary)'}
                                                >
                                                    {child.label}
                                                </Link>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        }

                        // STANDARD LINK
                        if (item.path && item.path !== '#') {
                            return (
                                <Link
                                    key={index}
                                    to={item.path}
                                    style={itemStyle}
                                    onClick={() => isMobile && setIsCollapsed(true)}
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

                        // ACTION ITEM
                        return (
                            <div key={index} style={itemStyle}
                                onClick={() => {
                                    if (item.action) item.action();
                                    if (isMobile) setIsCollapsed(true);
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                                    e.currentTarget.style.color = 'var(--text-primary)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                    e.currentTarget.style.color = 'var(--text-secondary)';
                                }}
                            >
                                {content}
                            </div>
                        );
                    })}
                </nav>

                {/* Branding Footer */}
                <div style={{
                    padding: '0 12px 12px 12px',
                    textAlign: 'center',
                    marginTop: 'auto',
                    opacity: isCollapsed && !isMobile ? 0 : 0.6,
                    transform: isCollapsed && !isMobile ? 'scale(0)' : 'scale(1)',
                    transition: 'all 0.3s ease',
                    height: isCollapsed && !isMobile ? '0' : 'auto',
                    overflow: 'hidden'
                }}>
                    <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
                        <FiFileText size={20} color="var(--accent-primary)" />
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', lineHeight: '1.4' }}>
                        © 2026 DataVue Analytics.<br />
                        保留所有權利。
                    </div>
                </div>

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
                            // marginTop: 'auto', // Remove this as Branding is now above it and taking the space/push
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                        {isCollapsed ? <FiChevronRight size={24} /> : <FiChevronLeft size={24} />}
                    </div>
                )}

            </aside>

            <CreateTeamModal
                isOpen={openCreateTeam}
                onClose={() => setOpenCreateTeam(false)}
                language={language}
                onTeamCreated={() => window.location.reload()}
            />

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                language={language || 'zh'}
                teamId={selectedTeamId}
                teamName={selectedTeamName}
                onSuccess={onRefresh} // Trigger refresh on success
            />
        </>
    );
};

export default Sidebar;
