import React from 'react';
import { FiRefreshCw } from 'react-icons/fi';

const darkInputStyle = {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)'
};

const lightInputStyle = {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: '#ffffff',
    color: '#000000'
};

const OpenRouterSettingsTab = ({
    aiLoading,
    fetchAvailableModels,
    isCustomModel,
    isSyncingModels,
    language,
    openrouterData,
    openrouterModels,
    saveAiSettingsToServer,
    setAiLoading,
    setIsCustomModel,
    setOpenrouterData,
    setStatus,
}) => {
    const clearSettings = async () => {
        setAiLoading(true);
        try {
            await saveAiSettingsToServer({ openrouter_api_key: '' });
            setOpenrouterData({ apiKey: '', model: 'deepseek/deepseek-v4-flash' });
            setStatus({ type: 'success', message: language === 'zh' ? '已清除 OpenRouter 設定' : 'OpenRouter settings cleared' });
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setAiLoading(false);
        }
    };

    const saveSettings = async () => {
        if (!openrouterData.apiKey) {
            setStatus({ type: 'error', message: language === 'zh' ? '請輸入 API Key' : 'Please enter API Key' });
            return;
        }
        setAiLoading(true);
        try {
            await saveAiSettingsToServer({
                openrouter_api_key: openrouterData.apiKey === '********' ? null : openrouterData.apiKey,
                ai_model: openrouterData.model,
                ai_provider: 'openrouter'
            });
            setStatus({ type: 'success', message: language === 'zh' ? '✅ OpenRouter 設定已儲存至伺服器' : '✅ OpenRouter settings saved to server' });
        } catch (err) {
            setStatus({ type: 'error', message: language === 'zh' ? `❌ 儲存失敗: ${err.message}` : `❌ Save failed: ${err.message}` });
        } finally {
            setAiLoading(false);
        }
    };

    const testConnection = async () => {
        setAiLoading(true);
        setStatus({ type: 'info', message: language === 'zh' ? '正在測試連線...' : 'Testing connection...' });
        try {
            const token = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/ai/test-connection`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: openrouterData.apiKey === '********' ? null : openrouterData.apiKey,
                    provider: 'openrouter',
                    model: openrouterData.model
                })
            });
            const data = await res.json();
            if (res.ok) {
                setStatus({ type: 'success', message: language === 'zh' ? `✅ 連線成功！模型: ${openrouterData.model}` : `✅ Connected! Model: ${openrouterData.model}` });
            } else {
                setStatus({ type: 'error', message: language === 'zh' ? `❌ 連線失敗: ${data.detail || data.message}` : `❌ Failed: ${data.detail || data.message}` });
            }
        } catch (err) {
            setStatus({ type: 'error', message: language === 'zh' ? `❌ 測試錯誤: ${err.message}` : `❌ Test error: ${err.message}` });
        } finally {
            setAiLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{
                padding: '16px', borderRadius: '8px',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                background: 'rgba(59, 130, 246, 0.05)',
                display: 'flex', alignItems: 'flex-start', gap: '12px'
            }}>
                <div style={{ fontSize: '24px' }}>💎</div>
                <div>
                    <div style={{ fontWeight: 'bold', color: '#60a5fa' }}>
                        {language === 'zh' ? 'OpenRouter 整合模式' : 'OpenRouter Integration Mode'}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {language === 'zh'
                            ? '直接使用 OpenRouter 的 API Key，解鎖對 DeepSeek、Gemini、Claude 與 GPT 的高速直連。'
                            : 'Directly use OpenRouter API Key to unlock high-speed connections to DeepSeek, Gemini, Claude, and GPT.'}
                    </div>
                    <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '0.85rem', color: '#60a5fa', textDecoration: 'underline', marginTop: '8px', display: 'inline-block' }}
                    >
                        {language === 'zh' ? '👉 前往 OpenRouter 取得 API Key' : '👉 Get API Key from OpenRouter'}
                    </a>
                </div>
            </div>

            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ color: 'var(--text-secondary)' }}>
                        {language === 'zh' ? 'OpenRouter 模型' : 'OpenRouter Model'}
                    </label>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <button 
                            onClick={() => {
                                const nextCustom = !isCustomModel;
                                setIsCustomModel(nextCustom);
                                if (!nextCustom) {
                                    setOpenrouterData(prev => ({ ...prev, model: 'deepseek/deepseek-v4-flash' }));
                                }
                            }}
                            style={{ 
                                background: 'transparent', border: 'none', color: '#60a5fa', 
                                cursor: 'pointer', fontSize: '12px', textDecoration: 'underline'
                            }}
                        >
                            {isCustomModel 
                                ? (language === 'zh' ? '選擇預設模型' : 'Choose Preset') 
                                : (language === 'zh' ? '👉 自定義模型 ID' : '👉 Custom Model ID')
                            }
                        </button>
                        {!isCustomModel && (
                            <button 
                                onClick={() => fetchAvailableModels('openrouter', true)}
                                disabled={isSyncingModels}
                                style={{ 
                                    background: 'transparent', border: 'none', color: 'var(--accent-primary)', 
                                    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' 
                                }}
                            >
                                <FiRefreshCw className={isSyncingModels ? 'spin' : ''} size={12} />
                                {language === 'zh' ? '同步' : 'Sync'}
                            </button>
                        )}
                    </div>
                </div>
                {isCustomModel ? (
                    <input
                        type="text"
                        value={openrouterData.model}
                        onChange={(e) => setOpenrouterData({ ...openrouterData, model: e.target.value })}
                        placeholder={language === 'zh' ? '例如: mistralai/pixtral-12b 或 cohere/command-r' : 'e.g., mistralai/pixtral-12b'}
                        style={lightInputStyle}
                    />
                ) : (
                    <select
                        value={openrouterData.model}
                        onChange={(e) => setOpenrouterData({ ...openrouterData, model: e.target.value })}
                        style={darkInputStyle}
                    >
                        {Object.entries(openrouterModels).length > 0 ? (
                            Object.entries(openrouterModels).map(([id, config]) => (
                                <option key={id} value={id}>
                                    {config.display_name || id}
                                </option>
                            ))
                        ) : (
                            <>
                                <option value="deepseek/deepseek-v4-flash">DeepSeek V4 Flash (預設)</option>
                                <option value="deepseek/deepseek-chat">DeepSeek V3 (Chat)</option>
                                <option value="google/gemini-2.5-flash">Gemini 2.5 Flash</option>
                                <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                            </>
                        )}
                    </select>
                )}
            </div>

            <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                    OpenRouter API Key
                </label>
                <input
                    type="password"
                    value={openrouterData.apiKey}
                    onChange={(e) => setOpenrouterData({ ...openrouterData, apiKey: e.target.value })}
                    placeholder={language === 'zh' ? '輸入您的 OpenRouter API Key...' : 'Enter your OpenRouter API Key...'}
                    style={lightInputStyle}
                />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                {openrouterData.apiKey && (
                    <button
                        onClick={clearSettings}
                        style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: '#f87171', cursor: 'pointer' }}
                    >
                        {language === 'zh' ? '清除' : 'Clear'}
                    </button>
                )}
                <button
                    onClick={saveSettings}
                    disabled={aiLoading}
                    style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: aiLoading ? 'gray' : 'var(--accent-primary)', color: 'white', cursor: aiLoading ? 'not-allowed' : 'pointer' }}
                >
                    {aiLoading ? (language === 'zh' ? '儲存中...' : 'Saving...') : (language === 'zh' ? '儲存設定' : 'Save')}
                </button>
                <button
                    onClick={testConnection}
                    disabled={aiLoading}
                    style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'transparent', color: 'var(--text-secondary)', cursor: aiLoading ? 'not-allowed' : 'pointer' }}
                >
                    {language === 'zh' ? '🔗 測試連線' : '🔗 Test'}
                </button>
            </div>

            <div style={{
                padding: '12px', borderRadius: '8px',
                background: 'rgba(74, 222, 128, 0.1)',
                border: '1px solid rgba(74, 222, 128, 0.2)',
                fontSize: '0.85rem',
                color: '#4ade80'
            }}>
                💡 {language === 'zh'
                    ? '儲存後，請到上方切換啟用的 AI 模組為「💎 OpenRouter」即可開始使用。'
                    : 'After saving, switch to "💎 OpenRouter" in the provider selector above to start using it.'}
            </div>
        </div>
    );
};

export default OpenRouterSettingsTab;
