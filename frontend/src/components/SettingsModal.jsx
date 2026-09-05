import React, { useState, useEffect } from 'react';
import FacebookSettingsTab from './Settings/FacebookSettingsTab';
import LineBindingCard from './Settings/LineBindingCard';
import OpenRouterSettingsTab from './Settings/OpenRouterSettingsTab';
import SettingsTabs from './Settings/SettingsTabs';

const SettingsModal = ({ isOpen, onClose, language, teamId, teamName, onSuccess }) => {
    // Tabs: 'facebook' | 'gemini' | 'line'
    const [activeTab, setActiveTab] = useState('facebook');

    // Facebook Form Data
    const [fbData, setFbData] = useState({
        appId: '',
        appSecret: '',
        shortToken: ''
    });

    // OpenRouter Direct API Data
    const [openrouterData, setOpenrouterData] = useState({
        apiKey: '',
        model: 'deepseek/deepseek-v4-flash'
    });

    // Available models from backend
    const [openrouterModels, setOpenrouterModels] = useState({});
    const [isCustomModel, setIsCustomModel] = useState(false);

    // Status & Loading (separate for FB and AI tabs)
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [fbLoading, setFbLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

    // Token Info (Facebook)
    const [tokenInfo, setTokenInfo] = useState(null);

    const t = {
        title: language === 'zh' ? '整合中心 (Integration Center)' : 'Integration Center',
        tabs: {
            facebook: 'Facebook Ads',
            gemini: 'OpenRouter',
            line: language === 'zh' ? 'LINE 通知' : 'LINE Notify'
        },
        fb: {
            appId: 'App ID',
            appSecret: 'App Secret',
            shortToken: language === 'zh' ? '短期權杖 (Short-Lived Token)' : 'Short-Lived Token',
            save: language === 'zh' ? '連線並交換權杖' : 'Connect & Exchange Token',
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
                return data; // { ai_provider, ai_model, has_gemini_key, has_openrouter_key }
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

    const fetchAvailableModels = async (provider = 'openrouter', sync = false) => {
        if (sync) setIsSyncingModels(true);
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/models?provider=${provider}${sync ? '&sync=true' : ''}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setOpenrouterModels(data.models || {});

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

    useEffect(() => {
        if (isOpen) {
            // Reset status
            setStatus(null);
            // Fetch Facebook token status
            fetchTokenStatus();
            // Fetch OpenRouter model list
            fetchAvailableModels('openrouter');

            // Fetch AI settings from backend
            fetchAiSettings().then(settings => {
                if (settings) {
                    const activeModel = settings.ai_model || 'deepseek/deepseek-v4-flash';
                    const presets = ['deepseek/deepseek-v4-flash', 'deepseek/deepseek-chat', 'google/gemini-2.5-flash', 'anthropic/claude-3.5-sonnet'];
                    const isPreset = presets.includes(activeModel);

                    setOpenrouterData(prev => ({
                        ...prev,
                        model: activeModel,
                        apiKey: (settings.has_openrouter_key || settings.has_gemini_key) ? '********' : ''
                    }));

                    setIsCustomModel(!isPreset && !!activeModel);
                    // Store provider in localStorage for GSCStats to use (sync purpose only)
                    localStorage.setItem('ai_provider', 'openrouter');
                }
            });
        }
    }, [isOpen, teamId]);

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

                <SettingsTabs
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    setStatus={setStatus}
                    tabs={t.tabs}
                />

                <div style={{ minHeight: '300px' }}>
                    {activeTab === 'facebook' && (
                        <FacebookSettingsTab
                            fbData={fbData}
                            fbLoading={fbLoading}
                            handleFbSubmit={handleFbSubmit}
                            language={language}
                            setFbData={setFbData}
                            t={t}
                            teamId={teamId}
                            teamName={teamName}
                            tokenInfo={tokenInfo}
                        />
                    )}

                    {activeTab === 'gemini' && (
                        <OpenRouterSettingsTab
                            aiLoading={aiLoading}
                            fetchAvailableModels={fetchAvailableModels}
                            isCustomModel={isCustomModel}
                            isSyncingModels={isSyncingModels}
                            language={language}
                            openrouterData={openrouterData}
                            openrouterModels={openrouterModels}
                            saveAiSettingsToServer={saveAiSettingsToServer}
                            setAiLoading={setAiLoading}
                            setIsCustomModel={setIsCustomModel}
                            setOpenrouterData={setOpenrouterData}
                            setStatus={setStatus}
                        />
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
