import React, { useState, useEffect } from 'react';

const SettingsModal = ({ isOpen, onClose, language, teamId, teamName, onSuccess }) => {
    // Tabs: 'facebook' | 'ai'
    const [activeTab, setActiveTab] = useState('facebook');

    // Facebook Form Data
    const [fbData, setFbData] = useState({
        appId: '',
        appSecret: '',
        shortToken: ''
    });

    // AI Form Data
    const [aiData, setAiData] = useState({
        provider: 'google', // Default
        apiKey: '',
        model: 'gemini-2.5-flash'
    });

    // Status & Loading
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [loading, setLoading] = useState(false);

    // Token Info (Facebook)
    const [tokenInfo, setTokenInfo] = useState(null);

    // Zeabur / AI Status
    const [aiConnectionStatus, setAiConnectionStatus] = useState('unknown'); // unknown, connected_zeabur, connected_user, disconnected

    const t = {
        title: language === 'zh' ? '整合中心 (Integration Center)' : 'Integration Center',
        tabs: {
            facebook: 'Facebook Ads',
            ai: 'AI Intelligence'
        },
        fb: {
            appId: 'App ID',
            appSecret: 'App Secret',
            shortToken: language === 'zh' ? '短期權杖 (Short-Lived Token)' : 'Short-Lived Token',
            save: language === 'zh' ? '連線並交換權杖' : 'Connect & Exchange Token',
        },
        ai: {
            provider: 'Provider',
            apiKey: 'API Key',
            model: 'Model',
            test: language === 'zh' ? '測試連線' : 'Test Connection',
            zeaburDetected: language === 'zh' ? '🟢 系統託管模式 (Zeabur AI Hub)' : '🟢 Managed Mode (Zeabur AI Hub)',
            zeaburDesc: language === 'zh' ? '系統已自動偵測到託管的金鑰，您無需設定即可使用 AI 功能。' : 'System has detected a managed key. You can use AI features without configuration.',
            manualDesc: language === 'zh' ? '請輸入您的 Google Gemini API Key (我們會安全地儲存在您的瀏覽器中)。' : 'Please enter your Google Gemini API Key (securely stored in your browser).',
            saveKey: language === 'zh' ? '儲存金鑰' : 'Save Key (Local)',
        },
        common: {
            cancel: language === 'zh' ? '關閉' : 'Close',
            processing: language === 'zh' ? '處理中...' : 'Processing...',
            success: language === 'zh' ? '設定已儲存！' : 'Settings Saved!',
            error: language === 'zh' ? '錯誤：' : 'Error: '
        }
    };

    // --- Facebook Logic ---
    const fetchTokenStatus = async () => {
        // if (teamId) return; // Allow for team
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            let url = `${apiUrl}/api/auth/token-status`;
            if (teamId) url += `?team_id=${teamId}`;

            const res = await fetch(url, {
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

    const handleFbSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('google_token');

            const payload = {
                app_id: fbData.appId,
                app_secret: fbData.appSecret,
                short_token: fbData.shortToken
            };
            if (teamId) payload.team_id = teamId;

            const response = await fetch(`${apiUrl}/api/auth/exchange-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload),
            });

            if (response.status === 401) {
                localStorage.removeItem('google_token');
                window.location.href = '/login';
                return;
            }

            const data = await response.json();

            if (response.ok) {
                setStatus({ type: 'success', message: t.common.success });
                setFbData({ appId: '', appSecret: '', shortToken: '' });
                fetchTokenStatus();
                if (onSuccess) onSuccess();
            } else {
                const errorDetail = data.detail || JSON.stringify(data);
                setStatus({ type: 'error', message: `${t.common.error} ${errorDetail}` });
            }
        } catch (err) {
            setStatus({ type: 'error', message: `${t.common.error} ${err.message}` });
        } finally {
            setLoading(false);
        }
    };

    // --- AI Logic ---
    const checkAiConnection = async () => {
        setLoading(true);
        // 1. Check LocalStorage for user key
        const localKey = localStorage.getItem('ai_api_key');
        if (localKey) {
            setAiData(prev => ({ ...prev, apiKey: localKey }));
        }

        // 2. Test Connection (Backend will check Zeabur env if key is null)
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            // First, test with NO key to see if Zeabur is active
            const res = await fetch(`${apiUrl}/api/ai/test-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ api_key: null })
            });

            if (res.ok) {
                setAiConnectionStatus('connected_zeabur');
            } else {
                // If Zeabur failed, try with Local Key if exists
                if (localKey) {
                    const res2 = await fetch(`${apiUrl}/api/ai/test-connection`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ api_key: localKey })
                    });
                    if (res2.ok) {
                        setAiConnectionStatus('connected_user');
                    } else {
                        setAiConnectionStatus('disconnected');
                    }
                } else {
                    setAiConnectionStatus('disconnected');
                }
            }

        } catch (err) {
            console.error("AI Check Failed", err);
            setAiConnectionStatus('disconnected');
        } finally {
            setLoading(false);
        }
    };

    const handleSaveAiKey = () => {
        if (aiData.apiKey) {
            localStorage.setItem('ai_api_key', aiData.apiKey);
            // Re-test
            checkAiConnection();
            setStatus({ type: 'success', message: 'API Key Saved Locally!' });
        }
    };

    const handleClearAiKey = () => {
        localStorage.removeItem('ai_api_key');
        setAiData(prev => ({ ...prev, apiKey: '' }));
        checkAiConnection();
        setStatus(null);
    }

    useEffect(() => {
        if (isOpen) {
            // Reset
            setStatus(null);
            fetchTokenStatus();

            // Determine default tab? No, keep existing behavior or default to facebook
            if (activeTab === 'ai') {
                checkAiConnection();
            }
        }
    }, [isOpen, teamId]);

    // Switch to AI tab triggers check
    useEffect(() => {
        if (isOpen && activeTab === 'ai') {
            checkAiConnection();
        }
    }, [activeTab]);


    if (!isOpen) return null;

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed', inset: 0,
                backgroundColor: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(5px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                zIndex: 1000, cursor: 'default'
            }}
        >
            <div
                className="glass-panel"
                onClick={(e) => e.stopPropagation()}
                style={{
                    width: '600px', // Wider for tabs
                    padding: '32px',
                    borderRadius: 'var(--radius-xl)',
                    backgroundColor: '#242526',
                    position: 'relative',
                    maxHeight: '85vh',
                    overflowY: 'auto'
                }}
            >
                {/* Header & Tabs */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.5rem', margin: 0 }}>{t.title}</h2>
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', fontSize: '24px', cursor: 'pointer' }}>×</button>
                </div>

                {/* Tabs Config */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--glass-border)' }}>
                    {Object.keys(t.tabs).map(key => (
                        <button
                            key={key}
                            onClick={() => { setActiveTab(key); setStatus(null); }}
                            style={{
                                padding: '12px 24px',
                                background: 'transparent',
                                border: 'none',
                                borderBottom: activeTab === key ? '2px solid var(--accent-primary)' : '2px solid transparent',
                                color: activeTab === key ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                fontWeight: activeTab === key ? 'bold' : 'normal',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                fontSize: '1rem'
                            }}
                        >
                            {t.tabs[key]}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div style={{ minHeight: '300px' }}>

                    {/* --- FACEBOOK TAB --- */}
                    {activeTab === 'facebook' && (
                        <>
                            {teamId && (
                                <div style={{
                                    marginBottom: '20px', padding: '12px', borderRadius: '8px',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#60a5fa', fontSize: '0.9rem'
                                }}>
                                    {language === 'zh'
                                        ? `⚠️ 您正在為團隊「${teamName}」設定 API。此 Token 將授權給團隊所有成員查看廣告數據。`
                                        : `⚠️ You are setting API for team "${teamName}". This token will allow all team members to view ad data.`}
                                </div>
                            )}

                            {/* Token Status Widget */}
                            {tokenInfo?.expires_at && (
                                <div style={{
                                    marginBottom: '20px', padding: '12px', borderRadius: '8px',
                                    backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid rgba(74, 222, 128, 0.2)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between'
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
                                        background: '#4ade80', color: 'black', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold'
                                    }}>
                                        {tokenInfo.days_remaining} {language === 'zh' ? '天後到期' : 'Days Left'}
                                    </div>
                                </div>
                            )}

                            <form onSubmit={handleFbSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.appId}</label>
                                    <input type="text" required value={fbData.appId} onChange={(e) => setFbData({ ...fbData, appId: e.target.value })}
                                        style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.appSecret}</label>
                                    <input type="password" required value={fbData.appSecret} onChange={(e) => setFbData({ ...fbData, appSecret: e.target.value })}
                                        style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.shortToken}</label>
                                    <input type="password" required value={fbData.shortToken} onChange={(e) => setFbData({ ...fbData, shortToken: e.target.value })}
                                        style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }} />
                                </div>

                                <div style={{ display: 'flex', gap: '12px', marginTop: '16px', justifyContent: 'flex-end' }}>
                                    <button type="submit" disabled={loading}
                                        style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: loading ? 'gray' : 'var(--accent-primary)', color: 'white', cursor: loading ? 'not-allowed' : 'pointer' }}>
                                        {loading ? t.common.processing : t.fb.save}
                                    </button>
                                </div>
                            </form>
                        </>
                    )}

                    {/* --- AI TAB --- */}
                    {activeTab === 'ai' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                            {/* Status Indicator */}
                            <div style={{
                                padding: '16px', borderRadius: '8px',
                                border: aiConnectionStatus.startsWith('connected') ? '1px solid rgba(74, 222, 128, 0.2)' : '1px solid rgba(248, 113, 113, 0.2)',
                                background: aiConnectionStatus.startsWith('connected') ? 'rgba(74, 222, 128, 0.05)' : 'rgba(248, 113, 113, 0.05)',
                                display: 'flex', alignItems: 'center', gap: '12px'
                            }}>
                                <div style={{ fontSize: '24px' }}>
                                    {aiConnectionStatus.startsWith('connected') ? '🤖' : '🔌'}
                                </div>
                                <div>
                                    <div style={{ fontWeight: 'bold', color: aiConnectionStatus.startsWith('connected') ? '#4ade80' : '#f87171' }}>
                                        {aiConnectionStatus === 'connected_zeabur' && t.ai.zeaburDetected}
                                        {aiConnectionStatus === 'connected_user' && (language === 'zh' ? '🟢 已連線 (用戶自訂 Key)' : '🟢 Connected (User Key)')}
                                        {aiConnectionStatus === 'disconnected' && (language === 'zh' ? '🔴 未連線' : '🔴 Disconnected')}
                                        {aiConnectionStatus === 'unknown' && t.common.processing}
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                                        {aiConnectionStatus === 'connected_zeabur' && t.ai.zeaburDesc}
                                        {aiConnectionStatus !== 'connected_zeabur' && t.ai.manualDesc}
                                    </div>
                                </div>
                            </div>

                            {/* Manual Configuration (Only if not Zeabur Managed) */}
                            {aiConnectionStatus !== 'connected_zeabur' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', opacity: loading ? 0.5 : 1 }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.ai.provider}</label>
                                        <select
                                            value={aiData.provider}
                                            onChange={(e) => setAiData({ ...aiData, provider: e.target.value })}
                                            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
                                        >
                                            <option value="google">Google Gemini</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.ai.apiKey}</label>
                                        <input
                                            type="password"
                                            placeholder="sk-..."
                                            value={aiData.apiKey}
                                            onChange={(e) => setAiData({ ...aiData, apiKey: e.target.value })}
                                            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
                                        />
                                    </div>

                                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                                        {aiData.apiKey && (
                                            <button
                                                onClick={handleClearAiKey}
                                                style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: '#f87171', cursor: 'pointer' }}
                                            >
                                                {language === 'zh' ? '清除' : 'Clear'}
                                            </button>
                                        )}
                                        <button
                                            onClick={handleSaveAiKey}
                                            disabled={loading || !aiData.apiKey}
                                            style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: 'var(--accent-primary)', color: 'white', cursor: loading ? 'not-allowed' : 'pointer' }}
                                        >
                                            {loading ? t.common.processing : t.ai.test}
                                        </button>
                                    </div>
                                </div>
                            )}

                        </div>
                    )}
                </div>

                {/* Status Message Overlay */}
                {status && (
                    <div style={{
                        marginTop: '16px', padding: '12px', borderRadius: '8px',
                        backgroundColor: status.type === 'success' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                        color: status.type === 'success' ? '#4ade80' : '#f87171',
                        border: `1px solid ${status.type === 'success' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(248, 113, 113, 0.2)'}`
                    }}>
                        {status.message}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SettingsModal;
