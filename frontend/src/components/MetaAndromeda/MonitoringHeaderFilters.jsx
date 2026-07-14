import React from 'react';

import {
    actionButtonStyle,
    errorPanelStyle,
    inputStyle,
    toggleLabelStyle,
} from './shared';

export const MonitoringHeaderFilters = ({ isMobile, monitoring }) => {
    const {
        summary,
        error,
        hostFilter,
        setHostFilter,
        eventQuery,
        setEventQuery,
        deadLetterOnly,
        setDeadLetterOnly,
        t,
        loadSummary,
    } = monitoring;

    return (
        <>
            {/* 注入精美磨砂玻璃滾動條樣式 */}
            <style>{`
                .queue-scroll-box::-webkit-scrollbar {
                    width: 6px;
                }
                .queue-scroll-box::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.01);
                    border-radius: 999px;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb {
                    background: var(--glass-border);
                    border-radius: 999px;
                    transition: all 0.2s;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb:hover {
                    background: var(--accent-primary);
                }
            `}</style>

            <div style={{
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: '16px',
                flexDirection: isMobile ? 'column' : 'row',
            }}>
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        Meta Andromeda
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t('Monitoring Summary', '監控總覽')}
                    </h1>
                </div>
                <button type="button" onClick={loadSummary} style={actionButtonStyle}>
                    {t('Refresh', '重新整理')}
                </button>
            </div>

            <div style={{
                marginBottom: '16px',
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '1.1fr 0.8fr auto',
                gap: '10px',
                alignItems: 'center',
                padding: '14px 18px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--glass-border)',
                borderRadius: '14px',
            }}>
                <input
                    type="text"
                    value={eventQuery}
                    onChange={(event) => setEventQuery(event.target.value)}
                    placeholder={t('Search score event, runtime job, or message', '搜尋評分事件、執行任務或訊息')}
                    style={inputStyle}
                />
                <select value={hostFilter} onChange={(event) => setHostFilter(event.target.value)} style={inputStyle}>
                    <option value="all">{t('All Hosts', '所有主機')}</option>
                    {Array.from(new Set([
                        summary?.worker_host?.active_host,
                        ...(summary?.worker_host?.recent_events || []).map((event) => event.queue_host),
                        ...(summary?.worker_host?.dead_letters || []).map((item) => item.queue_host),
                    ].filter(Boolean))).map((host) => (
                        <option key={host} value={host}>{host}</option>
                    ))}
                </select>
                <label style={toggleLabelStyle}>
                    <input
                        type="checkbox"
                        checked={deadLetterOnly}
                        onChange={(event) => setDeadLetterOnly(event.target.checked)}
                    />
                    <span>{t('Dead Letters Only', '只看異常任務')}</span>
                </label>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}
        </>
    );
};
