import React from 'react';

const isOpenRouterProvider = (provider) => provider === 'openrouter' || provider === 'gemini';

const ActiveAiProviderSelector = ({
    activeAiProvider,
    fetchAiSettings,
    language,
    saveAiSettingsToServer,
    setActiveAiProvider,
    setStatus,
}) => (
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
                color: isOpenRouterProvider(activeAiProvider) ? '#60a5fa' : '#4ade80',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
            }}>
                {isOpenRouterProvider(activeAiProvider) ? '💎 OpenRouter' : '🚀 Zeabur AI Hub'}
            </span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
            <button
                onClick={async () => {
                    setActiveAiProvider('zeabur');
                    localStorage.setItem('ai_provider', 'zeabur');
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
                    const settings = await fetchAiSettings();
                    if (!settings?.has_openrouter_key && !settings?.has_gemini_key) {
                        setStatus({ type: 'error', message: language === 'zh' ? '請先在 OpenRouter 分頁設定 API Key' : 'Please configure API Key in OpenRouter tab first' });
                        return;
                    }
                    setActiveAiProvider('openrouter');
                    localStorage.setItem('ai_provider', 'openrouter');
                    try {
                        await saveAiSettingsToServer({ ai_provider: 'openrouter' });
                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 OpenRouter' : 'Switched to OpenRouter' });
                    } catch (err) {
                        setStatus({ type: 'success', message: language === 'zh' ? '已切換為 OpenRouter (本地)' : 'Switched to OpenRouter (local)' });
                    }
                }}
                style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: isOpenRouterProvider(activeAiProvider) ? '2px solid #60a5fa' : '1px solid var(--glass-border)',
                    background: isOpenRouterProvider(activeAiProvider) ? 'rgba(96, 165, 250, 0.1)' : 'transparent',
                    color: isOpenRouterProvider(activeAiProvider) ? '#60a5fa' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: isOpenRouterProvider(activeAiProvider) ? 'bold' : 'normal'
                }}
            >
                💎 OpenRouter
            </button>
        </div>
    </div>
);

export default ActiveAiProviderSelector;
