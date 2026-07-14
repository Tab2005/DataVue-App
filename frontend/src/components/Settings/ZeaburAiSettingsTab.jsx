import React from 'react';
import { FiRefreshCw } from 'react-icons/fi';

const inputStyle = {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)'
};

const ZeaburAiSettingsTab = ({
    aiConnectionStatus,
    aiData,
    aiLoading,
    fetchAvailableModels,
    handleClearAiKey,
    handleSaveAiKey,
    handleTestConnection,
    isSyncingModels,
    language,
    setAiData,
    t,
    zeaburModels,
}) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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

        {aiConnectionStatus !== 'connected_zeabur' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', opacity: aiLoading ? 0.5 : 1 }}>
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
                        style={inputStyle}
                    >
                        {Object.entries(zeaburModels).length > 0 ? (
                            <>
                                {Array.from(new Set(Object.values(zeaburModels).map(m => m.provider))).map(provider => (
                                    <optgroup key={provider} label={provider.toUpperCase()} style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)' }}>
                                        {Object.entries(zeaburModels)
                                            .filter(([_, config]) => config.provider === provider)
                                            .map(([id, config]) => (
                                                <option key={id} value={id}>
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
                        style={inputStyle}
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
);

export default ZeaburAiSettingsTab;
