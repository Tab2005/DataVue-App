import React, { useEffect, useState } from 'react';
import { UserService } from '../services/userService';
import { TeamService } from '../services/teamService';
import InviteModal from '../components/InviteModal';
import { FaUserPlus, FaEdit, FaTrash, FaShieldAlt, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

const UserManagement = ({ language, selectedTeamId, user, teams, embedded = false }) => {
    // 2. Define Translations
    const translations = {
        en: {
            title: selectedTeamId ? "Team Members" : "User Management",
            subtitle: selectedTeamId ? "Manage your team members" : "Manage system users",
            invite: "Invite Member",
            invite_alert: "Tell new users to Sign In with Google. Their account will appear here pending approval.",
            loading: "Loading Members...",
            error_permission: "Failed to load info. You might not have permissions.",
            confirm_delete: "Are you sure you want to remove this user?",
            failed_delete: "Failed to remove user",
            failed_save: "Failed to save user",

            // Table Headers
            th_user: "User",
            th_role: "Role",
            th_status: "Status",
            th_joined: "Joined",
            th_actions: "Actions",

            // Empty/Unknown
            unknown: "Unknown",
            no_email: "No Email",

            // Modal
            modal_title: "Edit Permissions",
            modal_role: "Role",
            modal_status: "Status",
            btn_cancel: "Cancel",
            btn_save: "Save Changes",

            // Attributes
            role_viewer: "Viewer",
            role_member: "Member",
            role_admin: "Admin",
            status_active: "Active",
            status_suspended: "Suspended"
        },
        zh: {
            title: selectedTeamId ? "團隊成員" : "成員管理",
            subtitle: selectedTeamId ? "管理您的團隊成員" : "管理系統使用者",
            invite: "邀請成員",
            invite_alert: "請新成員直接使用 Google 登入系統。他們的帳號將會顯示在此列表中，等待您的核准。",
            loading: "讀取列表中...",
            error_permission: "無法載入資訊。您可能沒有權限。",
            confirm_delete: "您確定要移除這位成員嗎？",
            failed_delete: "移除失敗",
            failed_save: "儲存失敗",

            th_user: "成員",
            th_role: "角色權限",
            th_status: "狀態",
            th_joined: "加入時間",
            th_actions: "操作",

            unknown: "未知",
            no_email: "無 Email",

            modal_title: "編輯權限",
            modal_role: "角色",
            modal_status: "狀態",
            btn_cancel: "取消",
            btn_save: "儲存變更",

            role_viewer: "檢視者",
            role_member: "成員",
            role_admin: "管理員",
            status_active: "啟用中",
            status_suspended: "已停用"
        }
    };

    const t = translations[language] || translations.en;

    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        role: 'viewer',
        status: 'active'
    });

    // --- STYLES (Vanilla CSS replacement for Tailwind) ---
    const styles = {
        container: {
            width: '100%',
            height: '100%',
            overflowY: embedded ? 'visible' : 'auto',
            padding: embedded ? '0' : '24px',
            maxWidth: embedded ? 'none' : '1280px',
            margin: embedded ? '0' : '0 auto'
        },
        header: {
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        },
        inviteBtnContainer: {
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'flex-end'
        },
        inviteBtn: {
            display: 'flex',
            alignItems: 'center',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '8px',
            fontWeight: '500',
            backgroundColor: 'var(--accent-primary)',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            transition: 'transform 0.1s'
        },
        errorBox: {
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderLeft: '4px solid #ef4444',
            padding: '16px',
            marginBottom: '24px',
            color: '#ef4444',
            fontWeight: 'bold'
        },
        tableContainer: {
            borderRadius: '16px',
            overflow: 'hidden',
            border: '1px solid var(--glass-border)',
            padding: 0,
            background: embedded ? 'transparent' : 'var(--glass-bg)', // Use full glass only if not embedded (embedded parent has styles)
        },
        table: {
            width: '100%',
            textAlign: 'left',
            borderCollapse: 'collapse'
        },
        th: {
            padding: '16px',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-secondary)',
            background: '#242526', // Dark header
            borderBottom: '1px solid var(--glass-border)'
        },
        td: {
            padding: '16px',
            borderBottom: '1px solid rgba(255,255,255,0.05)'
        },
        badge: (bgColor, textColor) => ({
            padding: '4px 8px',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: '600',
            backgroundColor: bgColor,
            color: textColor,
            display: 'inline-block'
        }),
        actionBtn: {
            padding: '8px',
            borderRadius: '6px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            transition: 'background 0.2s',
            marginLeft: '8px'
        },
        modalOverlay: {
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            backdropFilter: 'blur(4px)'
        },
        modalContent: {
            width: '384px', // w-96
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        },
        input: {
            width: '100%',
            borderRadius: '8px',
            padding: '12px',
            outline: 'none',
            backgroundColor: 'rgba(255,255,255,0.05)',
            color: 'var(--text-primary)',
            border: '1px solid var(--glass-border)',
            marginTop: '8px'
        }
    };

    const fetchUsers = async () => {
        try {
            setLoading(true);
            let data = [];

            if (selectedTeamId) {
                const members = await TeamService.getTeamMembers(selectedTeamId);
                data = members.map(m => ({
                    id: m.user_id,
                    name: m.user?.name,
                    email: m.user?.email,
                    role: m.role,
                    status: m.user?.status,
                    created_at: m.joined_at,
                    _member: m
                }));
            } else {
                data = await UserService.getAllUsers();
            }

            setUsers(data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError(t.error_permission);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedTeamId || !embedded) {
            fetchUsers();
        }
    }, [language, selectedTeamId]);

    const handleEdit = (user) => {
        setEditingUser(user);
        setFormData({ role: user.role, status: user.status });
        setIsModalOpen(true);
    };

    const handleDelete = async (userId) => {
        const confirmMsg = selectedTeamId
            ? (language === 'zh' ? '確定要將此成員移出團隊嗎？' : 'Remove this member from the team?')
            : t.confirm_delete;

        if (!window.confirm(confirmMsg)) return;

        try {
            if (selectedTeamId) {
                await TeamService.removeMember(selectedTeamId, userId);
            } else {
                await UserService.deleteUser(userId);
            }
            setUsers(users.filter(u => u.id !== userId));
        } catch (err) {
            console.error(err);
            alert(err.message || t.failed_delete);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            if (editingUser) {
                if (selectedTeamId) {
                    await TeamService.updateMemberRole(selectedTeamId, editingUser.id, formData.role);
                    setUsers(users.map(u => u.id === editingUser.id ? { ...u, role: formData.role } : u));
                } else {
                    const updatedUser = await UserService.updateUser(editingUser.id, formData);
                    setUsers(users.map(u => u.id === editingUser.id ? updatedUser : u));
                }
            } else {
                alert(t.invite_alert);
                return;
            }
            setIsModalOpen(false);
            setEditingUser(null);
        } catch (err) {
            console.error(err);
            alert(err.message || t.failed_save);
        }
    };

    const RoleBadge = ({ role }) => {
        let bg = '#f3f4f6'; // gray-100
        let text = '#1f2937'; // gray-800

        if (role === 'admin') {
            bg = '#fee2e2'; // red-100
            text = '#991b1b'; // red-800
        } else if (role === 'member') {
            bg = '#dbeafe'; // blue-100
            text = '#1e40af'; // blue-800
        }

        return (
            <span style={styles.badge(bg, text)}>
                {role.toUpperCase()}
            </span>
        );
    };

    const StatusBadge = ({ status }) => {
        const isActive = status === 'active';
        return (
            <span style={{ display: 'flex', alignItems: 'center', color: isActive ? '#16a34a' : '#dc2626', fontWeight: '500' }}>
                {isActive ? <FaCheckCircle style={{ marginRight: '4px' }} /> : <FaTimesCircle style={{ marginRight: '4px' }} />}
                {isActive ? t.status_active : t.status_suspended}
            </span>
        );
    };

    const currentTeam = teams?.find(t => t.id === selectedTeamId);
    const myMemberInfo = users.find(u => u.id === user?.id);
    const isTeamAdmin = myMemberInfo?.role === 'admin';
    const canManage = !selectedTeamId ? user?.is_super_admin : isTeamAdmin;

    if (loading && !users.length) return <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>{t.loading}</div>;

    return (
        <div style={styles.container}>
            {!embedded && (
                <div style={styles.header}>
                    <div>
                        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.title}</h1>
                        <p style={{ color: 'var(--text-secondary)' }}>{t.subtitle}</p>
                    </div>
                </div>
            )}

            {/* Invite Button */}
            {canManage && (
                <div style={styles.inviteBtnContainer}>
                    <button
                        onClick={() => {
                            if (selectedTeamId) {
                                setIsInviteModalOpen(true);
                            } else {
                                alert(t.invite_alert);
                            }
                        }}
                        style={styles.inviteBtn}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                        <FaUserPlus style={{ marginRight: '8px' }} /> {t.invite}
                    </button>
                </div>
            )}

            {error && <div style={styles.errorBox}>{error}</div>}

            <div className="glass-panel" style={styles.tableContainer}>
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>{t.th_user}</th>
                                <th style={styles.th}>{t.th_role}</th>
                                <th style={styles.th}>{t.th_status}</th>
                                <th style={styles.th}>{t.th_joined}</th>
                                {canManage && <th style={{ ...styles.th, textAlign: 'right' }}>{t.th_actions}</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user, idx) => (
                                <tr key={user.id} style={{
                                    ...styles.td,
                                    backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                }}>
                                    <td style={styles.td}>
                                        <div style={{ display: 'flex', alignItems: 'center' }}>
                                            <div style={{
                                                height: '40px', width: '40px', borderRadius: '50%',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontWeight: 'bold', marginRight: '12px',
                                                backgroundColor: 'rgba(45, 136, 255, 0.2)',
                                                color: 'var(--accent-primary)',
                                                border: '1px solid rgba(45, 136, 255, 0.3)'
                                            }}>
                                                {user.name ? user.name.charAt(0).toUpperCase() : '?'}
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{user.name || t.unknown}</div>
                                                <div style={{ fontSize: '0.75rem', marginTop: '2px', color: 'var(--text-secondary)' }}>{user.email || t.no_email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td style={styles.td}><RoleBadge role={user.role} /></td>
                                    <td style={styles.td}><StatusBadge status={user.status} /></td>
                                    <td style={{ ...styles.td, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                    </td>
                                    {canManage && (
                                        <td style={{ ...styles.td, textAlign: 'right' }}>
                                            {selectedTeamId && currentTeam?.owner_id === user.id ? (
                                                <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', backgroundColor: '#374151', color: '#9ca3af', border: '1px solid #4b5563' }}>Owner</span>
                                            ) : (
                                                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px' }}>
                                                    <button onClick={() => handleEdit(user)} style={styles.actionBtn} title="Edit">
                                                        <FaEdit size={16} />
                                                    </button>
                                                    <button onClick={() => handleDelete(user.id)} style={styles.actionBtn} title="Delete">
                                                        <FaTrash size={16} />
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Edit Modal */}
            {isModalOpen && (
                <div style={styles.modalOverlay}>
                    <div className="glass-panel" style={styles.modalContent}>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
                            <FaShieldAlt style={{ color: '#3b82f6' }} />
                            {selectedTeamId ? (language === 'zh' ? '編輯成員權限' : 'Edit Team Role') : t.modal_title}
                        </h2>
                        <form onSubmit={handleSave}>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.modal_role}</label>
                                <select
                                    value={formData.role}
                                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                    style={styles.input}
                                >
                                    <option value="viewer" style={{ color: 'black' }}>{t.role_viewer}</option>
                                    <option value="member" style={{ color: 'black' }}>{t.role_member}</option>
                                    <option value="admin" style={{ color: 'black' }}>{t.role_admin}</option>
                                </select>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    style={{ padding: '8px 16px', borderRadius: '8px', background: 'transparent', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer' }}
                                >
                                    {t.btn_cancel}
                                </button>
                                <button
                                    type="submit"
                                    style={{ padding: '8px 24px', borderRadius: '8px', background: 'var(--accent-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                                >
                                    {t.btn_save}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Invite Modal uses its own styles? Let's assume it might break too but one step at a time. */}
            <InviteModal
                isOpen={isInviteModalOpen}
                onClose={() => setIsInviteModalOpen(false)}
                teamId={selectedTeamId}
                language={language}
            />
        </div >
    );
};

export default UserManagement;
