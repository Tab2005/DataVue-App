import React from 'react';
import { FiChevronUp, FiFileText, FiUsers, FiUser } from 'react-icons/fi';

import { DATE_PRESETS, COMPARE_PRESETS, VIEW_PRESETS } from '../../constants/analyticsConfig';
import { ALL_METRIC_GROUPS } from './analyticsMetrics';

const AnalyticsFiltersPanel = ({
    activeView,
    compareDateRange,
    comparePreset,
    datePreset,
    dateRange,
    fetchAnalytics,
    filterActiveOnly,
    filterKeyword,
    filterMode,
    filterObservationImported,
    handleComparePresetChange,
    handlePresetChange,
    handleViewChange,
    isCompareMode,
    isMobile,
    language,
    level,
    reportData,
    savedViews,
    selectedMetrics,
    setActiveView,
    setCompareDateRange,
    setDateRange,
    setFilterActiveOnly,
    setFilterKeyword,
    setFilterMode,
    setFilterObservationImported,
    setIsCompareMode,
    setLevel,
    setSelectedMetrics,
    setShowAiPanel,
    setShowMetricPanel,
    setShowReportModal,
    showMetricPanel,
    toggleMetric,
    txt,
}) => (
    <>
            {/* Split Layout Control Panel (Top) */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '3fr 1fr',
                gap: '24px',
                marginBottom: '24px'
            }}>

                {/* Left Panel: Primary Settings */}
                <div className="glass-panel" style={{ padding: isMobile ? '16px' : '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

                    <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{txt.mainSettings}</h3>

                    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: '20px', flexWrap: 'wrap' }}>
                        {/* Level Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.level}</label>
                            <select
                                value={level}
                                onChange={(e) => setLevel(e.target.value)}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'var(--text-primary)',
                                    width: '100%'
                                }}
                            >
                                <option value="campaign" style={{ color: 'black' }}>{txt.levels.campaign}</option>
                                <option value="adset" style={{ color: 'black' }}>{txt.levels.adset}</option>
                                <option value="ad" style={{ color: 'black' }}>{txt.levels.ad}</option>
                                <option value="account" style={{ color: 'black' }}>{txt.levels.account}</option>
                            </select>
                        </div>

                        {/* Date Preset Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.dateRange}</label>
                            <select
                                value={datePreset}
                                onChange={handlePresetChange}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'var(--text-primary)',
                                    width: '100%'
                                }}
                            >
                                {DATE_PRESETS.map(p => (
                                    <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                        {txt.presets[p.value] || p.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Custom Date Inputs (Conditional) */}
                    {datePreset === 'custom' && (
                        <div style={{ display: 'flex', gap: '16px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customStart}</label>
                                <input type="date" value={dateRange.since} onChange={(e) => setDateRange({ ...dateRange, since: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customEnd}</label>
                                <input type="date" value={dateRange.until} onChange={(e) => setDateRange({ ...dateRange, until: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                        </div>
                    )}


                    {/* Metric Selector Toggle (Now includes ALL groups) */}
                    <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '16px' }}>

                        {/* View Tabs */}
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                            {Object.entries(VIEW_PRESETS).map(([key, preset]) => (
                                <button
                                    key={key}
                                    onClick={() => handleViewChange(key)}
                                    style={{
                                        padding: '6px 12px',
                                        borderRadius: '20px',
                                        border: '1px solid var(--glass-border)',
                                        background: activeView === key ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)',
                                        color: 'white',
                                        fontSize: '0.85rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {language === 'zh' ? preset.label_zh : preset.label_en}
                                </button>
                            ))}

                            {/* AI Analyst Button - Placed right after Custom tab */}
                            <button
                                onClick={() => setShowAiPanel(true)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: '6px',
                                    padding: '6px 16px', borderRadius: '20px',
                                    background: 'linear-gradient(135deg, #6366f1, #a855f7)', // Indigo to Purple
                                    border: 'none', color: 'white',
                                    fontSize: '0.9rem', fontWeight: 'bold', cursor: 'pointer',
                                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
                                    transition: 'transform 0.2s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                                onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                            >
                                🤖 {language === 'zh' ? 'AI 廣告分析' : 'AI Analyst'}
                            </button>

                            {/* Saved Views from MetricsLab */}
                            {savedViews.length > 0 && (
                                <>
                                    <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)', margin: '0 4px' }} />
                                    {savedViews.map(view => (
                                        <button
                                            key={`saved-${view.id}`}
                                            onClick={() => {
                                                // Load saved view metrics
                                                const newSet = new Set();
                                                view.metrics.forEach(metricKey => {
                                                    // Map registry keys to composite keys (search in ALL groups including extended)
                                                    for (const group of ALL_METRIC_GROUPS) {
                                                        const match = group.metrics.find(m => m.key === metricKey);
                                                        if (match) {
                                                            newSet.add(`${group.id}:${metricKey}`);
                                                            break;
                                                        }
                                                    }
                                                });
                                                setSelectedMetrics(newSet);
                                                setActiveView(`saved-${view.id}`);
                                                setShowMetricPanel(false);
                                            }}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '4px',
                                                padding: '6px 12px',
                                                borderRadius: '20px',
                                                border: view.is_personal ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
                                                background: activeView === `saved-${view.id}`
                                                    ? (view.is_personal ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)')
                                                    : (view.is_personal ? 'rgba(59, 130, 246, 0.05)' : 'rgba(16, 185, 129, 0.05)'),
                                                color: view.is_personal ? '#60a5fa' : '#34d399',
                                                fontSize: '0.85rem',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                            title={view.is_personal ? (language === 'zh' ? '個人視角' : 'Personal View') : (language === 'zh' ? '團隊視角' : 'Team View')}
                                        >
                                            {view.is_personal ? <FiUser size={12} /> : <FiUsers size={12} />}
                                            {view.name}
                                        </button>
                                    ))}
                                </>
                            )}
                        </div>
                    </div>

                    {/* Row 2: Filter Toolbar (Moved here) */}
                    <div style={{
                        display: 'flex',
                        flexDirection: isMobile ? 'column' : 'row',
                        gap: '16px',
                        alignItems: isMobile ? 'stretch' : 'center',
                        marginBottom: '16px',
                        background: 'rgba(255,255,255,0.03)',
                        padding: '12px',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        {/* Keyword Search */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                            <span style={{ fontSize: '1.2rem' }}>🔍</span>
                            <input
                                type="text"
                                placeholder={language === 'zh' ? "搜尋關鍵字..." : "Search keyword..."}
                                value={filterKeyword}
                                onChange={(e) => setFilterKeyword(e.target.value)}
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--text-primary)',
                                    fontSize: '1rem',
                                    width: '100%',
                                    outline: 'none'
                                }}
                            />
                        </div>

                        <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>

                        {/* Filter Mode */}
                        <select
                            value={filterMode}
                            onChange={(e) => setFilterMode(e.target.value)}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--glass-border)',
                                color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                                cursor: 'pointer',
                                outline: 'none',
                                padding: '6px 10px',
                                borderRadius: '6px'
                            }}
                        >
                            <option value="include">{language === 'zh' ? '包含 (Include)' : 'Include'}</option>
                            <option value="exclude">{language === 'zh' ? '排除 (Exclude)' : 'Exclude'}</option>
                        </select>

                        <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>

                        {/* Active Only Toggle */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                            <span style={{ fontSize: '0.9rem', color: filterActiveOnly ? '#4ade80' : 'var(--text-secondary)', fontWeight: filterActiveOnly ? 600 : 400 }}>
                                ⚡ {language === 'zh' ? '只看快篩 (Active)' : 'Active Only'}
                            </span>
                            <div className="switch" style={{ position: 'relative', display: 'inline-block', width: '36px', height: '20px' }}>
                                <input type="checkbox" checked={filterActiveOnly} onChange={(e) => setFilterActiveOnly(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{
                                    position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                    backgroundColor: filterActiveOnly ? '#4ade80' : '#4b5563', borderRadius: '20px', transition: '.4s'
                                }}>
                                    <span style={{
                                        position: 'absolute', content: "", height: '14px', width: '14px', left: '3px', bottom: '3px',
                                        backgroundColor: 'white', transition: '.4s', borderRadius: '50%',
                                        transform: filterActiveOnly ? 'translateX(16px)' : 'translateX(0)'
                                    }}></span>
                                </span>
                            </div>
                        </label>

                        {level === 'ad' && (
                            <>
                                <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>
                                <select
                                    value={filterObservationImported}
                                    onChange={(e) => setFilterObservationImported(e.target.value)}
                                    style={{
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                        cursor: 'pointer',
                                        outline: 'none',
                                        padding: '6px 10px',
                                        borderRadius: '6px'
                                    }}
                                >
                                    <option value="all">{language === 'zh' ? '全部匯入狀態' : 'All Import Status'}</option>
                                    <option value="imported">{language === 'zh' ? '已送出' : 'Imported'}</option>
                                    <option value="not_imported">{language === 'zh' ? '未送出' : 'Not Imported'}</option>
                                </select>
                            </>
                        )}
                    </div>

                    {activeView === 'custom' && showMetricPanel && (
                        <div style={{ marginTop: '16px', animation: 'fadeIn 0.3s' }}>
                            {ALL_METRIC_GROUPS.map(group => (
                                <div key={group.id} style={{ marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <div style={{ fontSize: '0.85rem', color: group.color || 'var(--accent-primary)', fontWeight: 'bold' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', display: 'flex', gap: '8px' }}>
                                            <span
                                                onClick={() => {
                                                    const newSet = new Set(selectedMetrics);
                                                    // Use composite keys
                                                    group.metrics.forEach(m => newSet.add(`${group.id}:${m.key}`));
                                                    setSelectedMetrics(newSet);
                                                }}
                                                style={{ color: 'var(--accent-primary)', cursor: 'pointer', textDecoration: 'underline' }}
                                            >
                                                {language === 'zh' ? '全選' : 'Select All'}
                                            </span>
                                            <span style={{ color: 'var(--text-tertiary)' }}>|</span>
                                            <span
                                                onClick={() => {
                                                    const newSet = new Set(selectedMetrics);
                                                    group.metrics.forEach(m => newSet.delete(`${group.id}:${m.key}`));
                                                    setSelectedMetrics(newSet);
                                                }}
                                                style={{ color: 'var(--accent-primary)', cursor: 'pointer', textDecoration: 'underline' }}
                                            >
                                                {language === 'zh' ? '全消' : 'Deselect All'}
                                            </span>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                                        {group.metrics.map(metric => (
                                            <label key={metric.key} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedMetrics.has(`${group.id}:${metric.key}`)}
                                                    onChange={() => toggleMetric(group.id, metric.key)}
                                                    style={{ accentColor: 'var(--accent-primary)' }}
                                                />
                                                {language === 'zh' ? metric.label_zh : metric.label_en}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            ))}

                            {/* Done / Collapse Button */}
                            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
                                <button
                                    onClick={() => setShowMetricPanel(false)}
                                    style={{
                                        padding: '8px 24px',
                                        borderRadius: '20px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'white',
                                        fontSize: '0.9rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        display: 'flex', alignItems: 'center', gap: '8px'
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                                >
                                    <FiChevronUp /> {language === 'zh' ? '完成並收合' : 'Done & Collapse'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>


                {/* Right Panel: Actions */}
                <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    {/* (Same advanced options) */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)' }}>{txt.advanced}</h3>
                        </div>

                        {/* Comparison Toggle */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{txt.compareMode}</span>
                            <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '40px', height: '24px' }}>
                                <input type="checkbox" checked={isCompareMode} onChange={(e) => setIsCompareMode(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{
                                    position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                    backgroundColor: isCompareMode ? 'var(--accent-primary)' : '#ccc', borderRadius: '24px', transition: '.4s'
                                }}>
                                    <span style={{
                                        position: 'absolute', content: "", height: '16px', width: '16px', left: '4px', bottom: '4px',
                                        backgroundColor: 'white', transition: '.4s', borderRadius: '50%',
                                        transform: isCompareMode ? 'translateX(16px)' : 'translateX(0)'
                                    }}></span>
                                </span>
                            </label>
                        </div>

                        {/* Comparison Date Selector (Visible only if enabled) */}
                        {isCompareMode && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', transition: 'all 0.3s' }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.comparePeriod}</label>
                                <select
                                    value={comparePreset}
                                    onChange={handleComparePresetChange}
                                    style={{
                                        padding: '10px',
                                        borderRadius: '8px',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'var(--text-primary)',
                                        width: '100%'
                                    }}
                                >
                                    {COMPARE_PRESETS.map(p => (
                                        <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                            {txt.comparePresets[p.value] || p.label}
                                        </option>
                                    ))}
                                </select>

                                {/* Custom Compare Date Inputs */}
                                {comparePreset === 'custom' && (
                                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                                {language === 'zh' ? '比較開始日期' : 'Compare Start'}
                                            </label>
                                            <input 
                                                type="date" 
                                                value={compareDateRange.since} 
                                                onChange={(e) => setCompareDateRange({ ...compareDateRange, since: e.target.value })}
                                                style={{ 
                                                    padding: '10px', 
                                                    borderRadius: '8px', 
                                                    background: 'rgba(255,255,255,0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    color: 'var(--text-primary)',
                                                    colorScheme: 'dark',
                                                    width: '100%' 
                                                }} 
                                            />
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                                {language === 'zh' ? '比較結束日期' : 'Compare End'}
                                            </label>
                                            <input 
                                                type="date" 
                                                value={compareDateRange.until} 
                                                onChange={(e) => setCompareDateRange({ ...compareDateRange, until: e.target.value })}
                                                style={{ 
                                                    padding: '10px', 
                                                    borderRadius: '8px', 
                                                    background: 'rgba(255,255,255,0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    color: 'var(--text-primary)',
                                                    colorScheme: 'dark',
                                                    width: '100%' 
                                                }} 
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => setShowReportModal(true)}
                        style={{
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '1rem',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '8px',
                            opacity: reportData && reportData.length > 0 ? 1 : 0.5,
                            pointerEvents: reportData && reportData.length > 0 ? 'auto' : 'none'
                        }}
                    >
                        <FiFileText /> {language === 'zh' ? '匯出報表' : 'Export Report'}
                    </button>

                    <button
                        onClick={fetchAnalytics}
                        style={{
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'var(--accent-primary)',
                            border: 'none',
                            borderRadius: '8px',
                            color: 'white',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '1rem',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        {txt.updateReport}
                    </button>
                </div>
            </div>
    </>
);

export default AnalyticsFiltersPanel;
