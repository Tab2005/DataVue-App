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
        provider: 'zeabur', // Default to Zeabur AI Hub
        apiKey: '',
        model: 'gemini-2.5-flash'
    });

    // Available models from backend
    const [availableModels, setAvailableModels] = useState({});

    // Status & Loading (separate for FB and AI tabs)
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [fbLoading, setFbLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

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
            manualDesc: language === 'zh' ? '請輸入您的 Zeabur AI Hub API Key (我們會安全地儲存在您的瀏覽器中)。' : 'Please enter your Zeabur AI Hub API Key (securely stored in your browser).',
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
        console.log("[SettingsModal] Fetching token status...");
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
                console.log("[SettingsModal] Token status data:", data);
                setTokenInfo(data);
            } else {
                console.error("[SettingsModal] Failed to fetch token status:", res.status);
                if (res.status === 401) {
                    // Token expired or invalid
                    setTokenInfo({ expires_at: null, token_exists: false });
                }
            }
        } catch (err) {
            console.error("[SettingsModal] Network error fetching token status", err);
        }
    };

    const handleFbSubmit = async (e) => {
        e.preventDefault();
        setFbLoading(true);
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
                // Support multiple error formats:
                // 1. FastAPI standard: { detail: "msg" }
                // 2. Custom Exception Handler: { error: "msg", error_code: ... }
                const errorDetail = data.error || data.detail || JSON.stringify(data);

                // Optional: Client-side translation/friendly mapping
                let friendlierMessage = errorDetail;
                if (typeof errorDetail === 'string' && errorDetail.includes("Permission Denied")) {
                    friendlierMessage = language === 'zh'
                        ? "權限不足：只有團隊管理員 (Admin) 才能修改設定。"
                        : "Permission Denied: Only Team Admins can update settings.";
                }

                setStatus({ type: 'error', message: `${t.common.error} ${friendlierMessage}` });
            }
        } catch (err) {
            setStatus({ type: 'error', message: `${t.common.error} ${err.message}` });
        } finally {
            setFbLoading(false);
        }
    };

    // --- AI Logic ---
    const fetchAvailableModels = async (provider = 'zeabur') => {
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/models?provider=${provider}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAvailableModels(data.models || {});
            }
        } catch (err) {
            console.error("Failed to fetch AI models", err);
        }
    };

    const checkAiConnection = async () => {
        setAiLoading(true);
        // 1. Check LocalStorage for user key and settings
        const localKey = localStorage.getItem('ai_api_key');
        const savedProvider = localStorage.getItem('ai_provider') || 'zeabur';
        const savedModel = localStorage.getItem('ai_model') || 'gemini-2.5-flash';

        if (localKey) {
            setAiData(prev => ({ ...prev, apiKey: localKey, provider: savedProvider, model: savedModel }));
        } else {
            setAiData(prev => ({ ...prev, provider: savedProvider, model: savedModel }));
        }

        // Fetch available models for the provider
        await fetchAvailableModels(savedProvider);

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
                body: JSON.stringify({
                    api_key: null,
                    provider: savedProvider,
                    model: savedModel
                })
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
                        body: JSON.stringify({
                            api_key: localKey,
                            provider: savedProvider,
                            model: savedModel
                        })
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
            setAiLoading(false);
        }
    };

    const handleSaveAiKey = () => {
        // Save provider and model preferences immediately
        localStorage.setItem('ai_provider', aiData.provider);
        localStorage.setItem('ai_model', aiData.model);

        if (aiData.apiKey) {
            localStorage.setItem('ai_api_key', aiData.apiKey);
        }

        // Show success message immediately
        setStatus({ type: 'success', message: language === 'zh' ? '設定已儲存！' : 'Settings Saved!' });
    };

    const handleTestConnection = async () => {
        setAiLoading(true);
        setStatus(null);

        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const res = await fetch(`${apiUrl}/api/ai/test-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    api_key: aiData.apiKey || null,
                    provider: 'zeabur',
                    model: aiData.model
                })
            });

            if (res.ok) {
                setStatus({ type: 'success', message: language === 'zh' ? '✅ 連線成功！' : '✅ Connection Successful!' });
                setAiConnectionStatus('connected_zeabur');
            } else {
                setStatus({ type: 'error', message: language === 'zh' ? '❌ 連線失敗，請檢查 API Key' : '❌ Connection Failed, check API Key' });
                setAiConnectionStatus('disconnected');
            }
        } catch (err) {
            setStatus({ type: 'error', message: language === 'zh' ? '❌ 連線失敗' : '❌ Connection Failed' });
            setAiConnectionStatus('disconnected');
        } finally {
            setAiLoading(false);
        }
    };

    const handleProviderChange = async (newProvider) => {
        setAiData(prev => ({ ...prev, provider: newProvider }));
        await fetchAvailableModels(newProvider);
        // Reset model to first available
        setAiData(prev => ({ ...prev, model: 'gemini-2.5-flash' }));
    };

    const handleClearAiKey = () => {
        localStorage.removeItem('ai_api_key');
        setAiData(prev => ({ ...prev, apiKey: '' }));
        checkAiConnection();
        setStatus(null);
    }

    useEffect(() => {
        if (isOpen) {
            // Reset status
            setStatus(null);
            // Fetch Facebook token status
            fetchTokenStatus();
            // Don't auto-check AI connection - let user trigger it
        }
    }, [isOpen, teamId]);

    // Switch to AI tab - just load saved settings, don't auto-test
    useEffect(() => {
        if (isOpen && activeTab === 'ai') {
            // Load saved settings from localStorage
            const savedModel = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
            const savedKey = localStorage.getItem('ai_api_key') || '';
            setAiData(prev => ({ ...prev, model: savedModel, apiKey: savedKey }));
            setAiConnectionStatus('unknown');
        }
    }, [activeTab, isOpen]);


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
                            {tokenInfo && (
                                <>
                                    {/* Warning: Token missing but has expiration date */}
                                    {tokenInfo.expires_at && tokenInfo.token_exists === false && (
                                        <div style={{
                                            marginBottom: '20px', padding: '12px', borderRadius: '8px',
                                            backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)',
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
                                                <span>⚠️</span>
                                                <span>{language === 'zh' ? '權杖資料不同步' : 'Token Data Out of Sync'}</span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                                {language === 'zh'
                                                    ? `到期日期 ${new Date(tokenInfo.expires_at).toLocaleDateString()} 存在，但實際權杖遺失。請重新設定連線。`
                                                    : `Expiration date ${new Date(tokenInfo.expires_at).toLocaleDateString()} exists, but actual token is missing. Please reconnect.`
                                                }
                                            </div>
                                        </div>
                                    )}

                                    {/* Normal Status: Token exists and not expired */}
                                    {tokenInfo.expires_at && tokenInfo.token_exists !== false && (
                                        <div style={{
                                            marginBottom: '20px', padding: '12px', borderRadius: '8px',
                                            backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid rgba(74, 222, 128, 0.2)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                                        }}>
                                            <div>
                                                <div style={{ color: '#4ade80', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
                                                    {language === 'zh' ? '✓ 權杖狀態正常' : '✓ Token Active'}
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

                                    {/* Not Connected Status */}
                                    {!tokenInfo.expires_at && (
                                        <div style={{
                                            marginBottom: '20px', padding: '12px', borderRadius: '8px',
                                            backgroundColor: tokenInfo.error ? 'rgba(248, 113, 113, 0.1)' : 'rgba(100, 100, 100, 0.1)',
                                            border: tokenInfo.error ? '1px solid rgba(248, 113, 113, 0.3)' : '1px solid rgba(100, 100, 100, 0.2)',
                                            color: tokenInfo.error ? '#f87171' : 'var(--text-secondary)',
                                            fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px'
                                        }}>
                                            <span>{tokenInfo.error ? '⚠️' : '⚪'}</span>
                                            {tokenInfo.error
                                                ? (language === 'zh' ? '無法連線到後端服務 (Timeout)' : 'Connection Timeout / Server Error')
                                                : (language === 'zh' ? '尚未連線或權杖已過期' : 'Not Connected or Token Expired')
                                            }
                                        </div>
                                    )}
                                </>
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
                                    <button type="submit" disabled={fbLoading}
                                        style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: fbLoading ? 'gray' : 'var(--accent-primary)', color: 'white', cursor: fbLoading ? 'not-allowed' : 'pointer' }}>
                                        {fbLoading ? t.common.processing : t.fb.save}
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
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', opacity: aiLoading ? 0.5 : 1 }}>
                                    {/* Model Selection - Direct model choice without provider */}
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                            {language === 'zh' ? 'AI 模型' : 'AI Model'}
                                        </label>
                                        <select
                                            value={aiData.model}
                                            onChange={(e) => setAiData({ ...aiData, model: e.target.value })}
                                            style={{
                                                width: '100%',
                                                padding: '12px',
                                                borderRadius: '8px',
                                                border: '1px solid var(--glass-border)',
                                                background: '#1a1a1a',
                                                color: 'white'
                                            }}
                                        >
                                            <optgroup label="Gemini (推薦 - 免費額度高)" style={{ background: '#2a2a2a' }}>
                                                <option value="gemini-2.5-flash" style={{ background: '#1a1a1a' }}>gemini-2.5-flash (快速、免費額度高) ✅ 推薦</option>
                                                <option value="gemini-2.5-pro" style={{ background: '#1a1a1a' }}>gemini-2.5-pro (高品質、長文本)</option>
                                                <option value="gemini-3-flash-preview" style={{ background: '#1a1a1a' }}>gemini-3-flash-preview (最新預覽)</option>
                                            </optgroup>
                                            <optgroup label="Claude (Anthropic)" style={{ background: '#2a2a2a' }}>
                                                <option value="claude-sonnet-4-5" style={{ background: '#1a1a1a' }}>claude-sonnet-4-5 (高品質)</option>
                                                <option value="claude-haiku-4-5" style={{ background: '#1a1a1a' }}>claude-haiku-4-5 (快速、經濟)</option>
                                            </optgroup>
                                            <optgroup label="GPT (OpenAI)" style={{ background: '#2a2a2a' }}>
                                                <option value="gpt-4o" style={{ background: '#1a1a1a' }}>gpt-4o (多模態)</option>
                                                <option value="gpt-4o-mini" style={{ background: '#1a1a1a' }}>gpt-4o-mini (經濟實惠)</option>
                                            </optgroup>
                                            <optgroup label="其他模型" style={{ background: '#2a2a2a' }}>
                                                <option value="deepseek-v3.2" style={{ background: '#1a1a1a' }}>deepseek-v3.2 (開源高品質)</option>
                                                <option value="qwen-3-32" style={{ background: '#1a1a1a' }}>qwen-3-32 (通義千問，中文優化)</option>
                                                <option value="llama-3.3-70b" style={{ background: '#1a1a1a' }}>llama-3.3-70b (Meta 開源)</option>
                                            </optgroup>
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
                                            onClick={handleTestConnection}
                                            disabled={aiLoading}
                                            style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: 'var(--accent-primary)', cursor: aiLoading ? 'not-allowed' : 'pointer' }}
                                        >
                                            {aiLoading ? t.common.processing : t.ai.test}
                                        </button>
                                        <button
                                            onClick={handleSaveAiKey}
                                            style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: 'var(--accent-primary)', color: 'white', cursor: 'pointer' }}
                                        >
                                            {language === 'zh' ? '儲存設定' : 'Save'}
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
