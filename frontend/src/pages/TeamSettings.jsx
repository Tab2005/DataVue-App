import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { TeamService } from '../services/teamService';
import { FiSave, FiAlertTriangle, FiTrash2 } from 'react-icons/fi';

const TeamSettings = () => {
    const { language, selectedTeamId, user, teams, setTeams, setSelectedTeamId } = useOutletContext();
    const navigate = useNavigate();

    const [teamName, setTeamName] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // { type: 'success'|'error', msg }

    const t = {
        title: language === 'zh' ? '一般設定' : 'General Settings',
        subtitle: language === 'zh' ? '管理團隊的基本資訊' : 'Manage your team profile',
        team_name: language === 'zh' ? '團隊名稱' : 'Team Name',
        save: language === 'zh' ? '儲存變更' : 'Save Changes',
        danger_zone: language === 'zh' ? '危險區域' : 'Danger Zone',
        disband_team: language === 'zh' ? '解散團隊' : 'Disband Team',
        disband_desc: language === 'zh' ? '此操作無法復原。這將永久刪除團隊及其所有關聯資料 (成員、權限)。' : 'This action cannot be undone. This will permanently delete the team and all associated data.',
        confirm_disband: language === 'zh' ? '確定要解散團隊嗎？請輸入團隊名稱以確認：' : 'Are you sure you want to disband? Type team name to confirm:',
        confirm_warning: language === 'zh' ? '最終警告：此操作絕對無法復原！' : 'FINAL WARNING: This is absolutely irreversible.',
        success: language === 'zh' ? '更新成功' : 'Updated successfully',
        failed: language === 'zh' ? '更新失敗' : 'Update failed',
        processing: language === 'zh' ? '處理中...' : 'Processing...',
        not_owner: language === 'zh' ? '只有團隊擁有者可以執行此操作' : 'Only Team Owner can perform this action'
    };

    const currentTeam = teams?.find(t => t.id === selectedTeamId);
    const isOwner = currentTeam?.owner_id === user?.id;

    useEffect(() => {
        if (currentTeam) {
            setTeamName(currentTeam.name);
        }
    }, [currentTeam]);

    const handleUpdate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);
        try {
            const updatedTeam = await TeamService.updateTeam(selectedTeamId, teamName);
            // Update local state
            setTeams(teams.map(t => t.id === selectedTeamId ? updatedTeam : t));
            setStatus({ type: 'success', msg: t.success });
        } catch (err) {
            setStatus({ type: 'error', msg: err.message || t.failed });
        } finally {
            setLoading(false);
        }
    };

    const handleDisband = async () => {
        const confirmName = window.prompt(`${t.confirm_disband} ${currentTeam.name}`);
        if (confirmName !== currentTeam.name) {
            alert("Team name mismatch. Action cancelled.");
            return;
        }

        if (!window.confirm(t.confirm_warning)) return;

        setLoading(true);
        try {
            await TeamService.deleteTeam(selectedTeamId);
            // Remove from local list
            const remainingTeams = teams.filter(t => t.id !== selectedTeamId);
            setTeams(remainingTeams);

            // Redirect
            if (remainingTeams.length > 0) {
                // Switch to another team (e.g. first one)
                setSelectedTeamId(remainingTeams[0].id);
                // Also update URL to that team eventually, or just go home
                // Actually setSelectedTeamId might not persist without calling backend switching api if fully realized?
                // But for now context update + reload might be safe
                // Let's just navigate home
                navigate('/');
                window.location.reload(); // Force refresh to clean state
            } else {
                setSelectedTeamId(null);
                navigate('/');
                window.location.reload();
            }
        } catch (err) {
            alert(err.message);
            setLoading(false);
        }
    };

    if (!selectedTeamId) {
        return <div className="p-8">{language === 'zh' ? '請先選擇一個團隊' : 'Please select a team first.'}</div>;
    }

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>{t.title}</h1>
            <p className="mb-8" style={{ color: 'var(--text-secondary)' }}>{t.subtitle}</p>

            {/* General Section */}
            <div className="rounded-xl p-6 mb-8 border border-gray-800" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--glass-border)' }}>
                <form onSubmit={handleUpdate}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>{t.team_name}</label>
                        <input
                            type="text"
                            value={teamName}
                            onChange={(e) => setTeamName(e.target.value)}
                            disabled={!isOwner}
                            className="w-full p-3 rounded-lg border bg-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            style={{
                                backgroundColor: 'var(--bg-primary)',
                                borderColor: 'var(--glass-border)',
                                color: 'var(--text-primary)'
                            }}
                        />
                    </div>

                    {status && (
                        <div className={`mb-4 p-3 rounded ${status.type === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                            {status.msg}
                        </div>
                    )}

                    {isOwner && (
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={loading || teamName === currentTeam?.name}
                                className="flex items-center px-6 py-2 rounded-lg font-medium transition-colors"
                                style={{
                                    backgroundColor: 'var(--accent-primary)',
                                    color: 'white',
                                    opacity: (loading || teamName === currentTeam?.name) ? 0.5 : 1
                                }}
                            >
                                <FiSave className="mr-2" />
                                {loading ? t.processing : t.save}
                            </button>
                        </div>
                    )}
                </form>
            </div>

            {/* Danger Zone */}
            {isOwner && (
                <div className="rounded-xl p-6 border border-red-900/30" style={{ backgroundColor: 'rgba(239, 68, 68, 0.05)' }}>
                    <h2 className="text-xl font-bold mb-4 text-red-500 flex items-center">
                        <FiAlertTriangle className="mr-2" />
                        {t.danger_zone}
                    </h2>
                    <p className="mb-6 text-sm" style={{ color: 'var(--text-secondary)' }}>
                        {t.disband_desc}
                    </p>
                    <button
                        onClick={handleDisband}
                        disabled={loading}
                        className="flex items-center px-6 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
                    >
                        <FiTrash2 className="mr-2" />
                        {t.disband_team}
                    </button>
                </div>
            )}
            {!isOwner && (
                <div className="p-4 rounded-lg bg-gray-800 text-gray-400 text-sm text-center">
                    {t.not_owner}
                </div>
            )}
        </div>
    );
};

export default TeamSettings;
