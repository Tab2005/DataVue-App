import React from 'react';
import { DATE_PRESETS, COMPARE_OPTIONS } from './constants';
import { formatLocalDate } from './ga4Formatters';

const GA4SettingsPanel = ({
    compareMode,
    dateRange,
    fetchAnalytics,
    getCompareDateRange,
    handleCustomDateChange,
    handleDatePresetChange,
    isMobile,
    language,
    loading,
    properties,
    propertiesLoading,
    selectedProperty,
    setCompareMode,
    setDateRange,
    setSelectedProperty,
    t
}) => (
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

                {/* Row 1: Account + Date Range + Compare Mode */}
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '20px',
                    flexWrap: 'wrap'
                }}>
                    {/* Account Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('選擇帳號', 'Select Account')}
                        </label>
                        {propertiesLoading && (
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                marginBottom: '8px',
                                color: 'var(--text-secondary)',
                                fontSize: '12px'
                            }}>
                                <div style={{
                                    width: '14px',
                                    height: '14px',
                                    border: '2px solid rgba(52, 168, 83, 0.2)',
                                    borderTop: '2px solid #34a853',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }} />
                                {t('載入 GA4 帳號列表中...', 'Loading GA4 properties...')}
                                <style>{`
                                    @keyframes spin {
                                        0% { transform: rotate(0deg); }
                                        100% { transform: rotate(360deg); }
                                    }
                                `}</style>
                            </div>
                        )}
                        <select
                            value={selectedProperty}
                            onChange={(e) => setSelectedProperty(e.target.value)}
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
                            <option value="" style={{ color: 'black' }}>{t('選擇 GA4 帳號...', 'Select GA4 Account...')}</option>
                            {properties.map(prop => (
                                <option key={prop.property_id} value={prop.property_id} style={{ color: 'black' }}>
                                    {prop.display_name || prop.property_id}
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
                            value={dateRange.preset}
                            onChange={(e) => handleDatePresetChange(e.target.value)}
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
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
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

                    {/* Refresh Button */}
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button
                            onClick={() => fetchAnalytics(true)}
                            disabled={loading || !selectedProperty}
                            style={{
                                padding: '10px 20px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px',
                                cursor: loading || !selectedProperty ? 'not-allowed' : 'pointer',
                                opacity: loading || !selectedProperty ? 0.5 : 1,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                transition: 'all 0.2s'
                            }}
                            title={t('強制重新整理（忽略快取）', 'Force refresh (ignore cache)')}
                        >
                            🔄 {t('重新整理', 'Refresh')}
                        </button>
                    </div>
                </div>

                {/* Custom Date Picker - Inline when selected */}
                {dateRange.preset === 'custom' && (
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
                                    value={dateRange.startDate}
                                    max={dateRange.endDate}
                                    onChange={(e) => handleCustomDateChange('startDate', e.target.value)}
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
                                    value={dateRange.endDate}
                                    min={dateRange.startDate}
                                    max={formatLocalDate(new Date())}
                                    onChange={(e) => handleCustomDateChange('endDate', e.target.value)}
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

                        {/* Quick Selection + Range Display */}
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
                                { label: t('今天', 'Today'), type: 'today' },
                                { label: t('昨天', 'Yesterday'), type: 'yesterday' },
                                { label: t('本週', 'This Week'), type: 'thisWeek' },
                                { label: t('上週', 'Last Week'), type: 'lastWeek' },
                                { label: t('本月', 'This Month'), type: 'thisMonth' },
                                { label: t('上月', 'Last Month'), type: 'lastMonth' }
                            ].map(quick => (
                                <button
                                    key={quick.label}
                                    onClick={() => {
                                        const today = new Date();
                                        let start, end;

                                        switch (quick.type) {
                                            case 'today':
                                                start = end = new Date(today);
                                                break;
                                            case 'yesterday':
                                                start = end = new Date(today);
                                                start.setDate(start.getDate() - 1);
                                                break;
                                            case 'thisWeek': {
                                                // 本週：從本週一到今天
                                                end = new Date(today);
                                                start = new Date(today);
                                                const dayOfWeek = start.getDay();
                                                const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
                                                start.setDate(start.getDate() - daysToMonday);
                                                break;
                                            }
                                            case 'lastWeek': {
                                                // 上週：從上週一到上週日
                                                const lastWeekEnd = new Date(today);
                                                const dow = lastWeekEnd.getDay();
                                                const daysToLastSunday = dow === 0 ? 7 : dow;
                                                lastWeekEnd.setDate(lastWeekEnd.getDate() - daysToLastSunday);
                                                end = new Date(lastWeekEnd);
                                                start = new Date(lastWeekEnd);
                                                start.setDate(start.getDate() - 6);
                                                break;
                                            }
                                            case 'thisMonth': {
                                                // 本月：從本月1日到本月最後一天（GA4 不接受未來日期，需封頂到今天）
                                                const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                                                end = monthEnd > today ? new Date(today) : monthEnd;
                                                start = new Date(today.getFullYear(), today.getMonth(), 1);
                                                break;
                                            }
                                            case 'lastMonth':
                                                // 上月：從上月1日到上月最後一天
                                                start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                                                end = new Date(today.getFullYear(), today.getMonth(), 0);
                                                break;
                                            default:
                                                start = end = new Date(today);
                                        }

                                        setDateRange({
                                            startDate: formatLocalDate(start),
                                            endDate: formatLocalDate(end),
                                            preset: 'custom'
                                        });
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


                            {/* Selected Range Display */}
                            <div style={{
                                marginLeft: 'auto',
                                padding: '6px 12px',
                                background: 'rgba(66, 133, 244, 0.1)',
                                borderRadius: '6px',
                                fontSize: '13px',
                                color: 'var(--text-secondary)'
                            }}>
                                📆 {dateRange.startDate} ~ {dateRange.endDate}
                                <span style={{ marginLeft: '8px', opacity: 0.8 }}>
                                    ({Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24)) + 1} {t('天', 'days')})
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Date Range Info Bar - Always visible */}
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
                            {dateRange.startDate} ~ {dateRange.endDate}
                        </strong>
                        <span style={{ opacity: 0.7 }}>
                            ({Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24)) + 1} {t('天', 'days')})
                        </span>
                    </div>

                    {/* Compare Period - Only when enabled */}
                    {compareMode !== 'none' && getCompareDateRange() && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>|</span>
                            📊 {compareMode === 'previous_period' ? t('前一時段', 'Previous Period') : t('去年同期', 'Previous Year')}:
                            <strong style={{ color: '#a78bfa' }}>
                                {getCompareDateRange().startDate} ~ {getCompareDateRange().endDate}
                            </strong>
                        </div>
                    )}
                </div>

            </div>
);

export default GA4SettingsPanel;
