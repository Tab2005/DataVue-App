import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TeamService } from '../services/teamService';
import { FiUsers, FiCheckCircle, FiAlertTriangle } from 'react-icons/fi';

const InvitePage = () => {
    const { code } = useParams();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [inviteInfo, setInviteInfo] = useState(null);
    const [error, setError] = useState(null);
    const [processing, setProcessing] = useState(false);

    // Check if user is logged in (Simple check)
    const token = localStorage.getItem('google_token');

    useEffect(() => {
        // Robust Code Extraction
        let inviteCode = code;
        if (!inviteCode) {
            // Fallback: extract from pathname
            const parts = window.location.pathname.split('/');
            inviteCode = parts[parts.length - 1];
        }

        // Debug: Log what we see
        console.log("Raw Code:", code, "Extracted:", inviteCode);

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
            // Encode current path to return after login
            const returnUrl = encodeURIComponent(window.location.pathname);
            window.location.href = `/login?return_to=${returnUrl}`;
            return;
        }

        setProcessing(true);
        try {
            const res = await TeamService.acceptInvite(code);
            // Switch to that team automatically?
            if (res.team_id) {
                localStorage.setItem('selected_team_id', res.team_id);
            }
            alert("Successfully joined team!");
            navigate('/');
            // Force reload to update context
            window.location.reload();
        } catch (err) {
            alert(err.message);
            setProcessing(false);
        }
    };

    if (loading) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111827', color: 'white' }}>
                Loading Invite...
            </div>
        );
    }

    if (error || !inviteInfo?.is_valid) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#111827', color: 'white' }}>
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', maxWidth: '400px', borderRadius: '12px', border: '1px solid var(--glass-border)', background: 'var(--bg-secondary)' }}>
                    <FiAlertTriangle size={48} color="#ef4444" style={{ margin: '0 auto 16px' }} />
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>Invite Expired or Invalid</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                        This invitation link is no longer valid. Please ask the administrator for a new one.
                    </p>
                    <button onClick={() => navigate('/')} style={{ padding: '10px 24px', borderRadius: '8px', background: 'var(--glass-border)', border: 'none', color: 'white', cursor: 'pointer' }}>
                        Go Home
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

                <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Join Team</h2>
                <h3 style={{ fontSize: '1.4rem', color: 'var(--accent-primary)', marginBottom: '16px' }}>{inviteInfo.team_name}</h3>

                <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', lineHeight: 1.6 }}>
                    You have been invited to join this workspace. <br />
                    Invited by: <b>{inviteInfo.inviter_name || 'Admin'}</b>
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
                    {processing ? 'Joining...' : (token ? 'Accept Invite' : 'Login to Accept')}
                </button>
            </div>
        </div>
    );
};

export default InvitePage;
