import React from 'react';

const AnalyticsDataTable = ({
    loading,
    error,
    isMobile,
    isSidebarCollapsed,
    isCompareMode,
    filteredData,
    selectedRowIds,
    setSelectedRowIds,
    txt,
    level,
    activeCols,
    handleSort,
    sortConfig,
    language,
    dateRange,
    prevDateRange,
    canUseObservationImport,
    sortedData,
    prevReportData,
    renderMetricValue,
    selectedObservationIds,
    handleToggleObservationRow,
    handleObservationImport,
    observationImportState,
    observationWindowKind,
    getObservationStatusText,
    getScoreStatusText,
}) => {
    return (
        <>
            {/* Data Table */}
            {
                loading ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>載入數據中...</div>
                ) : error ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#f87171' }}>{error}</div>
                ) : (
                    <div className="glass-panel" style={{
                        padding: '0',
                        borderRadius: '16px',
                        overflowX: 'auto',
                        maxHeight: '600px',
                        overflowY: 'auto',
                        // Dynamic Width: 
                        // Mobile: Full width minus padding (32px)
                        // Desktop: Viewport minus Sidebar (240/80) - Padding (60)
                        maxWidth: isMobile
                            ? 'calc(100vw - 32px)'
                            : (isSidebarCollapsed ? 'calc(100vw - 140px)' : 'calc(100vw - 300px)'),
                        width: '100%',
                        display: 'block',
                        transition: 'max-width 0.3s ease'
                    }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                            <thead>
                                {/* Comparison Mode Header */}
                                {isCompareMode ? (
                                    <>
                                        {/* Row 1: Metric Names */}
                                        <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'center' }}>
                                            <th rowSpan={2} style={{
                                                padding: '12px',
                                                minWidth: '200px',
                                                position: 'sticky',
                                                top: 0,
                                                left: 0,
                                                zIndex: 50,
                                                background: '#242526',
                                                textAlign: 'left',
                                                borderRight: '1px solid var(--glass-border)'
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <input
                                                        type="checkbox"
                                                        checked={filteredData.length > 0 && selectedRowIds.size === filteredData.length}
                                                        onChange={(e) => {
                                                            if (e.target.checked) {
                                                                setSelectedRowIds(new Set(filteredData.map(d => d.id)));
                                                            } else {
                                                                setSelectedRowIds(new Set());
                                                            }
                                                        }}
                                                        style={{ cursor: 'pointer' }}
                                                    />
                                                    {txt.table.headers[level] || txt.table.name}
                                                </div>
                                            </th>
                                            {activeCols.map(col => (
                                                <th
                                                    key={col.uniqueKey}
                                                    colSpan={4}
                                                    onClick={() => handleSort(col.key)}
                                                    style={{
                                                        padding: '8px',
                                                        borderLeft: '1px solid var(--glass-border)',
                                                        background: '#242526', // Use solid bg for headers
                                                        position: 'sticky',
                                                        top: 0,
                                                        zIndex: 40,
                                                        cursor: 'pointer',
                                                        userSelect: 'none',
                                                        color: sortConfig.key === col.key ? 'var(--accent-primary)' : 'inherit'
                                                    }}
                                                >
                                                    {language === 'zh' ? col.label_zh : col.label_en}
                                                    {sortConfig.key === col.key && (
                                                        <span style={{ marginLeft: '4px' }}>
                                                            {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                                        </span>
                                                    )}
                                                </th>
                                            ))}
                                            {canUseObservationImport && (
                                                <th rowSpan={2} style={{
                                                    padding: '12px',
                                                    minWidth: '150px',
                                                    position: 'sticky',
                                                    top: 0,
                                                    zIndex: 40,
                                                    background: '#242526',
                                                    textAlign: 'left',
                                                    borderLeft: '1px solid var(--glass-border)'
                                                }}>
                                                    {language === 'zh' ? '操作' : 'Actions'}
                                                </th>
                                            )}
                                        </tr>
                                        {/* Row 2: Sub-columns */}
                                        <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                            {activeCols.map(col => (
                                                <React.Fragment key={col.uniqueKey}>
                                                    <th style={{ padding: '8px', minWidth: '90px', background: '#242526', borderLeft: '1px solid var(--glass-border)', position: 'sticky', top: '38px', zIndex: 39 }}>
                                                        {dateRange.since}<br />~ {dateRange.until?.slice(5)}
                                                    </th>
                                                    <th style={{ padding: '8px', minWidth: '90px', background: '#242526', position: 'sticky', top: '38px', zIndex: 39 }}>
                                                        {prevDateRange.since}<br />~ {prevDateRange.until?.slice(5)}
                                                    </th>
                                                    <th style={{ padding: '8px', minWidth: '80px', background: '#242526', position: 'sticky', top: '38px', zIndex: 39 }}>
                                                        {language === 'zh' ? '變化' : 'Change'}
                                                    </th>
                                                    <th style={{ padding: '8px', minWidth: '80px', background: '#242526', position: 'sticky', top: '38px', zIndex: 39 }}>
                                                        {language === 'zh' ? '變化 (%)' : 'Change (%)'}
                                                    </th>
                                                </React.Fragment>
                                            ))}
                                        </tr>
                                    </>
                                ) : (
                                    /* Standard Header */
                                    <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left' }}>
                                        <th style={{
                                            padding: '12px',
                                            minWidth: '200px',
                                            position: 'sticky',
                                            top: 0,
                                            left: 0,
                                            zIndex: 50,
                                            background: '#242526'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={filteredData.length > 0 && selectedRowIds.size === filteredData.length}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSelectedRowIds(new Set(filteredData.map(d => d.id)));
                                                        } else {
                                                            setSelectedRowIds(new Set());
                                                        }
                                                    }}
                                                    style={{ cursor: 'pointer' }}
                                                />
                                                {txt.table.headers[level] || txt.table.name}
                                            </div>
                                        </th>
                                        {activeCols.map(col => (
                                            <th
                                                key={col.uniqueKey}
                                                onClick={() => handleSort(col.key)}
                                                style={{
                                                    padding: '8px',
                                                    minWidth: '100px',
                                                    position: 'sticky',
                                                    top: 0,
                                                    zIndex: 40,
                                                    background: '#242526',
                                                    cursor: 'pointer',
                                                    userSelect: 'none',
                                                    color: sortConfig.key === col.key ? 'var(--accent-primary)' : 'inherit'
                                                }}
                                            >
                                                {language === 'zh' ? col.label_zh : col.label_en}
                                                {sortConfig.key === col.key && (
                                                    <span style={{ marginLeft: '4px' }}>
                                                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                                    </span>
                                                )}
                                            </th>
                                        ))}
                                        {canUseObservationImport && (
                                            <th style={{
                                                padding: '12px',
                                                minWidth: '150px',
                                                position: 'sticky',
                                                top: 0,
                                                zIndex: 40,
                                                background: '#242526',
                                                borderLeft: '1px solid var(--glass-border)',
                                                textAlign: 'left'
                                            }}>
                                                {language === 'zh' ? '操作' : 'Actions'}
                                            </th>
                                        )}
                                    </tr>
                                )}
                            </thead>
                            <tbody>
                                {sortedData && sortedData.map((row, idx) => (
                                    <tr key={idx} style={{
                                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                                        background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                    }}>
                                        {/* Name Column with Thumbnail */}
                                        <td style={{
                                            padding: '12px',
                                            position: 'sticky',
                                            left: 0,
                                            zIndex: 30,
                                            background: '#242526',
                                            borderRight: '1px solid var(--glass-border)',
                                            minWidth: '200px',
                                            maxWidth: '200px'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                                                {/* Row Selection Checkbox */}
                                                <div style={{ marginTop: '2px', flexShrink: 0 }}>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedRowIds.has(row.id)}
                                                        onChange={(e) => {
                                                            const newSet = new Set(selectedRowIds);
                                                            if (e.target.checked) {
                                                                newSet.add(row.id);
                                                            } else {
                                                                newSet.delete(row.id);
                                                            }
                                                            setSelectedRowIds(newSet);
                                                        }}
                                                        style={{ cursor: 'pointer' }}
                                                    />
                                                </div>

                                                {/* Thumbnail & Preview */}
                                                {row.image_url && (
                                                    <div
                                                        style={{ position: 'relative', flexShrink: 0, marginTop: '2px' }}
                                                        onMouseEnter={(e) => {
                                                            const rect = e.currentTarget.getBoundingClientRect();
                                                            document.getElementById('preview-img-container').style.display = 'block';
                                                            document.getElementById('preview-img').src = row.image_url;
                                                            document.getElementById('preview-img-container').style.top = `${rect.top}px`;
                                                            document.getElementById('preview-img-container').style.left = `${rect.right + 10}px`;
                                                        }}
                                                        onMouseLeave={() => {
                                                            document.getElementById('preview-img-container').style.display = 'none';
                                                        }}
                                                    >
                                                        <img
                                                            src={row.image_url}
                                                            alt="Ad"
                                                            style={{
                                                                width: '40px',
                                                                height: '40px',
                                                                objectFit: 'cover',
                                                                borderRadius: '4px',
                                                                cursor: 'zoom-in',
                                                                border: '1px solid var(--glass-border)'
                                                            }}
                                                        />
                                                    </div>
                                                )}

                                                <div style={{
                                                    display: '-webkit-box',
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: 'vertical',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'normal',
                                                    lineHeight: '1.4',
                                                    wordBreak: 'break-word'
                                                }} title={row.name}>
                                                    {row.name}
                                                </div>
                                            </div>
                                        </td>

                                        {/* Data Columns */}
                                        {activeCols.map(col => {
                                            const currentVal = row[col.key];

                                            // Formatting Helper
                                            const formatVal = (v, format) => {
                                                if (v === undefined || v === null) return '-';
                                                if (format === 'percent') return `${v.toFixed(2)}%`;
                                                if (format === 'currency') return `$${v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                                                if (format === 'currency_decimal') {
                                                    // Smart decimal: show .X only if not a whole number
                                                    const isWholeNumber = Number.isInteger(v) || Math.abs(v - Math.round(v)) < 0.01;
                                                    return `$${v.toLocaleString(undefined, { minimumFractionDigits: isWholeNumber ? 0 : 1, maximumFractionDigits: isWholeNumber ? 0 : 1 })}`;
                                                }
                                                if (format === 'decimal') return v.toFixed(2);
                                                return v.toLocaleString();
                                            };

                                            if (isCompareMode && prevReportData) {
                                                // Comparison Logic
                                                let prevVal = 0;
                                                let diff = 0;
                                                let percentStr = '-';
                                                let diffColor = 'inherit';

                                                const idField = level === 'account' ? (row.date_start ? 'date_start' : 'index') : `${level}_id`;

                                                // Matching Logic
                                                let prevRow;
                                                if (level === 'account') {
                                                    // If 'account' overview (single row), assume index 0 match
                                                    if (!row.date_start) prevRow = prevReportData[0];
                                                    // If daily breakdown, match by date_start (TODO: verify this if breakdown used)
                                                } else {
                                                    prevRow = prevReportData.find(p => p[idField] === row[idField]);
                                                }

                                                if (prevRow) {
                                                    prevVal = prevRow[col.key] || 0;
                                                    diff = (currentVal || 0) - prevVal;

                                                    if (prevVal !== 0) {
                                                        const p = (diff / prevVal) * 100;
                                                        percentStr = `${p >= 0 ? '▲' : '▼'} ${Math.abs(p).toFixed(2)}%`;
                                                    } else if (currentVal !== 0) {
                                                        percentStr = '▲ 100%';
                                                    }

                                                    // Color
                                                    if (diff !== 0) {
                                                        const isIncrease = diff >= 0;
                                                        if (col.isInverse) {
                                                            diffColor = isIncrease ? '#fb7185' : '#4ade80';
                                                        } else {
                                                            diffColor = isIncrease ? '#4ade80' : '#fb7185';
                                                        }
                                                    }
                                                } else {
                                                    // No Prev Data found for this ID
                                                    diff = currentVal;
                                                    percentStr = '-'; // Don't show confusing 100% if likely data mismatch
                                                }

                                                return (
                                                    <React.Fragment key={col.uniqueKey}>
                                                        <td style={{ padding: '8px', textAlign: 'right', borderLeft: '1px solid var(--glass-border)' }}>{formatVal(currentVal, col.format)}</td>
                                                        <td style={{ padding: '8px', textAlign: 'right', color: 'var(--text-secondary)' }}>{prevRow ? formatVal(prevVal, col.format) : '-'}</td>
                                                        <td style={{ padding: '8px', textAlign: 'right' }}>{formatVal(diff, col.format)}</td>
                                                        <td style={{ padding: '8px', textAlign: 'right', color: diffColor, fontWeight: 500 }}>{percentStr}</td>
                                                    </React.Fragment>
                                                );

                                            } else {
                                                // Standard Mode
                                                return (
                                                    <td key={col.uniqueKey} style={{ padding: '8px' }}>{formatVal(currentVal, col.format)}</td>
                                                );
                                            }
                                        })}
                                        {canUseObservationImport && (
                                            <td style={{
                                                padding: '12px',
                                                borderLeft: '1px solid rgba(255,255,255,0.05)',
                                                verticalAlign: 'top',
                                                minWidth: '150px'
                                            }}>
                                                {row.ad_id ? (
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                        <div style={{
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '8px',
                                                            flexWrap: 'wrap'
                                                        }}>
                                                            <label style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '6px',
                                                                fontSize: '0.78rem',
                                                                color: 'var(--text-secondary)',
                                                                cursor: 'pointer',
                                                                whiteSpace: 'nowrap'
                                                            }}>
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedObservationIds.has(row.id)}
                                                                onChange={(e) => handleToggleObservationRow(row.id, e.target.checked)}
                                                                style={{ cursor: 'pointer' }}
                                                            />
                                                                {language === 'zh' ? '批次' : 'Batch'}
                                                            </label>
                                                            <button
                                                                type="button"
                                                                onClick={() => handleObservationImport(row)}
                                                                disabled={['loading', 'accepted', 'polling'].includes(observationImportState[row.id]?.status)}
                                                                title={
                                                                    observationWindowKind === 'custom'
                                                                        ? (language === 'zh'
                                                                            ? '目前日期區段會以自訂時間區間匯入 observation。'
                                                                            : 'Current date preset will import observation as custom range.')
                                                                        : undefined
                                                                }
                                                                style={{
                                                                    display: 'inline-flex',
                                                                    alignItems: 'center',
                                                                    justifyContent: 'center',
                                                                    padding: '6px 10px',
                                                                    borderRadius: '8px',
                                                                    border: '1px solid var(--glass-border)',
                                                                    background: 'rgba(255,255,255,0.04)',
                                                                    color: 'var(--accent-primary)',
                                                                    fontSize: '0.78rem',
                                                                    fontWeight: 600,
                                                                    cursor: ['loading', 'accepted', 'polling'].includes(observationImportState[row.id]?.status) ? 'wait' : 'pointer',
                                                                    whiteSpace: 'nowrap'
                                                                }}
                                                            >
                                                                {['loading', 'accepted', 'polling'].includes(observationImportState[row.id]?.status)
                                                                    ? (language === 'zh' ? '處理中' : 'Processing')
                                                                    : (language === 'zh' ? '送出' : 'Send')}
                                                            </button>
                                                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                                                                <div style={{
                                                                    display: 'inline-flex',
                                                                    alignItems: 'center',
                                                                    width: 'fit-content',
                                                                    maxWidth: '100%',
                                                                    padding: '4px 8px',
                                                                    borderRadius: '999px',
                                                                    fontSize: '0.72rem',
                                                                    fontWeight: 600,
                                                                    background: observationImportState[row.id]?.observationStatus === 'completed'
                                                                        ? 'rgba(52, 211, 153, 0.12)'
                                                                        : observationImportState[row.id]?.observationStatus === 'failed'
                                                                            ? 'rgba(248, 113, 113, 0.12)'
                                                                            : 'rgba(96, 165, 250, 0.12)',
                                                                    color: observationImportState[row.id]?.observationStatus === 'completed'
                                                                        ? '#34d399'
                                                                        : observationImportState[row.id]?.observationStatus === 'failed'
                                                                            ? '#f87171'
                                                                            : '#60a5fa',
                                                                    whiteSpace: 'nowrap'
                                                                }}>
                                                                    {`Obs: ${getObservationStatusText(observationImportState[row.id]?.observationStatus)}`}
                                                                </div>
                                                                <div style={{
                                                                    display: 'inline-flex',
                                                                    alignItems: 'center',
                                                                    width: 'fit-content',
                                                                    maxWidth: '100%',
                                                                    padding: '4px 8px',
                                                                    borderRadius: '999px',
                                                                    fontSize: '0.72rem',
                                                                    fontWeight: 600,
                                                                    background: observationImportState[row.id]?.scoreStatus === 'completed'
                                                                        ? 'rgba(52, 211, 153, 0.12)'
                                                                        : ['failed', 'blocked_by_observation_failure'].includes(observationImportState[row.id]?.scoreStatus)
                                                                            ? 'rgba(248, 113, 113, 0.12)'
                                                                            : 'rgba(255,255,255,0.06)',
                                                                    color: observationImportState[row.id]?.scoreStatus === 'completed'
                                                                        ? '#34d399'
                                                                        : ['failed', 'blocked_by_observation_failure'].includes(observationImportState[row.id]?.scoreStatus)
                                                                            ? '#f87171'
                                                                            : 'var(--text-secondary)',
                                                                    whiteSpace: 'nowrap'
                                                                }}>
                                                                    {`Score: ${getScoreStatusText(observationImportState[row.id]?.scoreStatus)}`}
                                                                </div>
                                                            </div>
                                                        </div>
                                                        {observationImportState[row.id]?.message && (
                                                            <div style={{
                                                                fontSize: '0.75rem',
                                                                color: 'var(--text-secondary)',
                                                                lineHeight: 1.4,
                                                                wordBreak: 'break-word',
                                                            }}>
                                                                {observationImportState[row.id].message}
                                                            </div>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
                                                        {language === 'zh' ? '缺少 ad_id，無法匯入。' : 'Unavailable without ad_id.'}
                                                    </div>
                                                )}
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )
            }

            {/* Hover Preview Container (Fixed Position) */}
            <div
                id="preview-img-container"
                style={{
                    display: 'none',
                    position: 'fixed',
                    zIndex: 9999,
                    background: '#242526',
                    padding: '8px',
                    borderRadius: '8px',
                    border: '1px solid var(--glass-border)',
                    boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
                    pointerEvents: 'none' // Let mouse pass through so it doesn't flicker
                }}
            >
                <img id="preview-img" src="" alt="Preview" style={{ maxWidth: '300px', maxHeight: '300px', borderRadius: '4px' }} />
            </div>
        </>
    );
};

export default AnalyticsDataTable;
