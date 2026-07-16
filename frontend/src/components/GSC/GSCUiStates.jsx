import React from 'react';

export const GSCInitialLoadingState = ({ t }) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '16px',
        border: '1px solid var(--glass-border)',
        margin: '20px'
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
            {t('正在載入 Search Console 網站列表', 'Loading Search Console sites')}
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

export const GSCErrorState = ({ error, t }) => (
    <div style={{ padding: '20px', color: '#ea4335' }}>
        {t('錯誤:', 'Error:')} {error}
    </div>
);

export const GSCDataLoadingState = ({ t }) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 20px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        color: 'var(--text-secondary)',
        gap: '12px'
    }}>
        <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(52, 168, 83, 0.2)',
            borderTop: '3px solid #34a853',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
        }} />
        <div>{t('正在載入分析資料...', 'Loading analytics data...')}</div>
        <style>{`
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `}</style>
    </div>
);
