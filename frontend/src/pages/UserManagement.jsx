import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { UserService } from '../services/userService';
import { TeamService } from '../services/teamService';
import InviteModal from '../components/InviteModal';
import { FaUserPlus, FaEdit, FaTrash, FaShieldAlt, FaUserSlash, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

const UserManagement = () => {
    // 1. Get language & Team Context from Layout
    const { language, selectedTeamId, user, teams } = useOutletContext();

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

            // Table Headers
            th_user: "成員",
            th_role: "角色權限",
            th_status: "狀態",
            th_joined: "加入時間",
            th_actions: "操作",

            // Empty/Unknown
            unknown: "未知",
            no_email: "無 Email",

            // Modal
            modal_title: "編輯權限",
            modal_role: "角色",
            modal_status: "狀態",
            btn_cancel: "取消",
            btn_save: "儲存變更",

            // Attributes
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
    const [isInviteModalOpen, setIsInviteModalOpen] = useState(false); // New Invite Modal State
    const [editingUser, setEditingUser] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        role: 'viewer',
        status: 'active'
    });

    const fetchUsers = async () => {
        try {
            setLoading(true);
            let data = [];

            if (selectedTeamId) {
                // Fetch Team Members
                const members = await TeamService.getTeamMembers(selectedTeamId);
                // Map to flat structure for table
                data = members.map(m => ({
                    id: m.user_id, // Key ID
                    name: m.user?.name,
                    email: m.user?.email,
                    role: m.role, // Team Role
                    status: m.user?.status,
                    created_at: m.joined_at,
                    // Store original for edit
                    _member: m
                }));
            } else {
                // Fetch All Users (Super Admin)
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
        fetchUsers();
    }, [language, selectedTeamId]); // Reload if language or Team changes

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
                // Remove from Team
                await TeamService.removeMember(selectedTeamId, userId);
            } else {
                // Delete System User
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
                    // Update Team Role
                    // Note: Team Member doesn't have 'status', only 'role'
                    await TeamService.updateMemberRole(selectedTeamId, editingUser.id, formData.role);

                    // Update user list state locally
                    setUsers(users.map(u => u.id === editingUser.id ? { ...u, role: formData.role } : u));
                } else {
                    // Update System User
                    const updatedUser = await UserService.updateUser(editingUser.id, formData);
                    setUsers(users.map(u => u.id === editingUser.id ? updatedUser : u));
                }
            } else {
                // Create/Invite logic
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
        const colors = {
            admin: 'bg-red-100 text-red-800',
            member: 'bg-blue-100 text-blue-800',
            viewer: 'bg-gray-100 text-gray-800'
        };
        return (
            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[role] || colors.viewer}`}>
                {role.toUpperCase()}
            </span>
        );
    };

    const StatusBadge = ({ status }) => {
        return status === 'active' ? (
            <span className="flex items-center text-green-600 font-medium">
                <FaCheckCircle className="mr-1" /> {t.status_active}
            </span>
        ) : (
            <span className="flex items-center text-red-600 font-medium">
                <FaTimesCircle className="mr-1" /> {t.status_suspended}
            </span>
        );
    };



    // Calculate Permissions
    const currentTeam = teams?.find(t => t.id === selectedTeamId);
    const myMemberInfo = users.find(u => u.id === user?.id);
    const isTeamAdmin = myMemberInfo?.role === 'admin';
    // Logic: 
    // - If NO selectedTeamId (System Mode) -> Only Super Admin sees this page anyway (protected route?) actually super admin dashboard is distinct. 
    //   Wait, UserManagement is linked from Settings -> Users. 
    //   If I am a regular user, I shouldn't see System Users. 
    //   If I am in Team Mode, I see Team Members.
    const canManage = !selectedTeamId ? user?.is_super_admin : isTeamAdmin;

    if (loading) return <div className="p-8 text-center" style={{ color: 'var(--text-secondary)' }}>{t.loading}</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto h-full overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{t.title}</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>{t.subtitle}</p>
                </div>
            </div>
            {/* Invite Button - Simplified prompt for now */}
            {canManage && (
                <button
                    onClick={() => {
                        if (selectedTeamId) {
                            setIsInviteModalOpen(true);
                        } else {
                            alert(t.invite_alert);
                        }
                    }}
                    className="flex items-center text-white px-4 py-2 rounded-lg transition"
                    style={{ backgroundColor: 'var(--accent-primary)' }}
                >
                    <FaUserPlus className="mr-2" /> {t.invite}
                </button>
            )}


            {
                error && (
                    <div className="bg-red-500 bg-opacity-10 border-l-4 border-red-500 p-4 mb-6">
                        <p className="text-red-500 font-bold">{error}</p>
                    </div>
                )
            }

            <div className="rounded-xl shadow-sm overflow-hidden" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--glass-border)' }}>
                <table className="w-full text-left border-collapse">
                    <thead style={{ borderBottom: '1px solid var(--glass-border)' }}>
                        <tr>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_user}</th>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_role}</th>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_status}</th>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_joined}</th>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_status}</th>
                            <th className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{t.th_joined}</th>
                            {canManage && <th className="p-4 text-sm font-semibold text-right" style={{ color: 'var(--text-secondary)' }}>{t.th_actions}</th>}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800" style={{ borderColor: 'var(--glass-border)' }}>
                        {users.map(user => (
                            <tr key={user.id} className="transition" style={{ borderBottom: '1px solid var(--glass-border)' }}
                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                            >
                                <td className="p-4">
                                    <div className="flex items-center">
                                        <div className="h-10 w-10 rounded-full flex items-center justify-center font-bold mr-3"
                                            style={{ backgroundColor: 'rgba(45, 136, 255, 0.2)', color: 'var(--accent-primary)' }}>
                                            {user.name ? user.name.charAt(0).toUpperCase() : '?'}
                                        </div>
                                        <div>
                                            <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{user.name || t.unknown}</div>
                                            <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user.email || t.no_email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4"><RoleBadge role={user.role} /></td>
                                <td className="p-4"><StatusBadge status={user.status} /></td>
                                <td className="p-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                </td>
                                {canManage && (
                                    <td className="p-4 text-right">
                                        {/* Cannot edit/delete Owner */}
                                        {selectedTeamId && currentTeam?.owner_id === user.id ? (
                                            <span className="text-xs text-gray-500 italic">Owner</span>
                                        ) : (
                                            <>
                                                <button
                                                    onClick={() => handleEdit(user)}
                                                    className="mx-2 transition"
                                                    style={{ color: 'var(--text-secondary)' }}
                                                    title="Edit Role"
                                                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent-primary)'}
                                                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                                                >
                                                    <FaEdit />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(user.id)}
                                                    className="mx-2 transition hover:text-red-500"
                                                    style={{ color: 'var(--text-secondary)' }}
                                                    title="Delete User"
                                                >
                                                    <FaTrash />
                                                </button>
                                            </>
                                        )}
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Edit Modal */}
            {
                isModalOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 backdrop-blur-sm">
                        <div className="rounded-lg p-6 w-96 shadow-xl" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--glass-border)' }}>
                            <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
                                {selectedTeamId ? (language === 'zh' ? '編輯成員權限' : 'Edit Team Role') : t.modal_title}
                            </h2>
                            <form onSubmit={handleSave}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{t.modal_role}</label>
                                    <select
                                        value={formData.role}
                                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                        className="w-full rounded-md p-2 outline-none"
                                        style={{
                                            backgroundColor: 'var(--bg-primary)',
                                            color: 'var(--text-primary)',
                                            borderColor: 'var(--glass-border)',
                                            borderWidth: '1px'
                                        }}
                                    >
                                        <option value="viewer">{t.role_viewer}</option>
                                        <option value="member">{t.role_member}</option>
                                        <option value="admin">{t.role_admin}</option>
                                    </select>
                                </div>
                                <div className="mb-6">
                                    {/* Only show Status for System Admin (Global User Edit) */}
                                    {!selectedTeamId && (
                                        <>
                                            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{t.modal_status}</label>
                                            <select
                                                value={formData.status}
                                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                                className="w-full rounded-md p-2 outline-none"
                                                style={{
                                                    backgroundColor: 'var(--bg-primary)',
                                                    color: 'var(--text-primary)',
                                                    borderColor: 'var(--glass-border)',
                                                    borderWidth: '1px'
                                                }}
                                            >
                                                <option value="active">{t.status_active}</option>
                                                <option value="suspended">{t.status_suspended}</option>
                                            </select>
                                        </>
                                    )}
                                </div>
                                <div className="flex justify-end space-x-2">
                                    <button
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="px-4 py-2 rounded-md transition"
                                        style={{ color: 'var(--text-secondary)', backgroundColor: 'transparent' }}
                                        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
                                        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                                    >
                                        {t.btn_cancel}
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-4 py-2 text-white rounded-md transition"
                                        style={{ backgroundColor: 'var(--accent-primary)' }}
                                    >
                                        {t.btn_save}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )
            }
            {/* Invite Modal */}
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
