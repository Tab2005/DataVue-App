import React from 'react';

const observationStatCardStyle = {
    padding: '10px 12px',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid var(--glass-border)',
};

const observationStatLabelStyle = {
    fontSize: '0.76rem',
    color: 'var(--text-secondary)',
    marginBottom: '4px',
};

const observationStatValueStyle = {
    fontSize: '1rem',
    fontWeight: 700,
    color: 'var(--text-primary)',
};

const MetaAndromedaImportActions = ({
    canUseObservationImport,
    isMobile,
    language,
    selectedObservationRows,
    observationImportableRows,
    observationWindowKind,
    observationBatchSummary,
    handleToggleAllObservationRows,
    handleBatchObservationImport,
}) => {
    return (
        <>
            {canUseObservationImport ? (
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    alignItems: isMobile ? 'stretch' : 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    marginBottom: '12px',
                    padding: '12px 14px',
                    borderRadius: '12px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--glass-border)'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {language === 'zh' ? 'Meta Andromeda 匯入操作' : 'Meta Andromeda Import Actions'}
                        </div>
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                            {language === 'zh'
                                ? `已選 ${selectedObservationRows.length} 筆 / 可匯入 ${observationImportableRows.length} 筆`
                                : `${selectedObservationRows.length} selected / ${observationImportableRows.length} importable`}
                            {observationWindowKind === 'custom' && (
                                <span style={{ marginLeft: '8px', color: '#fbbf24' }}>
                                    {language === 'zh'
                                        ? '目前日期區段將以自訂時間區間匯入。'
                                        : 'Current date preset imports as custom range.'}
                                </span>
                            )}
                        </div>
                        {observationBatchSummary?.message && (
                            <div style={{
                                fontSize: '0.8rem',
                                color: observationBatchSummary.status === 'success'
                                    ? '#34d399'
                                    : observationBatchSummary.status === 'warning'
                                        ? '#fbbf24'
                                        : 'var(--text-secondary)',
                                lineHeight: 1.4,
                            }}>
                                {observationBatchSummary.message}
                            </div>
                        )}
                        {observationBatchSummary && (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(3, minmax(90px, 1fr))',
                                gap: '8px',
                                marginTop: '8px',
                            }}>
                                <div style={observationStatCardStyle}>
                                    <div style={observationStatLabelStyle}>
                                        {language === 'zh' ? '本次送出' : 'Attempted'}
                                    </div>
                                    <div style={observationStatValueStyle}>
                                        {observationBatchSummary.attemptedCount ?? '--'}
                                    </div>
                                </div>
                                <div style={observationStatCardStyle}>
                                    <div style={observationStatLabelStyle}>
                                        {language === 'zh' ? '本次送出成功' : 'Accepted'}
                                    </div>
                                    <div style={{ ...observationStatValueStyle, color: '#34d399' }}>
                                        {observationBatchSummary.successCount ?? '--'}
                                    </div>
                                </div>
                                <div style={observationStatCardStyle}>
                                    <div style={observationStatLabelStyle}>
                                        {language === 'zh' ? '本次送出失敗' : 'Failed'}
                                    </div>
                                    <div style={{ ...observationStatValueStyle, color: observationBatchSummary.failureCount > 0 ? '#fbbf24' : 'var(--text-primary)' }}>
                                        {observationBatchSummary.failureCount ?? '--'}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                            type="button"
                            onClick={() => handleToggleAllObservationRows(true)}
                            disabled={observationImportableRows.length === 0}
                            style={{
                                padding: '8px 12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.04)',
                                color: 'var(--text-primary)',
                                cursor: observationImportableRows.length === 0 ? 'not-allowed' : 'pointer',
                                opacity: observationImportableRows.length === 0 ? 0.5 : 1,
                            }}
                        >
                            {language === 'zh' ? '全選可匯入項目' : 'Select importable'}
                        </button>
                        <button
                            type="button"
                            onClick={() => handleToggleAllObservationRows(false)}
                            disabled={selectedObservationRows.length === 0}
                            style={{
                                padding: '8px 12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.04)',
                                color: 'var(--text-primary)',
                                cursor: selectedObservationRows.length === 0 ? 'not-allowed' : 'pointer',
                                opacity: selectedObservationRows.length === 0 ? 0.5 : 1,
                            }}
                        >
                            {language === 'zh' ? '清除選取' : 'Clear selection'}
                        </button>
                        <button
                            type="button"
                            onClick={handleBatchObservationImport}
                            disabled={selectedObservationRows.length === 0 || observationBatchSummary?.status === 'loading'}
                            style={{
                                padding: '8px 14px',
                                borderRadius: '8px',
                                border: 'none',
                                background: 'var(--accent-primary)',
                                color: '#fff',
                                fontWeight: 600,
                                cursor: selectedObservationRows.length === 0 || observationBatchSummary?.status === 'loading' ? 'not-allowed' : 'pointer',
                                opacity: selectedObservationRows.length === 0 || observationBatchSummary?.status === 'loading' ? 0.5 : 1,
                            }}
                        >
                            {observationBatchSummary?.status === 'loading'
                                ? (language === 'zh' ? '批次匯入中...' : 'Batch importing...')
                                : (language === 'zh' ? '批次送出' : 'Batch send')}
                        </button>
                    </div>
                </div>
            ) : null}
        </>
    );
};

export default MetaAndromedaImportActions;
