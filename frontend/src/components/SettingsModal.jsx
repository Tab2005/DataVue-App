import React, { useState } from 'react';

const SettingsModal = ({ isOpen, onClose, language, teamId, teamName, onSuccess }) => {
    const [formData, setFormData] = useState({
        appId: '',
        appSecret: '',
        shortToken: ''
    });
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [loading, setLoading] = useState(false);
    const [tokenInfo, setTokenInfo] = useState(null); // { expires_at, days_remaining, is_expired }

    const fetchTokenStatus = async () => {
        // Only fetch for Personal Settings (No Team ID)
        if (teamId) return;

        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/auth/token-status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setTokenInfo(data);
            }
        } catch (err) {
            console.error("Failed to fetch token status", err);
        }
    };

    React.useEffect(() => {
        if (isOpen) {
            fetchTokenStatus();
            setStatus(null); // Reset detailed status on open
        }
    }, [isOpen, teamId]);

    if (!isOpen) return null;

    const t = {
        title: teamId ? (language === 'zh' ? `設定 API: ${teamName}` : `Setup API: ${teamName}`) : (language === 'zh' ? '設定 API 連線' : 'API Connection Settings'),
        appId: 'App ID',
        appSecret: 'App Secret',
        shortToken: language === 'zh' ? '短期權杖 (Short-Lived Token)' : 'Short-Lived Token',
        save: language === 'zh' ? '連線並交換權杖' : 'Connect & Exchange Token',
        cancel: language === 'zh' ? '取消' : 'Cancel',
        processing: language === 'zh' ? '處理中...' : 'Processing...',
        success: language === 'zh' ? '連線成功！權杖已安全儲存。' : 'Connected successfully! Token saved securely.',
        error: language === 'zh' ? '連線失敗：' : 'Connection failed: '
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);

        try {
            // 取得 API 網址
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('google_token');

            const payload = {
                app_id: formData.appId,
                app_secret: formData.appSecret,
                short_token: formData.shortToken
            };

            if (teamId) {
                payload.team_id = teamId;
            }

            const response = await fetch(`${apiUrl}/api/auth/exchange-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload),
            });

            // Handle Token Expiry (401)
            if (response.status === 401) {
                localStorage.removeItem('google_token');
                window.location.href = '/login';
                return;
            }

            const data = await response.json();

            if (response.ok) {
                setStatus({ type: 'success', message: t.success });
                setFormData({ appId: '', appSecret: '', shortToken: '' });
                fetchTokenStatus();
                if (onSuccess) onSuccess();
            } else {
                const errorDetail = data.detail || JSON.stringify(data);
                setStatus({ type: 'error', message: `${t.error} ${errorDetail}` });
            }
        } catch (err) {
            console.error("Settings connection error:", err);
            setStatus({ type: 'error', message: `${t.error} ${err.message}` });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(5px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                cursor: 'default'
            }}
        >
            <div
                className="glass-panel"
                onClick={(e) => e.stopPropagation()}
                style={{
                    width: '500px',
                    padding: '32px',
                    borderRadius: 'var(--radius-xl)',
                    backgroundColor: '#242526',
                    position: 'relative' // For absolute positioning of close button
                }}
            >
                {/* Close Button X */}
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '20px',
                        right: '20px',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        fontSize: '24px',
                        cursor: 'pointer',
                        lineHeight: '1',
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background 0.2s, color 0.2s'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.color = 'white';
                        e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.color = 'var(--text-secondary)';
                        e.currentTarget.style.background = 'transparent';
                    }}
                    aria-label="Close"
                >
                    ×
                </button>

                <h2 style={{ marginBottom: '24px', fontSize: '1.5rem' }}>{t.title}</h2>

                {teamId && (
                    <div style={{
                        marginBottom: '20px',
                        padding: '12px',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        color: '#60a5fa',
                        fontSize: '0.9rem',
                        lineHeight: '1.5'
                    }}>
                        {language === 'zh'
                            ? `⚠️ 您正在為團隊「${teamName}」設定 API。此 Token 將授權給團隊所有成員查看廣告數據。`
                            : `⚠️ You are setting API for team "${teamName}". This token will allow all team members to view ad data.`}
                    </div>
                )}

                {/* Token Status Widget (Personal Only) */}
                {!teamId && tokenInfo?.expires_at && (
                    <div style={{
                        marginBottom: '20px',
                        padding: '12px',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)',
                        border: '1px solid rgba(74, 222, 128, 0.2)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <div>
                            <div style={{ color: '#4ade80', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
                                {language === 'zh' ? '● 目前權杖狀態正常' : '● Active Token Found'}
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                {language === 'zh' ? '到期時間: ' : 'Exp: '}
                                {new Date(tokenInfo.expires_at).toLocaleDateString()}
                            </div>
                        </div>
                        <div style={{
                            background: '#4ade80',
                            color: 'black',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 'bold'
                        }}>
                            {tokenInfo.days_remaining} {language === 'zh' ? '天後到期' : 'Days Left'}
                        </div>
                    </div>
                )}


                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.appId}</label>
                        <input
                            type="text"
                            required
                            value={formData.appId}
                            onChange={(e) => setFormData({ ...formData, appId: e.target.value })}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.appSecret}</label>
                        <input
                            type="password"
                            required
                            value={formData.appSecret}
                            onChange={(e) => setFormData({ ...formData, appSecret: e.target.value })}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.shortToken}</label>
                        <input
                            type="password"
                            required
                            value={formData.shortToken}
                            onChange={(e) => setFormData({ ...formData, shortToken: e.target.value })}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    {status && (
                        <div style={{
                            padding: '12px',
                            borderRadius: '8px',
                            backgroundColor: status.type === 'success' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                            color: status.type === 'success' ? '#4ade80' : '#f87171',
                            border: `1px solid ${status.type === 'success' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(248, 113, 113, 0.2)'}`
                        }}>
                            {status.message}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '12px', marginTop: '16px', justifyContent: 'flex-end' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '8px',
                                border: 'none',
                                background: 'rgba(255,255,255,0.1)',
                                color: 'var(--text-primary)',
                                cursor: 'pointer'
                            }}
                        >
                            {t.cancel}
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '8px',
                                border: 'none',
                                background: loading ? 'gray' : 'var(--accent-primary)',
                                color: 'white',
                                cursor: loading ? 'not-allowed' : 'pointer'
                            }}
                        >
                            {loading ? t.processing : t.save}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SettingsModal;
