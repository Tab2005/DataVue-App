import React from 'react';
import { COMPARE_OPTIONS, DATE_PRESETS } from './constants';
import { formatDate, getDateRangeFromPreset } from './gscUtils';

const GSCSettingsPanel = ({ context }) => {
    const {
        compareMode,
        datePreset,
        dateRange,
        getCompareDateRange,
        getDaysInRange,
        handleCustomDateChange,
        handlePresetChange,
        handleRunAnalysis,
        isMobile,
        language,
        selectedSite,
        setCompareMode,
        setDateRange,
        setSelectedSite,
        setShowCustomDate,
        showCustomDate,
        sites,
        t
    } = context;

    return (
            <div className="glass-panel" style={{
                padding: isMobile ? '16px' : '24px',
                borderRadius: '16px',
                marginBottom: '24px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(10px)'
            }}>
                <h3 style={{
                    margin: '0 0 20px 0',
                    fontSize: '0.95rem',
                    color: 'var(--text-secondary)',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    ⚙️ {t('主要設定', 'Main Settings')}
                </h3>

                {/* Row 1: Site Selector + Date Range */}
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '20px',
                    flexWrap: 'wrap'
                }}>
                    {/* Site Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('選擇資源', 'Select Property')}
                        </label>
                        <select
                            value={selectedSite}
                            onChange={(e) => setSelectedSite(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {sites.map(site => (
                                <option key={site.siteUrl} value={site.siteUrl} style={{ color: 'black' }}>
                                    {site.siteUrl} ({site.permissionLevel})
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Date Range Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('日期範圍', 'Date Range')}
                        </label>
                        <select
                            value={datePreset}
                            onChange={(e) => handlePresetChange(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {DATE_PRESETS.map(preset => (
                                <option key={preset.key} value={preset.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? preset.label_zh : preset.label_en}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Compare Mode Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '150px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            📊 {t('比較模式', 'Compare Mode')}
                        </label>
                        <select
                            value={compareMode}
                            onChange={(e) => setCompareMode(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {COMPARE_OPTIONS.map(opt => (
                                <option key={opt.key} value={opt.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? opt.label_zh : opt.label_en}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Date Range Info Bar - Always visible (aligned with GA4) */}
                <div style={{
                    marginTop: '16px',
                    padding: '12px 16px',
                    background: compareMode !== 'none' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(66, 133, 244, 0.1)',
                    borderRadius: '8px',
                    border: `1px solid ${compareMode !== 'none' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(66, 133, 244, 0.2)'}`,
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    flexWrap: 'wrap'
                }}>
                    {/* Current Period */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        📆 {t('目前期間', 'Current Period')}:
                        <strong style={{ color: 'var(--text-primary)' }}>
                            {dateRange.start} ~ {dateRange.end}
                        </strong>
                        <span style={{ opacity: 0.7 }}>
                            ({getDaysInRange()} {t('天', 'days')})
                        </span>
                    </div>

                    {/* Compare Period - Only when enabled */}
                    {compareMode !== 'none' && getCompareDateRange() && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>|</span>
                            📊 {compareMode === 'previous_period' ? t('前一時段', 'Previous Period') : t('去年同期', 'Previous Year')}:
                            <strong style={{ color: '#a78bfa' }}>
                                {getCompareDateRange().start} ~ {getCompareDateRange().end}
                            </strong>
                        </div>
                    )}
                </div>


                {/* Custom Date Picker - Inline when selected */}
                {showCustomDate && (
                    <div style={{
                        marginTop: '20px',
                        paddingTop: '20px',
                        borderTop: '1px solid var(--glass-border)'
                    }}>
                        <div style={{
                            display: 'flex',
                            flexDirection: isMobile ? 'column' : 'row',
                            gap: '16px',
                            alignItems: isMobile ? 'stretch' : 'flex-end'
                        }}>
                            {/* Start Date */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.85rem'
                                }}>
                                    {t('開始日期', 'Start Date')}
                                </label>
                                <input
                                    type="date"
                                    value={dateRange.start}
                                    max={dateRange.end}
                                    onChange={(e) => handleCustomDateChange('start', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-primary)',
                                        fontSize: '14px',
                                        colorScheme: 'dark'
                                    }}
                                />
                            </div>

                            {/* End Date */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.85rem'
                                }}>
                                    {t('結束日期', 'End Date')}
                                </label>
                                <input
                                    type="date"
                                    value={dateRange.end}
                                    min={dateRange.start}
                                    max={formatDate(new Date())}
                                    onChange={(e) => handleCustomDateChange('end', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-primary)',
                                        fontSize: '14px',
                                        colorScheme: 'dark'
                                    }}
                                />
                            </div>
                        </div>

                        {/* Quick Selection Buttons */}
                        <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '8px',
                            marginTop: '16px',
                            alignItems: 'center'
                        }}>
                            <span style={{
                                fontSize: '13px',
                                color: 'var(--text-secondary)',
                                marginRight: '8px'
                            }}>
                                {t('快速選擇：', 'Quick select:')}
                            </span>
                            {[
                                { label: t('今天', 'Today'), key: 'today' },
                                { label: t('昨天', 'Yesterday'), key: 'yesterday' },
                                { label: t('本週', 'This Week'), key: 'this_week' },
                                { label: t('上週', 'Last Week'), key: 'last_week' },
                                { label: t('本月', 'This Month'), key: 'this_month' },
                                { label: t('上月', 'Last Month'), key: 'last_month' }
                            ].map(quick => (
                                <button
                                    key={quick.key}
                                    onClick={() => {
                                        const range = getDateRangeFromPreset(quick.key);
                                        setDateRange(range);
                                    }}
                                    style={{
                                        padding: '6px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '16px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-secondary)',
                                        fontSize: '12px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseOver={(e) => {
                                        e.target.style.background = 'var(--accent-primary)';
                                        e.target.style.color = 'white';
                                    }}
                                    onMouseOut={(e) => {
                                        e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                                        e.target.style.color = 'var(--text-secondary)';
                                    }}
                                >
                                    {quick.label}
                                </button>
                            ))}

                            {/* New Control Buttons */}
                            <div style={{ display: 'flex', gap: '8px', marginLeft: isMobile ? '0' : 'auto', width: isMobile ? '100%' : 'auto', marginTop: isMobile ? '8px' : '0' }}>
                                <button
                                    onClick={handleRunAnalysis}
                                    style={{
                                        padding: '6px 16px',
                                        background: 'var(--accent-primary)',
                                        color: 'white',
                                        borderRadius: '8px',
                                        border: 'none',
                                        fontSize: '13px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px'
                                    }}
                                >
                                    🚀 {t('開始分析', 'Start Analysis')}
                                </button>
                                <button
                                    onClick={() => setShowCustomDate(false)}
                                    style={{
                                        padding: '6px 16px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-secondary)',
                                        borderRadius: '8px',
                                        border: '1px solid var(--glass-border)',
                                        fontSize: '13px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    {t('完成並收合', 'Finish & Collapse')}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
    );
};

export default GSCSettingsPanel;
