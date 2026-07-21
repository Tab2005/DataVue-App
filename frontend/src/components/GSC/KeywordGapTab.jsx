import React from 'react';

const KeywordGapTab = ({ context }) => {
    const {
        cardLabelStyle,
        cardStyle,
        cardValueStyle,
        DATE_PRESETS,
        downloadCSV,
        escapeCSV,
        fetchKeywordGap,
        gapDatePreset,
        gapDateRange,
        gapError,
        gapLoading,
        gapResults,
        gapTopN,
        gapUrl,
        getDateRangeFromPreset,
        isMobile,
        language,
        searchInputStyle,
        selectStyle,
        setGapDatePreset,
        setGapDateRange,
        setGapTopN,
        setGapUrl,
        t,
        tableContainerStyle,
        tableScrollStyle,
        tableStyle,
        tdStyle,
        thStyle,
        toggleButtonStyle,
        suggestLoading,
        suggestResults,
        suggestError,
        fetchContentGapSuggestions
    } = context;

    const SUGGESTION_TYPE_LABELS = {
        expand_existing: { emoji: '📝', label_zh: '補充現有內容', label_en: 'Expand Existing Page' },
        new_article: { emoji: '✨', label_zh: '新文章方向', label_en: 'New Article Direction' }
    };

    return (
                        /* Keyword Gap Analysis Tab */
                        <div style={{ ...tableContainerStyle, padding: '24px' }}>
                            <div style={{
                                marginBottom: '24px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                flexWrap: 'wrap',
                                gap: '16px'
                            }}>
                                <div>
                                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: 'var(--text-primary)' }}>
                                        🎯 {t('關鍵字內容缺口分析', 'Keyword Content Gap Analysis')}
                                    </h3>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                        {t('找出該頁面有排名但在內文中未出現的關鍵字，優化內容覆蓋率。', 'Find keywords your page ranks for but are missing from the content.')}
                                    </p>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                    {gapResults && (
                                        <button
                                            onClick={() => {
                                                const csvRows = [];
                                                // CSV Header
                                                csvRows.push([
                                                    t('關鍵字', 'Keyword'),
                                                    t('狀態', 'Status'),
                                                    t('點擊', 'Clicks'),
                                                    t('曝光', 'Impressions'),
                                                    t('排名', 'Position')
                                                ].join(','));

                                                // Add data rows
                                                gapResults.results.forEach(res => {
                                                    csvRows.push([
                                                        escapeCSV(res.query),
                                                        res.in_content ? t('已涵蓋', 'Covered') : t('缺漏', 'Missing'),
                                                        res.clicks,
                                                        res.impressions,
                                                        res.position.toFixed(1)
                                                    ].join(','));
                                                });

                                                downloadCSV(
                                                    csvRows,
                                                    `keyword_gap_analysis_${gapUrl.split('/').filter(Boolean).pop() || 'report'}_${new Date().toISOString().split('T')[0]}.csv`
                                                );
                                            }}
                                            style={{
                                                ...toggleButtonStyle(false),
                                                padding: '8px 16px',
                                                height: '42px', // Match date selector height
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '6px'
                                            }}
                                            title={t('下載缺口分析清單為 CSV', 'Download gap analysis list as CSV')}
                                        >
                                            📥 {t('下載清單', 'Download List')}
                                        </button>
                                    )}

                                    {/* Local Date Selector for Gap Analysis */}
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        padding: '8px 16px',
                                        borderRadius: '12px',
                                        border: '1px solid var(--glass-border)'
                                    }}>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                            📅 {t('分析區間', 'Date Range')}:
                                        </span>
                                        <select
                                            value={gapDatePreset}
                                            onChange={(e) => {
                                                const preset = e.target.value;
                                                setGapDatePreset(preset);
                                                // Only reset range if not custom, or keep current if switching to custom
                                                if (preset !== 'custom') {
                                                    setGapDateRange(getDateRangeFromPreset(preset));
                                                }
                                            }}
                                            style={{
                                                background: 'transparent',
                                                border: 'none',
                                                color: 'var(--text-primary)',
                                                fontSize: '0.85rem',
                                                cursor: 'pointer',
                                                outline: 'none'
                                            }}
                                        >
                                            {DATE_PRESETS.map(p => (
                                                <option key={p.key} value={p.key} style={{ color: 'black' }}>
                                                    {language === 'zh' ? p.label_zh : p.label_en}
                                                </option>
                                            ))}
                                        </select>

                                        {gapDatePreset === 'custom' ? (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <input
                                                    type="date"
                                                    value={gapDateRange.start}
                                                    onChange={(e) => setGapDateRange(prev => ({ ...prev, start: e.target.value }))}
                                                    style={{
                                                        background: 'rgba(255, 255, 255, 0.1)',
                                                        border: '1px solid var(--glass-border)',
                                                        borderRadius: '6px',
                                                        color: 'white',
                                                        fontSize: '0.8rem',
                                                        padding: '2px 4px',
                                                        colorScheme: 'light'
                                                    }}
                                                />
                                                <span style={{ color: 'var(--text-tertiary)' }}>~</span>
                                                <input
                                                    type="date"
                                                    value={gapDateRange.end}
                                                    onChange={(e) => setGapDateRange(prev => ({ ...prev, end: e.target.value }))}
                                                    style={{
                                                        background: 'rgba(255, 255, 255, 0.1)',
                                                        border: '1px solid var(--glass-border)',
                                                        borderRadius: '6px',
                                                        color: 'white',
                                                        fontSize: '0.8rem',
                                                        padding: '2px 4px',
                                                        colorScheme: 'light'
                                                    }}
                                                />
                                            </div>
                                        ) : (
                                            <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: '600' }}>
                                                {gapDateRange.start} ~ {gapDateRange.end}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
                                <div style={{ flex: 1, minWidth: isMobile ? '100%' : '300px' }}>
                                    <input
                                        type="text"
                                        placeholder={t('輸入網頁 URL...', 'Enter page URL...')}
                                        value={gapUrl}
                                        onChange={(e) => setGapUrl(e.target.value)}
                                        style={{ ...searchInputStyle, width: '100%', boxSizing: 'border-box' }}
                                    />
                                </div>

                                <div style={{ minWidth: isMobile ? '100%' : '140px' }}>
                                    <select
                                        value={gapTopN}
                                        onChange={(e) => setGapTopN(parseInt(e.target.value))}
                                        style={{ ...selectStyle, width: '100%' }}
                                        title={t('分析該網頁在 GSC 中點擊前 N 名的關鍵字', 'Analyze top N keywords for this page in GSC')}
                                    >
                                        <option value={50}>Top 50 Queries</option>
                                        <option value={100}>Top 100 Queries</option>
                                        <option value={200}>Top 200 Queries</option>
                                        <option value={500}>Top 500 Queries</option>
                                        <option value={0}>{t('全部 (不限數量)', 'All Keywords (No Limit)')}</option>
                                    </select>
                                </div>

                                <button
                                    onClick={() => fetchKeywordGap()}
                                    disabled={gapLoading}
                                    style={{
                                        padding: '10px 24px',
                                        background: 'var(--accent-primary)',
                                        border: 'none',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontWeight: '600',
                                        cursor: gapLoading ? 'wait' : 'pointer',
                                        opacity: gapLoading ? 0.7 : 1,
                                        width: isMobile ? '100%' : 'auto'
                                    }}
                                >
                                    {gapLoading ? t('分析中...', 'Analyzing...') : t('開始分析', 'Analyze Now')}
                                </button>
                            </div>

                            {gapError && (
                                <div style={{
                                    padding: '16px',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    border: '1px solid rgba(239, 68, 68, 0.3)',
                                    borderRadius: '8px',
                                    color: '#EF4444',
                                    marginBottom: '24px'
                                }}>
                                    ⚠️ {gapError}
                                </div>
                            )}

                            {gapResults && (
                                <div>
                                    <div style={{
                                        display: 'grid',
                                        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                                        gap: '16px',
                                        marginBottom: '24px'
                                    }}>
                                        <div style={{ ...cardStyle, background: 'rgba(255,255,255,0.02)' }}>
                                            <div style={cardLabelStyle}>{t('分析關鍵字數', 'Analyzed Keywords')}</div>
                                            <div style={cardValueStyle}>
                                                {gapResults.total_analyzed}
                                                {gapResults.total_found_in_gsc > 0 && (
                                                    <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginLeft: '8px', fontWeight: 'normal' }}>
                                                        / {gapResults.total_found_in_gsc} total
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div style={{ ...cardStyle, border: '1px solid rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.05)' }}>
                                            <div style={cardLabelStyle}>{t('已涵蓋關鍵字', 'Covered Keywords')}</div>
                                            <div style={{ ...cardValueStyle, color: '#10B981' }}>{gapResults.total_analyzed - gapResults.missing_count}</div>
                                        </div>
                                        <div style={{ ...cardStyle, border: '1px solid rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.05)' }}>
                                            <div style={cardLabelStyle}>{t('缺漏關鍵字', 'Missing Keywords')}</div>
                                            <div style={{ ...cardValueStyle, color: '#EF4444' }}>{gapResults.missing_count}</div>
                                        </div>
                                        <div style={{ ...cardStyle, border: '1px solid rgba(251, 191, 36, 0.3)', background: 'rgba(251, 191, 36, 0.05)' }}>
                                            <div style={cardLabelStyle}>{t('關鍵字缺失率', 'Missing Rate')}</div>
                                            <div style={{ ...cardValueStyle, color: '#FBBF24' }}>
                                                {gapResults.total_analyzed > 0
                                                    ? (gapResults.missing_count / gapResults.total_analyzed * 100).toFixed(1)
                                                    : 0}%
                                            </div>
                                        </div>
                                    </div>

                                    <div style={tableScrollStyle}>
                                        <table style={tableStyle}>
                                            <thead>
                                                <tr style={{ background: 'var(--bg-hover)' }}>
                                                    <th style={thStyle}>{t('關鍵字', 'Keyword')}</th>
                                                    <th style={thStyle}>{t('狀態', 'Status')}</th>
                                                    <th style={thStyle}>{t('點擊', 'Clicks')}</th>
                                                    <th style={thStyle}>{t('曝光', 'Impr.')}</th>
                                                    <th style={thStyle}>{t('排名', 'Pos.')}</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {gapResults.results.map((res, idx) => (
                                                    <tr key={idx} style={{ transition: 'background 0.2s' }}>
                                                        <td style={tdStyle}>{res.query}</td>
                                                        <td style={tdStyle}>
                                                            <span style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '4px',
                                                                padding: '2px 8px',
                                                                borderRadius: '12px',
                                                                fontSize: '11px',
                                                                fontWeight: '600',
                                                                background: res.in_content ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                                                color: res.in_content ? '#10B981' : '#EF4444'
                                                            }}>
                                                                {res.in_content ? '✅ ' + t('已涵蓋', 'In Content') : '❌ ' + t('未出現', 'Missing')}
                                                            </span>
                                                        </td>
                                                        <td style={tdStyle}>{res.clicks.toLocaleString()}</td>
                                                        <td style={tdStyle}>{res.impressions.toLocaleString()}</td>
                                                        <td style={tdStyle}>{res.position.toFixed(1)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {gapResults.missing_count > 0 && (
                                        <div style={{ marginTop: '24px' }}>
                                            <button
                                                onClick={() => fetchContentGapSuggestions()}
                                                disabled={suggestLoading}
                                                style={{
                                                    padding: '10px 24px',
                                                    background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
                                                    border: 'none',
                                                    borderRadius: '8px',
                                                    color: 'white',
                                                    fontWeight: '600',
                                                    cursor: suggestLoading ? 'wait' : 'pointer',
                                                    opacity: suggestLoading ? 0.7 : 1,
                                                    width: isMobile ? '100%' : 'auto'
                                                }}
                                            >
                                                {suggestLoading
                                                    ? t('產生建議中...', 'Generating suggestions...')
                                                    : t('🪄 產生文章方向建議', '🪄 Generate Article Direction Suggestions')}
                                            </button>

                                            {suggestError && (
                                                <div style={{
                                                    padding: '16px',
                                                    background: 'rgba(239, 68, 68, 0.1)',
                                                    border: '1px solid rgba(239, 68, 68, 0.3)',
                                                    borderRadius: '8px',
                                                    color: '#EF4444',
                                                    marginTop: '16px'
                                                }}>
                                                    ⚠️ {suggestError}
                                                </div>
                                            )}

                                            {suggestResults && (
                                                <div style={{ marginTop: '16px' }}>
                                                    <div style={{
                                                        fontSize: '0.8rem',
                                                        color: 'var(--text-tertiary)',
                                                        marginBottom: '12px'
                                                    }}>
                                                        ⚠️ {t(
                                                            'AI 生成建議僅供參考，請人工確認後再採用。',
                                                            'AI-generated suggestions are for reference only — please review before using.'
                                                        )}
                                                    </div>

                                                    {suggestResults.suggestions.length === 0 ? (
                                                        <div style={{ padding: '16px', color: 'var(--text-secondary)' }}>
                                                            {suggestResults.message || t('沒有可用的建議。', 'No suggestions available.')}
                                                        </div>
                                                    ) : (
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                                            {suggestResults.suggestions.map((sug, idx) => {
                                                                const typeInfo = SUGGESTION_TYPE_LABELS[sug.type] || { emoji: '💡', label_zh: sug.type, label_en: sug.type };
                                                                return (
                                                                    <div key={idx} style={{
                                                                        ...cardStyle,
                                                                        background: 'rgba(139, 92, 246, 0.05)',
                                                                        border: '1px solid rgba(139, 92, 246, 0.25)',
                                                                        padding: '20px'
                                                                    }}>
                                                                        <div style={{
                                                                            display: 'inline-flex',
                                                                            alignItems: 'center',
                                                                            gap: '4px',
                                                                            padding: '2px 10px',
                                                                            borderRadius: '12px',
                                                                            fontSize: '11px',
                                                                            fontWeight: '600',
                                                                            background: 'rgba(139, 92, 246, 0.15)',
                                                                            color: '#8B5CF6',
                                                                            marginBottom: '10px'
                                                                        }}>
                                                                            {typeInfo.emoji} {t(typeInfo.label_zh, typeInfo.label_en)}
                                                                        </div>
                                                                        <h4 style={{ margin: '0 0 10px 0', fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                                                                            {sug.title}
                                                                        </h4>
                                                                        {Array.isArray(sug.outline) && sug.outline.length > 0 && (
                                                                            <ul style={{ margin: '0 0 12px 0', paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                                                                {sug.outline.map((point, i) => (
                                                                                    <li key={i} style={{ marginBottom: '4px' }}>{point}</li>
                                                                                ))}
                                                                            </ul>
                                                                        )}
                                                                        {Array.isArray(sug.target_keywords) && sug.target_keywords.length > 0 && (
                                                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
                                                                                {sug.target_keywords.map((kw, i) => (
                                                                                    <span key={i} style={{
                                                                                        fontSize: '11px',
                                                                                        padding: '2px 8px',
                                                                                        borderRadius: '10px',
                                                                                        background: 'rgba(255, 255, 255, 0.08)',
                                                                                        color: 'var(--text-secondary)'
                                                                                    }}>
                                                                                        {kw}
                                                                                    </span>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                        {sug.reasoning && (
                                                                            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                                                                                {sug.reasoning}
                                                                            </p>
                                                                        )}
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
    );
};

export default KeywordGapTab;
