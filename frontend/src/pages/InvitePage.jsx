import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TeamService } from '../services/teamService';
import { FiUsers, FiCheckCircle, FiAlertTriangle } from 'react-icons/fi';

const InvitePage = () => {
    const { code } = useParams();
    const navigate = useNavigate();

    // Language State (Default ZH)
    const [language, setLanguage] = useState('zh');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [inviteInfo, setInviteInfo] = useState(null);
    const [processing, setProcessing] = useState(false);

    // Auth Check
    const token = localStorage.getItem('google_token');

    // Translation Dictionary
    const t = {
        zh: {
            loading: "正在讀取邀請資訊...",
            errorTitle: "邀請連結已失效",
            errorDesc: "此邀請連結已過期或無法使用，請聯繫管理員重新發送。",
            goHome: "回首頁",
            joinTitle: "加入團隊",
            invitedText: "您已受邀加入此工作區。",
            invitedBy: "邀請人：",
            joining: "正在加入...",
            accept: "接受邀請",
            loginAccept: "登入並接受",
            success: "成功加入團隊！"
        },
        en: {
            loading: "Loading Invite...",
            errorTitle: "Invite Expired or Invalid",
            errorDesc: "This invitation link is no longer valid. Please ask the administrator for a new one.",
            goHome: "Go Home",
            joinTitle: "Join Team",
            invitedText: "You have been invited to join this workspace.",
            invitedBy: "Invited by:",
            joining: "Joining...",
            accept: "Accept Invite",
            loginAccept: "Login to Accept",
            success: "Successfully joined team!"
        }
    };

    const txt = t[language] || t.zh;

    useEffect(() => {
        // Robust Code Extraction
        let inviteCode = code;
        if (!inviteCode) {
            // Fallback: extract from pathname
            const parts = window.location.pathname.split('/');
            inviteCode = parts[parts.length - 1];
        }

        const check = async () => {
            try {
                const info = await TeamService.checkInvite(inviteCode);
                setInviteInfo(info);
            } catch (err) {
                setError(`${err.message} (Code: ${inviteCode})`);
            } finally {
                setLoading(false);
            }
        };
        if (inviteCode) check();
        else {
            setError("No invite code found in URL");
            setLoading(false);
        }
    }, [code]);

    const handleJoin = async () => {
        if (!token) {
            // Redirect to login with return path
            const returnUrl = encodeURIComponent(window.location.pathname);
            window.location.href = `/login?return_to=${returnUrl}`;
            return;
        }

        setProcessing(true);
        try {
            const res = await TeamService.acceptInvite(code);
            if (res.team_id) {
                localStorage.setItem('selected_team_id', res.team_id);
            }
            alert(txt.success);
            navigate('/');
            window.location.reload();
        } catch (err) {
            alert(err.message);
            setProcessing(false);
        }
    };

    if (loading) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111827', color: 'white' }}>
                {txt.loading}
            </div>
        );
    }

    if (error || !inviteInfo?.is_valid) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111827', color: 'white' }}>
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', maxWidth: '400px', borderRadius: '12px', border: '1px solid var(--glass-border)', background: 'var(--bg-secondary)' }}>
                    <FiAlertTriangle size={48} color="#ef4444" style={{ margin: '0 auto 16px' }} />
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>{txt.errorTitle}</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                        {txt.errorDesc}
                    </p>
                    <button onClick={() => navigate('/')} style={{ padding: '10px 24px', borderRadius: '8px', background: 'var(--glass-border)', border: 'none', color: 'white', cursor: 'pointer' }}>
                        {txt.goHome}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111827', color: 'white' }}>
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', maxWidth: '400px', width: '90%', borderRadius: '12px', border: '1px solid var(--glass-border)', background: 'var(--bg-secondary)' }}>

                <div style={{ width: '64px', height: '64px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
                    <FiUsers size={32} color="#3b82f6" />
                </div>

                <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>{txt.joinTitle}</h2>
                <h3 style={{ fontSize: '1.4rem', color: 'var(--accent-primary)', marginBottom: '16px' }}>{inviteInfo.team_name}</h3>

                <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', lineHeight: 1.6 }}>
                    {txt.invitedText} <br />
                    {txt.invitedBy} <b>{inviteInfo.inviter_name || 'Admin'}</b>
                </p>

                <button
                    onClick={handleJoin}
                    disabled={processing}
                    style={{
                        width: '100%',
                        padding: '14px',
                        borderRadius: '8px',
                        background: 'var(--accent-primary)',
                        border: 'none',
                        color: 'white',
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        cursor: processing ? 'not-allowed' : 'pointer',
                        opacity: processing ? 0.7 : 1
                    }}
                >
                    {processing ? txt.joining : (token ? txt.accept : txt.loginAccept)}
                </button>
            </div>
        </div>
    );
};

export default InvitePage;
