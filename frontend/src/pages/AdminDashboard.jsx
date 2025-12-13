import React, { useState, useEffect } from 'react';
import { FaUsers, FaBuilding, FaTrash, FaShieldAlt } from 'react-icons/fa';
import { AdminService } from '../services/adminService';

const AdminDashboard = () => {
    const [stats, setStats] = useState({ user_count: 0, team_count: 0 });
    const [users, setUsers] = useState([]);
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('users');
    const [error, setError] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [statsData, usersData, teamsData] = await Promise.all([
                AdminService.getStats(),
                AdminService.getAllUsers(),
                AdminService.getAllTeams()
            ]);
            setStats(statsData || { user_count: 0, team_count: 0 });
            setUsers(Array.isArray(usersData) ? usersData : []);
            setTeams(Array.isArray(teamsData) ? teamsData : []);
        } catch (err) {
            console.error("Dashboard Load Error:", err);
            // Fix: Store error as string to prevent React crash
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm("Are you sure? This action is irreversible.")) return;
        try {
            await AdminService.deleteUser(userId);
            setUsers(users.filter(u => u.id !== userId));
            setStats(prev => ({ ...prev, user_count: prev.user_count - 1 }));
        } catch (err) {
            alert(err instanceof Error ? err.message : String(err));
        }
    };

    if (loading) return (
        <div className="p-8 text-center text-gray-400 flex flex-col items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
            Loading Admin Dashboard...
        </div>
    );

    if (error) return (
        <div className="p-8 text-center">
            <h2 className="text-2xl text-red-500 font-bold mb-2">Access Error</h2>
            <p className="text-gray-400 mb-4">{error}</p>
            <button
                onClick={fetchData}
                className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition text-white"
            >
                Retry
            </button>
        </div>
    );

    return (
        <div className="p-6 max-w-7xl mx-auto h-full overflow-y-auto">
            <div className="flex items-center mb-6">
                <FaShieldAlt className="text-blue-400 text-3xl mr-3" />
                <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Super Admin Dashboard</h1>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="glass-panel p-6 rounded-xl flex items-center justify-between" style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                    <div>
                        <p className="text-sm font-medium text-gray-400">Total Users</p>
                        <p className="text-3xl font-bold text-white">{stats.user_count}</p>
                    </div>
                    <div className="p-4 rounded-full bg-blue-500 bg-opacity-10">
                        <FaUsers className="text-2xl text-blue-500" />
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-xl flex items-center justify-between" style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                    <div>
                        <p className="text-sm font-medium text-gray-400">Total Teams</p>
                        <p className="text-3xl font-bold text-white">{stats.team_count}</p>
                    </div>
                    <div className="p-4 rounded-full bg-purple-500 bg-opacity-10">
                        <FaBuilding className="text-2xl text-purple-500" />
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex space-x-4 mb-6 border-b border-gray-700">
                <button
                    onClick={() => setActiveTab('users')}
                    className={`pb-2 px-4 transition font-medium ${activeTab === 'users' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-400 hover:text-gray-300'}`}
                >
                    All Users
                </button>
                <button
                    onClick={() => setActiveTab('teams')}
                    className={`pb-2 px-4 transition font-medium ${activeTab === 'teams' ? 'border-b-2 border-purple-500 text-purple-500' : 'text-gray-400 hover:text-gray-300'}`}
                >
                    All Teams
                </button>
            </div>

            {/* Content Table */}
            <div className="rounded-xl shadow-sm overflow-hidden" style={{ backgroundColor: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)' }}>
                {activeTab === 'users' ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-black bg-opacity-20 text-gray-400 uppercase text-xs tracking-wider">
                                <tr>
                                    <th className="p-4">Name</th>
                                    <th className="p-4">Email</th>
                                    <th className="p-4">Role</th>
                                    <th className="p-4">Joined</th>
                                    <th className="p-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {users.length > 0 ? users.map(user => (
                                    <tr key={user.id} className="hover:bg-white hover:bg-opacity-5 transition group">
                                        <td className="p-4 font-medium text-white flex items-center gap-2">
                                            {user.is_super_admin && <FaShieldAlt className="text-yellow-500" title="Super Admin" />}
                                            {user.name}
                                        </td>
                                        <td className="p-4 text-gray-300">{user.email}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold ${user.is_super_admin ? 'bg-yellow-900 text-yellow-200' :
                                                    user.role === 'admin' ? 'bg-red-900 text-red-200' :
                                                        'bg-gray-700 text-gray-300'
                                                }`}>
                                                {user.is_super_admin ? 'SUPER ADMIN' : (user.role || 'VIEWER').toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-400 text-sm">
                                            {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="p-4 text-right">
                                            {!user.is_super_admin && (
                                                <button
                                                    onClick={() => handleDeleteUser(user.id)}
                                                    className="text-gray-600 hover:text-red-400 transition opacity-0 group-hover:opacity-100"
                                                    title="Force Delete User"
                                                >
                                                    <FaTrash />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan="5" className="p-8 text-center text-gray-500">No users found</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-black bg-opacity-20 text-gray-400 uppercase text-xs tracking-wider">
                                <tr>
                                    <th className="p-4">Team Name</th>
                                    <th className="p-4">Owner ID</th>
                                    <th className="p-4">Created At</th>
                                    <th className="p-4 text-right">Members</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {teams.length > 0 ? teams.map(team => (
                                    <tr key={team.id} className="hover:bg-white hover:bg-opacity-5 transition">
                                        <td className="p-4 font-bold text-white">{team.name}</td>
                                        <td className="p-4 text-gray-500 font-mono text-xs">{team.owner_id}</td>
                                        <td className="p-4 text-gray-400 text-sm">
                                            {team.created_at ? new Date(team.created_at).toLocaleString() : '-'}
                                        </td>
                                        <td className="p-4 text-right text-gray-400">
                                            {/* Could add member count here if available */}
                                            -
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan="4" className="p-8 text-center text-gray-500">No teams found</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;
