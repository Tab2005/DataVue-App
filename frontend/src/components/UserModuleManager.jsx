/**
 * 使用者模組授權管理組件
 * 允許管理員為使用者開通或關閉模組存取權
 */
import React, { useState, useEffect } from 'react';
import { FaUserCog, FaToggleOn, FaToggleOff, FaSearch, FaCheck, FaTimes } from 'react-icons/fa';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const UserModuleManager = ({ language = 'zh' }) => {
    // State
    const [users, setUsers] = useState([]);
    const [modules, setModules] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [userModules, setUserModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Translations
    const translations = {
        en: {
            title: "User Module Access",
            subtitle: "Grant or revoke module access for users",
            search_placeholder: "Search users...",
            select_user: "Select a user to manage",
            no_users: "No users found",
            modules_for: "Module access for",
            grant: "Grant",
            revoke: "Revoke",
            save_success: "Changes saved successfully",
            save_error: "Failed to save changes",
            loading: "Loading..."
        },
        zh: {
            title: "使用者模組授權",
            subtitle: "為使用者開通或關閉模組存取權",
            search_placeholder: "搜尋使用者...",
            select_user: "請選擇一位使用者進行管理",
            no_users: "找不到使用者",
            modules_for: "模組存取權：",
            grant: "開通",
            revoke: "關閉",
            save_success: "變更已儲存",
            save_error: "儲存失敗",
            loading: "載入中..."
        }
    };

    const t = translations[language] || translations.zh;

    const getAuthHeaders = () => ({
        'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
        'Content-Type': 'application/json'
    });

    // Fetch initial data
    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const headers = getAuthHeaders();

            // Fetch users and modules in parallel
            const [usersRes, modulesRes] = await Promise.all([
                fetch(`${API_URL}/api/admin/users`, { headers }),
                fetch(`${API_URL}/api/permissions/admin/modules`, { headers })
            ]);

            if (usersRes.ok) {
                const usersData = await usersRes.json();
                setUsers(Array.isArray(usersData) ? usersData : []);
            }

            if (modulesRes.ok) {
                const modulesData = await modulesRes.json();
                setModules(modulesData);
            }
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    };

    // Fetch user's modules when selected
    useEffect(() => {
        if (selectedUser) {
            fetchUserModules(selectedUser.id);
        }
    }, [selectedUser]);

    const fetchUserModules = async (userId) => {
        try {
            const res = await fetch(
                `${API_URL}/api/permissions/admin/user/${userId}/modules`,
                { headers: getAuthHeaders() }
            );
            if (res.ok) {
                const data = await res.json();
                setUserModules(data.modules || []);
            }
        } catch (err) {
            console.error('Failed to fetch user modules:', err);
        }
    };

    // Toggle module access
    const toggleModuleAccess = async (moduleKey, currentlyEnabled) => {
        if (!selectedUser || saving) return;

        setSaving(true);
        setMessage({ type: '', text: '' });

        try {
            const endpoint = currentlyEnabled
                ? `${API_URL}/api/permissions/admin/revoke-module`
                : `${API_URL}/api/permissions/admin/grant-module`;

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    user_id: selectedUser.id,
                    module_key: moduleKey,
                    team_id: null
                })
            });

            if (res.ok) {
                // Update local state
                if (currentlyEnabled) {
                    setUserModules(userModules.filter(m => m !== moduleKey));
                } else {
                    setUserModules([...userModules, moduleKey]);
                }
                setMessage({ type: 'success', text: t.save_success });
            } else {
                setMessage({ type: 'error', text: t.save_error });
            }
        } catch (err) {
            console.error('Toggle module access failed:', err);
            setMessage({ type: 'error', text: t.save_error });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage({ type: '', text: '' }), 3000);
        }
    };

    // Filter users by search
    const filteredUsers = users.filter(user =>
        (user.name && user.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (user.email && user.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Styles
    const styles = {
        container: {
            padding: '24px 0'
        },
        header: {
            marginBottom: '24px'
        },
        title: {
            fontSize: '1.25rem',
            fontWeight: 'bold',
            color: 'var(--text-primary)',
            marginBottom: '4px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
        },
        subtitle: {
            fontSize: '0.875rem',
            color: 'var(--text-secondary)'
        },
        grid: {
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px'
        },
        panel: {
            backgroundColor: 'rgba(255,255,255,0.03)',
            borderRadius: '12px',
            border: '1px solid var(--glass-border)',
            overflow: 'hidden'
        },
        panelHeader: {
            padding: '16px',
            borderBottom: '1px solid var(--glass-border)',
            backgroundColor: 'rgba(0,0,0,0.1)'
        },
        panelBody: {
            padding: '16px',
            maxHeight: '400px',
            overflowY: 'auto'
        },
        searchBox: {
            position: 'relative',
            marginBottom: '12px'
        },
        searchInput: {
            width: '100%',
            padding: '10px 12px 10px 36px',
            backgroundColor: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--glass-border)',
            borderRadius: '8px',
            color: 'var(--text-primary)',
            fontSize: '0.875rem',
            outline: 'none'
        },
        searchIcon: {
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-secondary)'
        },
        userItem: (isSelected) => ({
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '8px',
            cursor: 'pointer',
            backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255,255,255,0.02)',
            border: isSelected ? '1px solid #3b82f6' : '1px solid transparent',
            transition: 'all 0.2s'
        }),
        userName: {
            fontWeight: '500',
            color: 'var(--text-primary)',
            marginBottom: '2px'
        },
        userEmail: {
            fontSize: '0.75rem',
            color: 'var(--text-secondary)'
        },
        moduleItem: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: 'rgba(255,255,255,0.02)',
            marginBottom: '8px'
        },
        moduleInfo: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        moduleIcon: {
            fontSize: '1.5rem'
        },
        toggleBtn: (enabled) => ({
            padding: '6px 16px',
            borderRadius: '20px',
            border: 'none',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontSize: '0.75rem',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: enabled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(107, 114, 128, 0.1)',
            color: enabled ? '#22c55e' : '#6b7280',
            opacity: saving ? 0.5 : 1,
            transition: 'all 0.2s'
        }),
        message: (type) => ({
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '16px',
            backgroundColor: type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: type === 'success' ? '#22c55e' : '#ef4444',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        }),
        placeholder: {
            textAlign: 'center',
            padding: '48px',
            color: 'var(--text-secondary)'
        }
    };

    if (loading) {
        return (
            <div style={styles.placeholder}>
                {t.loading}
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Header */}
            <div style={styles.header}>
                <h3 style={styles.title}>
                    <FaUserCog style={{ color: '#8b5cf6' }} />
                    {t.title}
                </h3>
                <p style={styles.subtitle}>{t.subtitle}</p>
            </div>

            {/* Message */}
            {message.text && (
                <div style={styles.message(message.type)}>
                    {message.type === 'success' ? <FaCheck /> : <FaTimes />}
                    {message.text}
                </div>
            )}

            {/* Grid Layout */}
            <div style={styles.grid}>
                {/* Users Panel */}
                <div style={styles.panel}>
                    <div style={styles.panelHeader}>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>使用者列表</div>
                    </div>
                    <div style={styles.panelBody}>
                        {/* Search */}
                        <div style={styles.searchBox}>
                            <FaSearch style={styles.searchIcon} />
                            <input
                                type="text"
                                placeholder={t.search_placeholder}
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={styles.searchInput}
                            />
                        </div>

                        {/* User List */}
                        {filteredUsers.length > 0 ? filteredUsers.map(user => (
                            <div
                                key={user.id}
                                style={styles.userItem(selectedUser?.id === user.id)}
                                onClick={() => setSelectedUser(user)}
                            >
                                <div style={styles.userName}>{user.name || 'Unknown'}</div>
                                <div style={styles.userEmail}>{user.email}</div>
                            </div>
                        )) : (
                            <div style={styles.placeholder}>{t.no_users}</div>
                        )}
                    </div>
                </div>

                {/* Modules Panel */}
                <div style={styles.panel}>
                    <div style={styles.panelHeader}>
                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                            {selectedUser ? `${t.modules_for} ${selectedUser.name}` : t.select_user}
                        </div>
                    </div>
                    <div style={styles.panelBody}>
                        {selectedUser ? (
                            modules.map(mod => {
                                const isEnabled = userModules.includes(mod.key);
                                return (
                                    <div key={mod.id} style={styles.moduleItem}>
                                        <div style={styles.moduleInfo}>
                                            <span style={styles.moduleIcon}>{mod.icon || '📦'}</span>
                                            <div>
                                                <div style={{ fontWeight: '500', color: 'var(--text-primary)' }}>
                                                    {mod.name}
                                                </div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                    {mod.key}
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            style={styles.toggleBtn(isEnabled)}
                                            onClick={() => toggleModuleAccess(mod.key, isEnabled)}
                                            disabled={saving}
                                        >
                                            {isEnabled ? (
                                                <>
                                                    <FaToggleOn size={14} />
                                                    已開通
                                                </>
                                            ) : (
                                                <>
                                                    <FaToggleOff size={14} />
                                                    未開通
                                                </>
                                            )}
                                        </button>
                                    </div>
                                );
                            })
                        ) : (
                            <div style={styles.placeholder}>
                                ← {t.select_user}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserModuleManager;
