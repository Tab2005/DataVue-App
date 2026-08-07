import React, { useMemo } from 'react';

// 評分（觀測匯入自動評分）到終態的三種歸類：完成 / 失敗（含被匯入失敗
// 連帶擋下）/ 略過（無素材可評）；其餘 pending_observation、
// queued_background、queued、processing、pending_score_event 或尚未有
// 任何狀態，都算「評估中」。與 useAnalyticsObservationImport.js 的
// TERMINAL_SCORE_STATUSES 對應，但這裡要拆開分類顯示，不能只判斷終態。
const FAILED_SCORE_STATUSES = new Set(['failed', 'blocked_by_observation_failure']);

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
    observationImportState,
    handleToggleAllObservationRows,
    handleBatchObservationImport,
}) => {
    // 「本次送出成功」只代表匯入請求本身被接受，實際 AI 評分是背景非同步
    // 進行、輪詢才會逐漸更新（docs/68 B1）。這裡從 observationImportState
    // 即時彙總這批 row 的評分終態分佈，讓使用者看得到「送出成功」之後
    // 究竟有幾筆真的評估完成、進了評估紀錄，而不是只看到匯入本身的成功/
    // 失敗數。隨 observationImportState 更新自動重新計算，不需要額外輪詢。
    const evaluationStats = useMemo(() => {
        const rowIds = observationBatchSummary?.rowIds;
        if (!rowIds || rowIds.length === 0) {
            return null;
        }
        let evaluatedCount = 0;
        let evaluationFailedCount = 0;
        let evaluationSkippedCount = 0;
        rowIds.forEach((rowId) => {
            const scoreStatus = observationImportState?.[rowId]?.scoreStatus;
            if (scoreStatus === 'completed') {
                evaluatedCount += 1;
            } else if (FAILED_SCORE_STATUSES.has(scoreStatus)) {
                evaluationFailedCount += 1;
            } else if (scoreStatus === 'skipped_no_asset') {
                evaluationSkippedCount += 1;
            }
        });
        const pendingCount = Math.max(
            0,
            rowIds.length - evaluatedCount - evaluationFailedCount - evaluationSkippedCount,
        );
        return { evaluatedCount, evaluationFailedCount, evaluationSkippedCount, pendingCount };
    }, [observationBatchSummary?.rowIds, observationImportState]);

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
                                gridTemplateColumns: evaluationStats
                                    ? 'repeat(4, minmax(90px, 1fr))'
                                    : 'repeat(3, minmax(90px, 1fr))',
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
                                {evaluationStats && (
                                    <div style={observationStatCardStyle}>
                                        <div style={observationStatLabelStyle}>
                                            {language === 'zh' ? '評估完成（進評估紀錄）' : 'Evaluated'}
                                        </div>
                                        <div style={{
                                            ...observationStatValueStyle,
                                            color: evaluationStats.evaluatedCount === (observationBatchSummary.successCount || 0) && evaluationStats.evaluatedCount > 0
                                                ? '#34d399'
                                                : 'var(--text-primary)',
                                        }}>
                                            {`${evaluationStats.evaluatedCount} / ${observationBatchSummary.successCount ?? 0}`}
                                        </div>
                                        {(evaluationStats.pendingCount > 0 || evaluationStats.evaluationFailedCount > 0 || evaluationStats.evaluationSkippedCount > 0) && (
                                            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                                {[
                                                    evaluationStats.pendingCount > 0
                                                        ? (language === 'zh' ? `評估中 ${evaluationStats.pendingCount}` : `${evaluationStats.pendingCount} pending`)
                                                        : null,
                                                    evaluationStats.evaluationFailedCount > 0
                                                        ? (language === 'zh' ? `失敗 ${evaluationStats.evaluationFailedCount}` : `${evaluationStats.evaluationFailedCount} failed`)
                                                        : null,
                                                    evaluationStats.evaluationSkippedCount > 0
                                                        ? (language === 'zh' ? `略過 ${evaluationStats.evaluationSkippedCount}` : `${evaluationStats.evaluationSkippedCount} skipped`)
                                                        : null,
                                                ].filter(Boolean).join(' · ')}
                                            </div>
                                        )}
                                    </div>
                                )}
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
