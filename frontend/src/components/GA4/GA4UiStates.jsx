import React from 'react';

export const GA4LoadingState = ({ loading, t }) => {
    if (!loading) return null;

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 20px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            margin: '20px 0'
        }}>
            <div style={{
                width: '48px',
                height: '48px',
                border: '4px solid rgba(52, 168, 83, 0.2)',
                borderTop: '4px solid #34a853',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: '20px'
            }} />
            <div style={{
                fontSize: '16px',
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: '8px'
            }}>
                {t('正在載入 GA4 數據', 'Loading GA4 data')}
            </div>
            <div style={{
                fontSize: '14px',
                color: 'var(--text-secondary)',
                textAlign: 'center'
            }}>
                {t('請稍候...', 'Please wait...')}
            </div>
            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export const GA4ErrorState = ({ error }) => {
    if (!error) return null;

    return (
        <div style={{
            padding: '16px',
            background: 'rgba(234, 67, 53, 0.1)',
            color: '#ea4335',
            borderRadius: '8px',
            border: '1px solid rgba(234, 67, 53, 0.2)',
            marginBottom: '24px'
        }}>
            ⚠️ {error}
        </div>
    );
};

export const GA4NoDataState = ({ analyticsData, error, loading, selectedProperty, t }) => {
    const hasRows = analyticsData?.rows?.length > 0;
    if (loading || error || hasRows || !selectedProperty) return null;

    return (
        <div style={{
            textAlign: 'center',
            padding: '40px',
            color: 'var(--text-secondary)'
        }}>
            {t('此日期範圍內沒有數據', 'No data available for this date range')}
        </div>
    );
};
