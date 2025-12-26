
import React, { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';

const GSCConnect = ({ onConnect, language }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const login = useGoogleLogin({
        onSuccess: async (codeResponse) => {
            setLoading(true);
            setError(null);
            try {
                const response = await fetch('/api/gsc/authorize', {
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
        scope: 'https://www.googleapis.com/auth/webmasters.readonly openid email profile',
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

                {/* Google Icon Circle */}
                <div style={iconCircleStyle}>
                    <svg viewBox="0 0 48 48" style={{ width: '100%', height: '100%' }}>
                        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
                        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
                        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
                        <path fill="#34A853" d="M24 48c6.48 0 12.01-2.09 15.61-5.67l-7.73-6c-2.15 1.45-4.92 2.3-7.88 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
                        <path fill="none" d="M0 0h48v48H0z"></path>
                    </svg>
                </div>

                <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: 'var(--text-primary)', textAlign: 'center' }}>
                    {t('連結 Google Search Console', 'Connect Search Console')}
                </h2>

                <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', textAlign: 'center', lineHeight: '1.6' }}>
                    {t('解鎖來自 Google 的搜尋洞察。即時監控關鍵字排名與 SEO 健康狀況。', 'Unlock insights straight from Google. Monitor keyword rankings and SEO health in real-time.')}
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
                    {t('由 GSC API 提供支援', 'Powered by GSC API')}
                </p>
            </div>
        </div>
    );
};

export default GSCConnect;

