import React, { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';

const GA4Connect = ({ onConnect, language }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const login = useGoogleLogin({
        onSuccess: async (codeResponse) => {
            if (loading) return; // Prevent double submission
            setLoading(true);
            setError(null);
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/ga4/authorize`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('google_token')}`
                    },
                    body: JSON.stringify({ code: codeResponse.code }),
                });

                const text = await response.text();
                let data;
                try {
                    data = text ? JSON.parse(text) : {};
                } catch (e) {
                    console.error("Non-JSON API Response:", text);
                    throw new Error(`Server Error (${response.status})`);
                }

                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to connect');
                }

                if (onConnect) onConnect();
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        },
        onError: (errorResponse) => {
            setError('Google Login Failed');
            console.error(errorResponse);
        },
        flow: 'auth-code',
        scope: 'https://www.googleapis.com/auth/analytics.readonly https://www.googleapis.com/auth/analytics.edit openid email profile',
    });

    // Inline Styles for Glassmorphism (Since Tailwind is not available)
    const containerStyle = {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px',
        maxWidth: '500px',
        margin: '0 auto',
        overflow: 'hidden',
        minHeight: '400px',
    };

    const blobStyle = {
        position: 'absolute',
        borderRadius: '50%',
        filter: 'blur(60px)',
        opacity: 0.3,
        zIndex: 0,
        animation: 'pulse 4s infinite ease-in-out',
    };

    const cardStyle = {
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        padding: '40px',
        background: 'rgba(36, 37, 38, 0.6)', // var(--glass-bg)
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '24px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    };

    const iconCircleStyle = {
        width: '80px',
        height: '80px',
        background: 'white',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '24px',
        padding: '16px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    };

    const buttonStyle = {
        marginTop: '24px',
        padding: '14px 28px',
        background: loading ? '#555' : 'linear-gradient(135deg, #4285F4, #34A853)',
        color: 'white',
        border: 'none',
        borderRadius: '12px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.7 : 1,
        transition: 'transform 0.2s',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        boxShadow: '0 4px 15px rgba(66, 133, 244, 0.3)',
    };

    return (
        <div style={containerStyle}>

            {/* Background Decor Elements */}
            <div style={{ ...blobStyle, top: '-20px', left: '-20px', width: '200px', height: '200px', background: '#4285F4' }}></div>
            <div style={{ ...blobStyle, top: '20px', right: '-20px', width: '180px', height: '180px', background: '#EA4335', animationDelay: '1s' }}></div>
            <div style={{ ...blobStyle, bottom: '-40px', left: '60px', width: '160px', height: '160px', background: '#34A853', animationDelay: '2s' }}></div>

            {/* Glassmorphism Card */}
            <div style={cardStyle}>

                {/* Google Analytics Icon Circle */}
                <div style={iconCircleStyle}>
                    <svg viewBox="0 0 48 48" style={{ width: '100%', height: '100%' }}>
                        <path fill="#E37400" d="M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm0 36c-8.84 0-16-7.16-16-16S15.16 8 24 8s16 7.16 16 16-7.16 16-16 16z"/>
                        <path fill="#E37400" d="M24 12c-4.42 0-8 3.58-8 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 12c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"/>
                        <path fill="#F9AB00" d="M32 28c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2s2 .9 2 2v4c0 1.1-.9 2-2 2z"/>
                        <path fill="#F9AB00" d="M16 28c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2s2 .9 2 2v4c0 1.1-.9 2-2 2z"/>
                    </svg>
                </div>

                <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: 'var(--text-primary)', textAlign: 'center' }}>
                    {t('連結 Google Analytics 4', 'Connect Google Analytics 4')}
                </h2>

                <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', textAlign: 'center', lineHeight: '1.6' }}>
                    {t('解鎖來自 Google Analytics 的流量洞察。即時監控用戶行為與網站成效。', 'Unlock insights from Google Analytics. Monitor user behavior and website performance in real-time.')}
                </p>

                {error && (
                    <div style={{ marginBottom: '20px', padding: '12px', background: 'rgba(234, 67, 53, 0.1)', color: '#ea4335', borderRadius: '8px', border: '1px solid rgba(234, 67, 53, 0.2)', fontSize: '14px', width: '100%', textAlign: 'center' }}>
                        ⚠️ {error}
                    </div>
                )}

                <button
                    onClick={() => login()}
                    disabled={loading}
                    style={buttonStyle}
                    onMouseEnter={(e) => {
                        if (!loading) e.currentTarget.style.transform = 'scale(1.02)';
                    }}
                    onMouseLeave={(e) => {
                        if (!loading) e.currentTarget.style.transform = 'scale(1)';
                    }}
                >
                    {loading ? t('連線中...', 'Connecting...') : t('連結 Google 帳號', 'Link Google Account')}
                </button>

                <p style={{ marginTop: '20px', fontSize: '12px', color: 'var(--text-secondary)', opacity: 0.7, textTransform: 'uppercase', letterSpacing: '1px' }}>
                    {t('由 GA4 API 提供支援', 'Powered by GA4 API')}
                </p>
            </div>
        </div>
    );
};

export default GA4Connect;