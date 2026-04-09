import React, { useState, useEffect } from 'react';
import { FiTrendingUp, FiMessageSquare, FiCpu, FiZap, FiRefreshCw } from 'react-icons/fi';
import LineBindingCard from './Settings/LineBindingCard';

const SettingsModal = ({ isOpen, onClose, language, teamId, teamName, onSuccess }) => {
    // Tabs: 'facebook' | 'ai'
    const [activeTab, setActiveTab] = useState('facebook');

    // Facebook Form Data
    const [fbData, setFbData] = useState({
        appId: '',
        appSecret: '',
        shortToken: ''
    });

    // AI Form Data (Zeabur AI Hub)
    const [aiData, setAiData] = useState({
        provider: 'zeabur', // Default to Zeabur AI Hub
        apiKey: '',
        model: 'gemini-2.5-flash'
    });

    // Google Gemini Direct API Data
    const [geminiData, setGeminiData] = useState({
        apiKey: '',
        model: 'gemini-2.5-flash'
    });

    // Available models from backend (Separate lists)
    const [zeaburModels, setZeaburModels] = useState({});
    const [googleModels, setGoogleModels] = useState({});

    // Status & Loading (separate for FB and AI tabs)
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [fbLoading, setFbLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

    // Token Info (Facebook)
    const [tokenInfo, setTokenInfo] = useState(null);

    // Zeabur / AI Status
    const [aiConnectionStatus, setAiConnectionStatus] = useState('unknown'); // unknown, connected_zeabur, connected_user, disconnected

    // Active AI Provider preference: 'zeabur' | 'gemini'
    const [activeAiProvider, setActiveAiProvider] = useState('zeabur');

    const t = {
        title: language === 'zh' ? '整合中心 (Integration Center)' : 'Integration Center',
        tabs: {
            facebook: 'Facebook Ads',
            ai: 'Zeabur AI Hub',
            gemini: 'Google Gemini',
            line: language === 'zh' ? 'LINE 通知' : 'LINE Notify'
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

    // Fetch AI settings from backend (encrypted storage)
    const fetchAiSettings = async () => {
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/settings`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                console.log('[SettingsModal] AI settings from DB:', data);
                return data; // { ai_provider, ai_model, has_zeabur_key, has_gemini_key }
            }
        } catch (err) {
            console.error('Failed to fetch AI settings', err);
        }
        return null;
    };

    // Save AI settings to backend (encrypted storage)
    const saveAiSettingsToServer = async (settings) => {
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/settings`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            if (res.ok) {
                const data = await res.json();
                console.log('[SettingsModal] AI settings saved:', data);
                return data;
            } else {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to save settings');
            }
        } catch (err) {
            console.error('Failed to save AI settings', err);
            throw err;
        }
    };

    const [isSyncingModels, setIsSyncingModels] = useState(false);

    const fetchAvailableModels = async (provider = 'zeabur', sync = false) => {
        if (sync) setIsSyncingModels(true);
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/models?provider=${provider}${sync ? '&sync=true' : ''}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (provider === 'zeabur') {
                    setZeaburModels(data.models || {});
                } else if (provider === 'google_gemini') {
                    setGoogleModels(data.models || {});
                }
                
                if (sync) {
                    setStatus({ type: 'success', message: language === 'zh' ? '✅ 模型清單已同步完成' : '✅ Model list synced' });
                }
            }
        } catch (err) {
            console.error("Failed to fetch AI models", err);
            if (sync) setStatus({ type: 'error', message: language === 'zh' ? '❌ 同步失敗' : '❌ Sync failed' });
        } finally {
            if (sync) setIsSyncingModels(false);
        }
    };

    const checkAiConnection = async () => {
        setAiLoading(true);
        // 1. Check LocalStorage for user key and settings
        const localKey = localStorage.getItem('ai_api_key');
        const savedProvider = localStorage.getItem('ai_provider') || 'zeabur';
        const savedModel = localStorage.getItem('ai_model') || 'gemini-1.5-flash';

        if (localKey) {
            setAiData(prev => ({ ...prev, apiKey: localKey, provider: savedProvider, model: savedModel }));
        } else {
            setAiData(prev => ({ ...prev, provider: savedProvider, model: savedModel }));
        }

        // Fetch BOTH model lists initially
        await Promise.all([
            fetchAvailableModels('zeabur'),
            fetchAvailableModels('google_gemini')
        ]);

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

    const handleSaveAiKey = async () => {
        setAiLoading(true);
        try {
            // Save to backend (encrypted)
            await saveAiSettingsToServer({
                zeabur_api_key: aiData.apiKey || null,
                ai_provider: 'zeabur',
                ai_model: aiData.model
            });

            // Sync provider to localStorage for GSCStats
            localStorage.setItem('ai_provider', 'zeabur');

            setStatus({ type: 'success', message: language === 'zh' ? '✅ 設定已儲存至伺服器！' : '✅ Settings saved to server!' });
        } catch (err) {
            setStatus({ type: 'error', message: language === 'zh' ? `❌ 儲存失敗: ${err.message}` : `❌ Save failed: ${err.message}` });
        } finally {
            setAiLoading(false);
        }
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

            // Fetch AI settings from backend
            fetchAiSettings().then(settings => {
                if (settings) {
                    setActiveAiProvider(settings.ai_provider || 'zeabur');
                    setAiData(prev => ({ ...prev, model: settings.ai_model || 'gemini-2.5-flash' }));
                    // Store provider in localStorage for GSCStats to use (sync purpose only)
                    localStorage.setItem('ai_provider', settings.ai_provider || 'zeabur');
                }
            });
        }
    }, [isOpen, teamId]);

    // Switch to AI tab - load settings from backend
    useEffect(() => {
        if (isOpen && activeTab === 'ai') {
            setAiConnectionStatus('unknown');
            // Settings already loaded on modal open
        }
    }, [activeTab, isOpen]);

    // Switch to Gemini tab - settings already loaded from backend
    useEffect(() => {
        if (isOpen && activeTab === 'gemini') {
            // Settings already loaded from backend on modal open
            // geminiData.apiKey will be empty since we don't expose keys to frontend
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

                {/* Active AI Provider Selector - only show when on AI-related tabs */}
                {(activeTab === 'ai' || activeTab === 'gemini') && (
                    <div style={{
                        marginBottom: '16px',
                        padding: '12px 16px',
                        borderRadius: '8px',
                        background: 'rgba(102, 126, 234, 0.1)',
                        border: '1px solid rgba(102, 126, 234, 0.2)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                                {language === 'zh' ? '目前啟用的 AI 模組：' : 'Active AI Module:'}
                            </span>
                            <span style={{
                                fontWeight: 'bold',
                                color: activeAiProvider === 'gemini' ? '#60a5fa' : '#4ade80',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                            }}>
                                {activeAiProvider === 'gemini' ? '💎 Google Gemini' : '🚀 Zeabur AI Hub'}
                            </span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                                onClick={async () => {
                                    setActiveAiProvider('zeabur');
                                    localStorage.setItem('ai_provider', 'zeabur');
                                    // Also save to backend
                                    try {
                                        await saveAiSettingsToServer({ ai_provider: 'zeabur' });
                                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 Zeabur AI Hub' : 'Switched to Zeabur AI Hub' });
                                    } catch (err) {
                                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 Zeabur AI Hub (本地)' : 'Switched to Zeabur AI Hub (local)' });
                                    }
                                }}
                                style={{
                                    padding: '6px 12px',
                                    borderRadius: '6px',
                                    border: activeAiProvider === 'zeabur' ? '2px solid #4ade80' : '1px solid var(--glass-border)',
                                    background: activeAiProvider === 'zeabur' ? 'rgba(74, 222, 128, 0.1)' : 'transparent',
                                    color: activeAiProvider === 'zeabur' ? '#4ade80' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                    fontWeight: activeAiProvider === 'zeabur' ? 'bold' : 'normal'
                                }}
                            >
                                🚀 Zeabur
                            </button>
                            <button
                                onClick={async () => {
                                    // Check from backend settings (loaded on modal open)
                                    const settings = await fetchAiSettings();
                                    if (!settings?.has_gemini_key) {
                                        setStatus({ type: 'error', message: language === 'zh' ? '請先在 Google Gemini 分頁設定 API Key' : 'Please configure API Key in Google Gemini tab first' });
                                        return;
                                    }
                                    setActiveAiProvider('gemini');
                                    localStorage.setItem('ai_provider', 'gemini');
                                    // Also save to backend
                                    try {
                                        await saveAiSettingsToServer({ ai_provider: 'gemini' });
                                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 Google Gemini' : 'Switched to Google Gemini' });
                                    } catch (err) {
                                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 Google Gemini (本地)' : 'Switched to Google Gemini (local)' });
                                    }
                                }}
                                style={{
                                    padding: '6px 12px',
                                    borderRadius: '6px',
                                    border: activeAiProvider === 'gemini' ? '2px solid #60a5fa' : '1px solid var(--glass-border)',
                                    background: activeAiProvider === 'gemini' ? 'rgba(96, 165, 250, 0.1)' : 'transparent',
                                    color: activeAiProvider === 'gemini' ? '#60a5fa' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                    fontWeight: activeAiProvider === 'gemini' ? 'bold' : 'normal'
                                }}
                            >
                                💎 Gemini
                            </button>
                        </div>
                    </div>
                )}

                {/* Tabs Config - Optimized Layout to prevent wrapping */}
                <div style={{ 
                    display: 'flex', 
                    marginBottom: '24px', 
                    borderBottom: '1px solid var(--glass-border)',
                    overflowX: 'auto',
                    scrollbarWidth: 'none',
                    msOverflowStyle: 'none',
                    position: 'relative'
                }}>
                    <style>{`
                        .settings-tab-container::-webkit-scrollbar { display: none; }
                        .settings-tab-btn {
                            padding: 12px 14px;
                            background: transparent;
                            border: none;
                            border-bottom: 2px solid transparent;
                            color: var(--text-secondary);
                            cursor: pointer;
                            transition: all 0.2s;
                            font-size: 0.88rem;
                            white-space: nowrap;
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            flex-shrink: 0;
                        }
                        .settings-tab-btn.active {
                            border-bottom: 2px solid var(--accent-primary);
                            color: var(--accent-primary);
                            font-weight: 600;
                            background: rgba(45, 136, 255, 0.05);
                        }
                        .settings-tab-btn:hover:not(.active) {
                            color: var(--text-primary);
                            background: rgba(255, 255, 255, 0.02);
                        }
                    `}</style>
                    
                    <div className="settings-tab-container" style={{ display: 'flex', width: '100%', overflowX: 'auto' }}>
                        {Object.keys(t.tabs).map(key => (
                            <button
                                key={key}
                                className={`settings-tab-btn ${activeTab === key ? 'active' : ''}`}
                                onClick={() => { setActiveTab(key); setStatus(null); }}
                            >
                                {key === 'facebook' && <FiTrendingUp size={14} />}
                                {key === 'ai' && <FiZap size={14} />}
                                {key === 'gemini' && <FiCpu size={14} />}
                                {key === 'line' && <FiMessageSquare size={14} />}
                                {t.tabs[key]}
                            </button>
                        ))}
                    </div>
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
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                            <label style={{ color: 'var(--text-secondary)' }}>
                                                {language === 'zh' ? 'AI 模型' : 'AI Model'}
                                            </label>
                                            <button 
                                                onClick={() => fetchAvailableModels('zeabur', true)}
                                                disabled={isSyncingModels}
                                                style={{ 
                                                    background: 'transparent', border: 'none', color: 'var(--accent-primary)', 
                                                    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' 
                                                }}
                                            >
                                                <FiRefreshCw className={isSyncingModels ? 'spin' : ''} size={12} />
                                                {language === 'zh' ? '同步清單' : 'Sync List'}
                                            </button>
                                        </div>
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
                                            {Object.entries(zeaburModels).length > 0 ? (
                                                <>
                                                    {/* Grouped by provider */}
                                                    {Array.from(new Set(Object.values(zeaburModels).map(m => m.provider))).map(provider => (
                                                        <optgroup key={provider} label={provider.toUpperCase()} style={{ background: '#2a2a2a' }}>
                                                            {Object.entries(zeaburModels)
                                                                .filter(([_, config]) => config.provider === provider)
                                                                .map(([id, config]) => (
                                                                    <option key={id} value={id} style={{ background: '#1a1a1a' }}>
                                                                        {config.description || id}
                                                                    </option>
                                                                ))
                                                            }
                                                        </optgroup>
                                                    ))}
                                                </>
                                            ) : (
                                                <option value="gemini-1.5-flash">Gemini 1.5 Flash (Loading...)</option>
                                            )}
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

                    {/* --- GOOGLE GEMINI TAB --- */}
                    {activeTab === 'gemini' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                            {/* Info Banner */}
                            <div style={{
                                padding: '16px', borderRadius: '8px',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                background: 'rgba(59, 130, 246, 0.05)',
                                display: 'flex', alignItems: 'flex-start', gap: '12px'
                            }}>
                                <div style={{ fontSize: '24px' }}>💎</div>
                                <div>
                                    <div style={{ fontWeight: 'bold', color: '#60a5fa' }}>
                                        {language === 'zh' ? 'Google Gemini 直連模式' : 'Google Gemini Direct Mode'}
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                                        {language === 'zh'
                                            ? '直接使用 Google AI Studio 的 API Key，繞過 Zeabur AI Hub。'
                                            : 'Directly use Google AI Studio API Key, bypass Zeabur AI Hub.'}
                                    </div>
                                    <a
                                        href="https://aistudio.google.com/app/apikey"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ fontSize: '0.85rem', color: '#60a5fa', textDecoration: 'underline', marginTop: '8px', display: 'inline-block' }}
                                    >
                                        {language === 'zh' ? '👉 前往 Google AI Studio 取得 API Key' : '👉 Get API Key from Google AI Studio'}
                                    </a>
                                </div>
                            </div>

                            {/* Model Selection */}
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                    <label style={{ color: 'var(--text-secondary)' }}>
                                        {language === 'zh' ? 'Gemini 模型' : 'Gemini Model'}
                                    </label>
                                    <button 
                                        onClick={() => fetchAvailableModels('google_gemini', true)}
                                        disabled={isSyncingModels}
                                        style={{ 
                                            background: 'transparent', border: 'none', color: 'var(--accent-primary)', 
                                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' 
                                        }}
                                    >
                                        <FiRefreshCw className={isSyncingModels ? 'spin' : ''} size={12} />
                                        {language === 'zh' ? '同步清單' : 'Sync List'}
                                    </button>
                                </div>
                                <select
                                    value={geminiData.model}
                                    onChange={(e) => setGeminiData({ ...geminiData, model: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        borderRadius: '8px',
                                        border: '1px solid var(--glass-border)',
                                        background: '#1a1a1a',
                                        color: 'white'
                                    }}
                                >
                                    {Object.entries(googleModels).length > 0 ? (
                                        Object.entries(googleModels).map(([id, config]) => (
                                            <option key={id} value={id}>
                                                {config.display_name || id}
                                            </option>
                                        ))
                                    ) : (
                                        <>
                                            <option value="models/gemini-1.5-flash">Gemini 1.5 Flash (穩定版)</option>
                                            <option value="models/gemini-2.0-flash">Gemini 2.0 Flash (最新世代)</option>
                                            <option value="models/gemini-1.5-pro">Gemini 1.5 Pro (高品質)</option>
                                        </>
                                    )}
                                </select>
                            </div>

                            {/* API Key */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                    Google AI API Key
                                </label>
                                <input
                                    type="password"
                                    value={geminiData.apiKey}
                                    onChange={(e) => setGeminiData({ ...geminiData, apiKey: e.target.value })}
                                    placeholder={language === 'zh' ? '輸入您的 Google AI API Key...' : 'Enter your Google AI API Key...'}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        borderRadius: '8px',
                                        border: '1px solid var(--glass-border)',
                                        background: '#1a1a1a',
                                        color: 'white'
                                    }}
                                />
                            </div>

                            {/* Buttons */}
                            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                                {geminiData.apiKey && (
                                    <button
                                        onClick={async () => {
                                            setAiLoading(true);
                                            try {
                                                await saveAiSettingsToServer({ gemini_api_key: '' });
                                                setGeminiData({ apiKey: '', model: 'gemini-2.5-flash' });
                                                setStatus({ type: 'success', message: language === 'zh' ? '已清除 Google Gemini 設定' : 'Google Gemini settings cleared' });
                                            } catch (err) {
                                                setStatus({ type: 'error', message: err.message });
                                            } finally {
                                                setAiLoading(false);
                                            }
                                        }}
                                        style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: '#f87171', cursor: 'pointer' }}
                                    >
                                        {language === 'zh' ? '清除' : 'Clear'}
                                    </button>
                                )}
                                <button
                                    onClick={async () => {
                                        if (!geminiData.apiKey) {
                                            setStatus({ type: 'error', message: language === 'zh' ? '請輸入 API Key' : 'Please enter API Key' });
                                            return;
                                        }
                                        setAiLoading(true);
                                        try {
                                            await saveAiSettingsToServer({
                                                gemini_api_key: geminiData.apiKey,
                                                ai_model: geminiData.model
                                            });
                                            setStatus({ type: 'success', message: language === 'zh' ? '✅ Google Gemini 設定已儲存至伺服器' : '✅ Google Gemini settings saved to server' });
                                        } catch (err) {
                                            setStatus({ type: 'error', message: language === 'zh' ? `❌ 儲存失敗: ${err.message}` : `❌ Save failed: ${err.message}` });
                                        } finally {
                                            setAiLoading(false);
                                        }
                                    }}
                                    disabled={aiLoading}
                                    style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: aiLoading ? 'gray' : 'var(--accent-primary)', color: 'white', cursor: aiLoading ? 'not-allowed' : 'pointer' }}
                                >
                                    {aiLoading ? (language === 'zh' ? '儲存中...' : 'Saving...') : (language === 'zh' ? '儲存設定' : 'Save')}
                                </button>
                                {/* Test Connection Button */}
                                <button
                                    onClick={async () => {
                                        setAiLoading(true);
                                        setStatus({ type: 'info', message: language === 'zh' ? '正在測試連線...' : 'Testing connection...' });
                                        try {
                                            const token = localStorage.getItem('google_token');
                                            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                                            const res = await fetch(`${apiUrl}/api/ai/test-gemini`, {
                                                method: 'POST',
                                                headers: { 
                                                    'Authorization': `Bearer ${token}`,
                                                    'Content-Type': 'application/json'
                                                },
                                                body: JSON.stringify({ model: geminiData.model })
                                            });
                                            const data = await res.json();
                                            if (data.success) {
                                                setStatus({ type: 'success', message: language === 'zh' ? `✅ 連線成功！模型: ${data.model}` : `✅ Connected! Model: ${data.model}` });
                                            } else {
                                                setStatus({ type: 'error', message: language === 'zh' ? `❌ 連線失敗: ${data.message}` : `❌ Failed: ${data.message}` });
                                            }
                                        } catch (err) {
                                            setStatus({ type: 'error', message: language === 'zh' ? `❌ 測試錯誤: ${err.message}` : `❌ Test error: ${err.message}` });
                                        } finally {
                                            setAiLoading(false);
                                        }
                                    }}
                                    disabled={aiLoading}
                                    style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: 'var(--text-secondary)', cursor: aiLoading ? 'not-allowed' : 'pointer' }}
                                >
                                    {language === 'zh' ? '🔗 測試連線' : '🔗 Test'}
                                </button>
                            </div>

                            {/* Info Note */}
                            <div style={{
                                padding: '12px', borderRadius: '8px',
                                background: 'rgba(74, 222, 128, 0.1)',
                                border: '1px solid rgba(74, 222, 128, 0.2)',
                                fontSize: '0.85rem',
                                color: '#4ade80'
                            }}>
                                💡 {language === 'zh'
                                    ? '儲存後，請到上方切換啟用的 AI 模組為「💎 Gemini」即可開始使用。'
                                    : 'After saving, switch to "💎 Gemini" in the provider selector above to start using it.'}
                            </div>
                        </div>
                    )}
                    {activeTab === 'line' && (
                        <LineBindingCard language={language} />
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
