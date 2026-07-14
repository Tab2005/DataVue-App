import React, { useState, useEffect } from 'react';
import ActiveAiProviderSelector from './Settings/ActiveAiProviderSelector';
import FacebookSettingsTab from './Settings/FacebookSettingsTab';
import LineBindingCard from './Settings/LineBindingCard';
import OpenRouterSettingsTab from './Settings/OpenRouterSettingsTab';
import SettingsTabs from './Settings/SettingsTabs';
import ZeaburAiSettingsTab from './Settings/ZeaburAiSettingsTab';

const SettingsModal = ({ isOpen, onClose, language, teamId, teamName, onSuccess }) => {
    // Tabs: 'facebook' | 'ai' | 'gemini' | 'line'
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
        model: 'deepseek/deepseek-v4-flash'
    });

    // OpenRouter Direct API Data
    const [openrouterData, setOpenrouterData] = useState({
        apiKey: '',
        model: 'deepseek/deepseek-v4-flash'
    });

    // Available models from backend (Separate lists)
    const [zeaburModels, setZeaburModels] = useState({});
    const [openrouterModels, setOpenrouterModels] = useState({});
    const [isCustomModel, setIsCustomModel] = useState(false);

    // Status & Loading (separate for FB and AI tabs)
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [fbLoading, setFbLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

    // Token Info (Facebook)
    const [tokenInfo, setTokenInfo] = useState(null);

    // Zeabur / AI Status
    const [aiConnectionStatus, setAiConnectionStatus] = useState('unknown'); // unknown, connected_zeabur, connected_user, disconnected

    // Active AI Provider preference: 'zeabur' | 'openrouter'
    const [activeAiProvider, setActiveAiProvider] = useState('zeabur');

    const t = {
        title: language === 'zh' ? '整合中心 (Integration Center)' : 'Integration Center',
        tabs: {
            facebook: 'Facebook Ads',
            ai: 'Zeabur AI Hub',
            gemini: 'OpenRouter',
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
                } else if (provider === 'openrouter') {
                    setOpenrouterModels(data.models || {});
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
        const savedModel = localStorage.getItem('ai_model') || 'deepseek/deepseek-v4-flash';

        if (localKey) {
            setAiData(prev => ({ ...prev, apiKey: localKey, provider: savedProvider, model: savedModel }));
        } else {
            setAiData(prev => ({ ...prev, provider: savedProvider, model: savedModel }));
        }

        // Fetch BOTH model lists initially
        await Promise.all([
            fetchAvailableModels('zeabur'),
            fetchAvailableModels('openrouter')
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
                zeabur_api_key: aiData.apiKey === '********' ? null : aiData.apiKey,
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
        } catch {
            setStatus({ type: 'error', message: language === 'zh' ? '❌ 連線失敗' : '❌ Connection Failed' });
            setAiConnectionStatus('disconnected');
        } finally {
            setAiLoading(false);
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
            // Reset status
            setStatus(null);
            // Fetch Facebook token status
            fetchTokenStatus();

            // Fetch AI settings from backend
            fetchAiSettings().then(settings => {
                if (settings) {
                    const provider = settings.ai_provider || 'zeabur';
                    setActiveAiProvider(provider);
                    
                    // 自動切換標籤頁到目前啟用的 AI Provider
                    if (provider === 'gemini' || provider === 'google_gemini' || provider === 'openrouter') {
                        setActiveTab('gemini');
                    } else if (provider === 'zeabur') {
                        setActiveTab('ai');
                    }

                    const activeModel = settings.ai_model || 'deepseek/deepseek-v4-flash';
                    const presets = ['deepseek/deepseek-v4-flash', 'deepseek/deepseek-chat', 'google/gemini-2.5-flash', 'anthropic/claude-3.5-sonnet'];
                    const isPreset = presets.includes(activeModel);

                    setAiData(prev => ({ 
                        ...prev, 
                        model: activeModel,
                        apiKey: settings.has_zeabur_key ? '********' : ''
                    }));
                    setOpenrouterData(prev => ({ 
                        ...prev, 
                        model: activeModel,
                        apiKey: (settings.has_openrouter_key || settings.has_gemini_key) ? '********' : ''
                    }));

                    if (!isPreset && activeModel && (provider === 'openrouter' || provider === 'gemini' || provider === 'google_gemini')) {
                        setIsCustomModel(true);
                    } else {
                        setIsCustomModel(false);
                    }
                    // Store provider in localStorage for GSCStats to use (sync purpose only)
                    localStorage.setItem('ai_provider', provider);
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

    // Switch to Gemini (now OpenRouter) tab - settings already loaded from backend
    useEffect(() => {
        if (isOpen && activeTab === 'gemini') {
            // Settings already loaded from backend on modal open
            // openrouterData.apiKey will be empty since we don't expose keys to frontend
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

                {(activeTab === 'ai' || activeTab === 'gemini') && (
                    <ActiveAiProviderSelector
                        activeAiProvider={activeAiProvider}
                        fetchAiSettings={fetchAiSettings}
                        language={language}
                        saveAiSettingsToServer={saveAiSettingsToServer}
                        setActiveAiProvider={setActiveAiProvider}
                        setStatus={setStatus}
                    />
                )}

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

                    {activeTab === 'ai' && (
                        <ZeaburAiSettingsTab
                            aiConnectionStatus={aiConnectionStatus}
                            aiData={aiData}
                            aiLoading={aiLoading}
                            fetchAvailableModels={fetchAvailableModels}
                            handleClearAiKey={handleClearAiKey}
                            handleSaveAiKey={handleSaveAiKey}
                            handleTestConnection={handleTestConnection}
                            isSyncingModels={isSyncingModels}
                            language={language}
                            setAiData={setAiData}
                            t={t}
                            zeaburModels={zeaburModels}
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
