import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import GA4Connect from '../components/GA4Connect';
import GA4Stats from '../components/GA4Stats';

const GA4Analytics = () => {
    const { language, isMobile } = useOutletContext();
    const [isConnected, setIsConnected] = useState(false);
    const [checking, setChecking] = useState(true);

    const checkConnection = async () => {
        setChecking(true);
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const resp = await fetch(`${apiUrl}/api/ga4/properties`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` },
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            const contentType = resp.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await resp.json();
                if (resp.ok && data.properties && data.properties.length > 0) {
                    setIsConnected(true);
                } else {
                    // Graceful handling of known errors
                    if (resp.status === 400 && data.detail === "No GA4 credentials found") {
                        setIsConnected(false);
                    } else {
                        console.warn("GA4 Connection Check Failed:", data);
                        setIsConnected(false);
                    }
                }
            } else {
                // Not JSON (likely HTML 404/500), assume not connected or server issue
                console.warn("GA4 API returned non-JSON response:", contentType);
                setIsConnected(false);
            }
        } catch (e) {
            console.error("GA4 Connection Check Error:", e);
            setIsConnected(false);
        } finally {
            setChecking(false);
        }
    };

    useEffect(() => {
        checkConnection();
    }, []);

    const handleConnect = () => {
        // Refresh connection status after successful connection
        setTimeout(() => {
            checkConnection();
        }, 1000);
    };

    if (checking) {
        return (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: 'var(--text-secondary)' }}>
                    {language === 'zh' ? '正在檢查 Google Analytics 4 連線...' : 'Checking Google Analytics 4 connection...'}
                </div>
            </div>
        );
    }

    return (
        <div style={{
            padding: isMobile ? '16px' : '24px',
            width: '100%',
            maxWidth: '100%',
            overflowX: 'hidden',
            overflowY: 'visible',
            boxSizing: 'border-box'
        }}>
            {/* Header Section - Responsive */}
            <header style={{
                marginBottom: isMobile ? '16px' : '24px',
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: isMobile ? '8px' : '0'
            }}>
                <div>
                    <h1 style={{
                        fontSize: isMobile ? '1.5rem' : '1.8rem',
                        fontWeight: '700',
                        color: 'var(--text-primary)',
                        margin: 0
                    }}>
                        Google Analytics 4
                    </h1>
                    <p style={{
                        color: 'var(--text-secondary)',
                        fontSize: isMobile ? '0.9rem' : '1rem',
                        margin: '4px 0 0 0'
                    }}>
                        {language === 'zh' ? '監控您的網站流量與用戶行為分析。' : 'Monitor your website traffic and user behavior analytics.'}
                    </p>
                </div>
            </header>

            {/* Main Content */}
            {!isConnected ? (
                <GA4Connect onConnect={handleConnect} language={language} />
            ) : (
                <GA4Stats language={language} isMobile={isMobile} />
            )}
        </div>
    );
};

export default GA4Analytics;