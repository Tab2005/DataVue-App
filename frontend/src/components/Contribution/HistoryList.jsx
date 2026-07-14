import React from 'react';

import { InfoPanel, secondaryButtonStyle, Section, t } from './ContributionShared';

const HistoryList = ({ language, history, loading, onSelect, onRefresh, selectedId, isMobile }) => {
    return (
        <Section
            title={t(language, 'Analysis History', '歷史分析快照')}
            subtitle={t(
                language,
                'Past analyses for this account. Click to load a snapshot.',
                '此帳戶的歷次分析。點選以載入快照。'
            )}
        >
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
                <button type="button" onClick={onRefresh} style={secondaryButtonStyle}>
                    {t(language, 'Refresh', '重新整理')}
                </button>
            </div>
            {loading ? (
                <InfoPanel message={t(language, 'Loading history…', '載入歷史中…')} />
            ) : history.length === 0 ? (
                <InfoPanel message={t(language, 'No analysis yet.', '尚無分析紀錄。')} />
            ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                    {history.map((row) => {
                        const isSelected = row.snapshot_id === selectedId;
                        const statusColor = {
                            completed: '#10b981',
                            processing: '#f59e0b',
                            queued: '#3b82f6',
                            failed: '#ef4444',
                        }[row.status] || '#9ca3af';
                        return (
                            <button
                                key={row.snapshot_id}
                                type="button"
                                onClick={() => onSelect(row.snapshot_id)}
                                style={{
                                    textAlign: 'left',
                                    padding: '10px 12px',
                                    borderRadius: '10px',
                                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
                                    background: isSelected ? 'rgba(45, 136, 255, 0.08)' : 'rgba(255,255,255,0.02)',
                                    color: 'var(--text-primary)',
                                    cursor: 'pointer',
                                    fontSize: '0.82rem',
                                }}
                            >
                                <div
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        gap: '8px',
                                        alignItems: 'center',
                                        flexWrap: isMobile ? 'wrap' : 'nowrap',
                                    }}
                                >
                                    <div>
                                        <div style={{ fontWeight: 600 }}>
                                            {row.date_start} ~ {row.date_end}
                                        </div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                            {row.snapshot_id}
                                        </div>
                                    </div>
                                    <div
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                            color: statusColor,
                                            fontWeight: 600,
                                            fontSize: '0.78rem',
                                        }}
                                    >
                                        <span
                                            style={{
                                                width: '8px',
                                                height: '8px',
                                                borderRadius: '50%',
                                                background: statusColor,
                                            }}
                                        />
                                        {row.status}
                                    </div>
                                </div>
                                {row.error_message && (
                                    <div
                                        style={{
                                            marginTop: '4px',
                                            color: '#fca5a5',
                                            fontSize: '0.72rem',
                                            whiteSpace: 'pre-wrap',
                                        }}
                                    >
                                        {row.error_message}
                                    </div>
                                )}
                            </button>
                        );
                    })}
                </div>
            )}
        </Section>
    );
};

export default HistoryList;
