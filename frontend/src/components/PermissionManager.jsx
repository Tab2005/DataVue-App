import React, { useState, useEffect } from 'react';
import { FaKey, FaCubes, FaUserTag, FaToggleOn, FaToggleOff, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import UserModuleManager from './UserModuleManager';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PermissionManager = ({ language = 'zh' }) => {
    // State
    const [modules, setModules] = useState([]);
    const [permissions, setPermissions] = useState([]);
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedModule, setExpandedModule] = useState(null);

    // Translations
    const translations = {
        en: {
            title: "Permission Management",
            subtitle: "Manage modules, permissions and roles",
            modules_title: "System Modules",
            modules_desc: "Available functional modules",
            permissions_title: "Permission Definitions",
            permissions_desc: "All available permissions grouped by module",
            roles_title: "Role Definitions",
            roles_desc: "Team roles and their scope",
            loading: "Loading...",
            error: "Error loading data",
            retry: "Retry",
            enabled: "Enabled",
            disabled: "Disabled",
            no_data: "No data available"
        },
        zh: {
            title: "權限管理",
            subtitle: "管理模組、權限和角色設定",
            modules_title: "系統模組",
            modules_desc: "可用的功能模組",
            permissions_title: "權限定義",
            permissions_desc: "依模組分組的所有權限",
            roles_title: "角色定義",
            roles_desc: "團隊角色及其適用範圍",
            loading: "載入中...",
            error: "載入資料時發生錯誤",
            retry: "重試",
            enabled: "已啟用",
            disabled: "已停用",
            no_data: "沒有資料"
        }
    };

    const t = translations[language] || translations.zh;

    // Fetch data
    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const token = localStorage.getItem('google_token');
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            const [modulesRes, permissionsRes, rolesRes] = await Promise.all([
                fetch(`${API_URL}/api/permissions/admin/modules`, { headers }),
                fetch(`${API_URL}/api/permissions/admin/permissions`, { headers }),
                fetch(`${API_URL}/api/permissions/admin/roles`, { headers })
            ]);

            if (!modulesRes.ok || !permissionsRes.ok || !rolesRes.ok) {
                throw new Error('Failed to fetch permission data');
            }

            const [modulesData, permissionsData, rolesData] = await Promise.all([
                modulesRes.json(),
                permissionsRes.json(),
                rolesRes.json()
            ]);

            setModules(modulesData);
            setPermissions(permissionsData);
            setRoles(rolesData);
        } catch (err) {
            console.error('Permission fetch error:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Group permissions by module
    const permissionsByModule = permissions.reduce((acc, perm) => {
        const moduleId = perm.module_id || 'other';
        if (!acc[moduleId]) acc[moduleId] = [];
        acc[moduleId].push(perm);
        return acc;
    }, {});

    // Styles
    const styles = {
        container: {
            padding: '24px 0'
        },
        header: {
            marginBottom: '32px'
        },
        title: {
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: 'var(--text-primary)',
            marginBottom: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        subtitle: {
            fontSize: '0.875rem',
            color: 'var(--text-secondary)'
        },
        grid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '24px',
            marginBottom: '32px'
        },
        section: {
            backgroundColor: 'rgba(255,255,255,0.03)',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            overflow: 'hidden'
        },
        sectionHeader: {
            padding: '20px',
            borderBottom: '1px solid var(--glass-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        sectionIcon: {
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        },
        sectionTitle: {
            fontSize: '1rem',
            fontWeight: '600',
            color: 'var(--text-primary)'
        },
        sectionDesc: {
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            marginTop: '2px'
        },
        sectionBody: {
            padding: '16px'
        },
        moduleCard: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '10px',
            backgroundColor: 'rgba(255,255,255,0.02)',
            marginBottom: '8px',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
        },
        moduleInfo: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
        },
        moduleIcon: {
            fontSize: '1.5rem'
        },
        moduleName: {
            fontWeight: '500',
            color: 'var(--text-primary)'
        },
        moduleKey: {
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            fontFamily: 'monospace'
        },
        badge: (enabled) => ({
            padding: '4px 10px',
            borderRadius: '9999px',
            fontSize: '0.7rem',
            fontWeight: '600',
            backgroundColor: enabled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: enabled ? '#22c55e' : '#ef4444'
        }),
        permissionItem: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 12px',
            borderRadius: '8px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            marginBottom: '6px',
            fontSize: '0.875rem'
        },
        permissionKey: {
            fontFamily: 'monospace',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            backgroundColor: 'rgba(0,0,0,0.2)',
            padding: '2px 8px',
            borderRadius: '4px'
        },
        roleCard: {
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'rgba(255,255,255,0.02)',
            marginBottom: '12px'
        },
        roleName: {
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '4px'
        },
        roleKey: {
            fontSize: '0.75rem',
            color: '#3b82f6',
            fontFamily: 'monospace'
        },
        roleScope: {
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            marginTop: '4px'
        },
        expandedPerms: {
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px solid var(--glass-border)'
        },
        loadingContainer: {
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '48px',
            color: 'var(--text-secondary)'
        },
        errorContainer: {
            textAlign: 'center',
            padding: '32px',
            color: '#ef4444'
        },
        retryBtn: {
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
        }
    };

    if (loading) {
        return (
            <div style={styles.loadingContainer}>
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                {t.loading}
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.errorContainer}>
                <p>{t.error}: {error}</p>
                <button style={styles.retryBtn} onClick={fetchData}>{t.retry}</button>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Header */}
            <div style={styles.header}>
                <h2 style={styles.title}>
                    <FaKey style={{ color: '#f59e0b' }} />
                    {t.title}
                </h2>
                <p style={styles.subtitle}>{t.subtitle}</p>
            </div>

            {/* Modules & Roles Grid */}
            <div style={styles.grid}>
                {/* Modules Section */}
                <div style={styles.section}>
                    <div style={styles.sectionHeader}>
                        <div style={{ ...styles.sectionIcon, backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                            <FaCubes size={18} />
                        </div>
                        <div>
                            <div style={styles.sectionTitle}>{t.modules_title}</div>
                            <div style={styles.sectionDesc}>{t.modules_desc}</div>
                        </div>
                    </div>
                    <div style={styles.sectionBody}>
                        {modules.length > 0 ? modules.map(mod => (
                            <div
                                key={mod.id}
                                style={styles.moduleCard}
                                onClick={() => setExpandedModule(expandedModule === mod.id ? null : mod.id)}
                            >
                                <div style={styles.moduleInfo}>
                                    <span style={styles.moduleIcon}>{mod.icon || '📦'}</span>
                                    <div>
                                        <div style={styles.moduleName}>{mod.name}</div>
                                        <div style={styles.moduleKey}>{mod.key}</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={styles.badge(mod.enabled)}>
                                        {mod.enabled ? t.enabled : t.disabled}
                                    </span>
                                    {expandedModule === mod.id ? <FaChevronUp size={12} /> : <FaChevronDown size={12} />}
                                </div>
                            </div>
                        )) : (
                            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {t.no_data}
                            </div>
                        )}

                        {/* Expanded Module Permissions */}
                        {expandedModule && (
                            <div style={styles.expandedPerms}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                                    {t.permissions_title}:
                                </div>
                                {permissions
                                    .filter(p => {
                                        const mod = modules.find(m => m.id === expandedModule);
                                        return mod && p.key.startsWith(mod.key + ':');
                                    })
                                    .map(p => (
                                        <div key={p.id} style={styles.permissionItem}>
                                            <span style={{ color: 'var(--text-primary)' }}>{p.name}</span>
                                            <code style={styles.permissionKey}>{p.key}</code>
                                        </div>
                                    ))
                                }
                            </div>
                        )}
                    </div>
                </div>

                {/* Roles Section */}
                <div style={styles.section}>
                    <div style={styles.sectionHeader}>
                        <div style={{ ...styles.sectionIcon, backgroundColor: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>
                            <FaUserTag size={18} />
                        </div>
                        <div>
                            <div style={styles.sectionTitle}>{t.roles_title}</div>
                            <div style={styles.sectionDesc}>{t.roles_desc}</div>
                        </div>
                    </div>
                    <div style={styles.sectionBody}>
                        {roles.length > 0 ? roles.map(role => (
                            <div key={role.id} style={styles.roleCard}>
                                <div style={styles.roleName}>{role.name}</div>
                                <div style={styles.roleKey}>{role.key}</div>
                                <div style={styles.roleScope}>
                                    適用範圍: <span style={{ color: '#22c55e' }}>{role.scope}</span>
                                </div>
                            </div>
                        )) : (
                            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {t.no_data}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Stats Summary */}
            <div style={{
                display: 'flex',
                gap: '24px',
                flexWrap: 'wrap',
                padding: '16px',
                backgroundColor: 'rgba(255,255,255,0.02)',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)'
            }}>
                <div>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>模組數: </span>
                    <span style={{ color: '#3b82f6', fontWeight: 'bold' }}>{modules.length}</span>
                </div>
                <div>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>權限數: </span>
                    <span style={{ color: '#22c55e', fontWeight: 'bold' }}>{permissions.length}</span>
                </div>
                <div>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>角色數: </span>
                    <span style={{ color: '#a855f7', fontWeight: 'bold' }}>{roles.length}</span>
                </div>
            </div>

            {/* Divider */}
            <div style={{ height: '1px', backgroundColor: 'var(--glass-border)', margin: '24px 0' }}></div>

            {/* User Module Manager */}
            <UserModuleManager language={language} />
        </div>
    );
};

export default PermissionManager;
