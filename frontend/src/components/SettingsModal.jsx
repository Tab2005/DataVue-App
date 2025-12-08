import React, { useState } from 'react';

const SettingsModal = ({ isOpen, onClose, language }) => {
    const [formData, setFormData] = useState({
        appId: '',
        appSecret: '',
        shortToken: ''
    });
    const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: '' }
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const t = {
        title: language === 'zh' ? '設定 API 連線' : 'API Connection Settings',
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
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/auth/exchange-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    app_id: formData.appId,
                    app_secret: formData.appSecret,
                    short_token: formData.shortToken
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setStatus({ type: 'success', message: t.success });
                setFormData({ appId: '', appSecret: '', shortToken: '' });
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
        <div style={{
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
            zIndex: 1000
        }}>
            <div className="glass-panel" style={{
                width: '500px',
                padding: '32px',
                borderRadius: 'var(--radius-xl)',
                backgroundColor: '#242526'
            }}>
                <h2 style={{ marginBottom: '24px', fontSize: '1.5rem' }}>{t.title}</h2>

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
