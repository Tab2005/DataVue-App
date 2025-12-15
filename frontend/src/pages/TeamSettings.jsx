import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { TeamService } from '../services/teamService';
import { FiSave, FiAlertTriangle, FiTrash2, FiUsers, FiSettings } from 'react-icons/fi';
import UserManagement from './UserManagement';
import AdAccountSelector from '../components/AdAccountSelector';

const TeamSettings = () => {
    const { language, selectedTeamId, user, teams, setTeams, setSelectedTeamId, isMobile } = useOutletContext();
    const navigate = useNavigate();

    // General Settings State
    const [teamName, setTeamName] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // { type: 'success'|'error', msg }

    const t = {
        title: language === 'zh' ? '團隊設定' : 'Team Settings',
        subtitle: language === 'zh' ? '管理您的團隊資訊與成員' : 'Manage your team profile and members',

        // Section Headers
        tab_general: language === 'zh' ? '一般設定' : 'General Settings',
        tab_members: language === 'zh' ? '團隊成員' : 'Team Members',

        // General Form
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
            const remainingTeams = teams.filter(t => t.id !== selectedTeamId);
            setTeams(remainingTeams);

            if (remainingTeams.length > 0) {
                setSelectedTeamId(remainingTeams[0].id);
                navigate('/');
                window.location.reload();
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
        return <div style={{ padding: '32px' }}>{language === 'zh' ? '請先選擇一個團隊' : 'Please select a team first.'}</div>;
    }

    // Styles Objects (Replacements for Tailwind)
    const styles = {
        container: {
            maxWidth: '1024px',
            margin: '0 auto',
            margin: '0 auto',
            padding: isMobile ? '16px' : '48px 32px',
            display: 'flex',
            flexDirection: 'column',
            gap: '32px'
        },
        header: {
            marginBottom: '8px'
        },
        sectionHeader: {
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            marginBottom: '24px'
        },
        iconBox: (color) => ({
            padding: '12px',
            borderRadius: '12px',
            backgroundColor: color === 'blue' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(168, 85, 247, 0.1)',
            color: color === 'blue' ? '#3b82f6' : '#a855f7', // Blue-500 or Purple-500
            border: `1px solid ${color === 'blue' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(168, 85, 247, 0.2)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }),
        divider: {
            position: 'relative',
            height: '1px',
            width: '100%',
            backgroundColor: 'var(--glass-border)'
        },
        input: {
            width: '100%',
            padding: '16px',
            borderRadius: '12px',
            border: '1px solid var(--glass-border)',
            backgroundColor: 'rgba(0,0,0,0.2)',
            color: 'var(--text-primary)',
            fontSize: '1rem',
            outline: 'none',
            transition: 'all 0.2s',
        },
        buttonPrimary: {
            display: 'flex',
            alignItems: 'center',
            padding: '14px 32px',
            borderRadius: '12px',
            fontWeight: 'bold',
            backgroundColor: 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)',
            transition: 'transform 0.1s, opacity 0.2s'
        },
        buttonDanger: {
            display: 'flex',
            alignItems: 'center',
            padding: '12px 24px',
            borderRadius: '12px',
            fontWeight: 'bold',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: '#ef4444',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            border: '1px solid transparent'
        },
        statusBox: (type) => ({
            marginBottom: '24px',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            backgroundColor: type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: type === 'success' ? '#22c55e' : '#ef4444',
            border: `1px solid ${type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
        }),
        dangerZone: {
            backgroundColor: 'rgba(239, 68, 68, 0.03)',
            borderRadius: '24px',
            padding: isMobile ? '20px' : '32px',
            border: '1px solid rgba(239, 68, 68, 0.2)'
        }
    };

    return (
        <div style={styles.container}>
            {/* Page Header */}
            <div style={styles.header}>
                <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>{t.title}</h1>
                <p style={{ fontSize: '1.125rem', color: 'var(--text-secondary)' }}>{t.subtitle}</p>
            </div>

            {/* SECTION 1: MEMBERS */}
            <section className="animate-fade-in">
                {/* Section Header */}
                <div style={styles.sectionHeader}>
                    <div style={styles.iconBox('blue')}>
                        <FiUsers size={20} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.tab_members}</h2>
                        <p style={{ fontSize: '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                            {language === 'zh' ? '管理團隊成員權限與邀請' : 'Manage team access and invitations'}
                        </p>
                    </div>
                </div>

                {/* Content */}
                <UserManagement
                    embedded={true}
                    language={language}
                    selectedTeamId={selectedTeamId}
                    user={user}
                    teams={teams}
                    isMobile={isMobile}
                />
            </section>

            {/* Divider */}
            <div style={styles.divider}></div>

            {/* SECTION 2: GENERAL SETTINGS */}
            <section className="animate-fade-in">
                {/* Section Header */}
                <div style={styles.sectionHeader}>
                    <div style={styles.iconBox('purple')}>
                        <FiSettings size={20} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.tab_general}</h2>
                        <p style={{ fontSize: '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                            {language === 'zh' ? '基本資料設定' : 'Basic profile settings'}
                        </p>
                    </div>
                </div>

                {/* Glass Panel Form */}
                <div className="glass-panel" style={{ padding: isMobile ? '20px' : '40px', borderRadius: '24px' }}>
                    <form onSubmit={handleUpdate}>
                        <div style={{ marginBottom: '32px', maxWidth: '576px' }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '12px', marginLeft: '4px', color: 'var(--text-secondary)' }}>
                                {t.team_name}
                            </label>
                            <input
                                type="text"
                                value={teamName}
                                onChange={(e) => setTeamName(e.target.value)}
                                disabled={!isOwner}
                                style={styles.input}
                                onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                                onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
                            />
                        </div>

                        {status && (
                            <div style={styles.statusBox(status.type)}>
                                {status.type === 'success' ? <FiSave /> : <FiAlertTriangle />}
                                <span style={{ fontWeight: '500' }}>{status.msg}</span>
                            </div>
                        )}

                        {isOwner && (
                            <div>
                                <button
                                    type="submit"
                                    disabled={loading || teamName === currentTeam?.name}
                                    style={{
                                        ...styles.buttonPrimary,
                                        cursor: (loading || teamName === currentTeam?.name) ? 'not-allowed' : 'pointer',
                                        opacity: (loading || teamName === currentTeam?.name) ? 0.5 : 1
                                    }}
                                    onMouseOver={(e) => { if (!e.target.disabled) e.currentTarget.style.transform = 'translateY(-2px)' }}
                                    onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)' }}
                                >
                                    <FiSave style={{ marginRight: '8px' }} />
                                    {loading ? t.processing : t.save}
                                </button>
                            </div>
                        )}
                        {!isOwner && (
                            <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: 'rgba(31, 41, 55, 0.5)', color: '#9ca3af', fontSize: '0.875rem', border: '1px solid #374151', display: 'inline-block', fontWeight: '500' }}>
                                {t.not_owner}
                            </div>
                        )}
                    </form>
                </div>

            </section >

            {/* SECTION 2.5: AD ACCOUNT ACCESS (Owner Only) */}
            {
                isOwner && (
                    <section className="animate-fade-in">
                        <div style={styles.sectionHeader}>
                            <div style={styles.iconBox('blue')}>
                                <FiSettings size={20} />
                            </div>
                            <div>
                                <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.tab_ad_accounts || (language === 'zh' ? '廣告帳號授權' : 'Ad Account Access')}</h2>
                                <p style={{ fontSize: '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                                    {language === 'zh' ? '選擇團隊成員可見的廣告帳號' : 'Select ad accounts visible to team members'}
                                </p>
                            </div>
                        </div>

                        <div className="glass-panel" style={{ padding: isMobile ? '20px' : '40px', borderRadius: '24px' }}>
                            <AdAccountSelector
                                teamId={selectedTeamId}
                                initialSelected={currentTeam?.visible_ad_account_ids}
                                teamName={teamName} // Trigger reload if needed
                                language={language}
                                styles={styles}
                            />
                        </div>
                    </section>
                )
            }

            {/* SECTION 3: DANGER ZONE */}
            {
                isOwner && (
                    <section className="animate-fade-in" style={{ paddingTop: '16px' }}>
                        <div style={styles.dangerZone}>
                            <h2 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '16px', color: '#ef4444', display: 'flex', alignItems: 'center' }}>
                                <FiAlertTriangle style={{ marginRight: '12px' }} size={20} />
                                {t.danger_zone}
                            </h2>
                            <p style={{ marginBottom: '32px', fontSize: '0.875rem', lineHeight: '1.625', maxWidth: '42rem', color: 'var(--text-secondary)', opacity: 0.8 }}>
                                {t.disband_desc}
                            </p>
                            <button
                                onClick={handleDisband}
                                disabled={loading}
                                style={styles.buttonDanger}
                                onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#ef4444'; e.currentTarget.style.color = 'white'; }}
                                onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)'; e.currentTarget.style.color = '#ef4444'; }}
                            >
                                <FiTrash2 style={{ marginRight: '8px' }} />
                                {t.disband_team}
                            </button>
                        </div>
                    </section>
                )
            }
        </div >
    );
};

export default TeamSettings;
