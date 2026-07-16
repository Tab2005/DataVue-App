import React from 'react';

const RegularDataTab = ({ context }) => {
    const {
        activeTab,
        analytics,
        childRowStyle,
        downloadCSV,
        escapeCSV,
        expandedGroups,
        expandedKeywordsCount,
        expandedPages,
        fetchKeywordGap,
        fetchPageIntent,
        fetchPageTitles,
        getPageIntent,
        getPerformanceIndicator,
        getTitleFromUrl,
        groupedData,
        groupingEnabled,
        groupRowStyle,
        handleSort,
        INTENT_TYPES,
        intentError,
        intentLoading,
        keywordIntents,
        language,
        loadMorePageKeywords,
        loadMoreQueryData,
        pageKeywords,
        pageKeywordsHasMore,
        pageKeywordsLoading,
        pageKeywordsLoadTime,
        pageKeywordsTotalCount,
        pageTitles,
        queryHasMore,
        queryLoadingMore,
        renderSortIndicator,
        rowLimit,
        searchInputStyle,
        searchKeyword,
        selectStyle,
        setDisplayLimit,
        setExpandedKeywordsCount,
        setGroupingEnabled,
        setRowLimit,
        setSearchKeyword,
        setTitlesRefreshing,
        showGroupedView,
        sortedData,
        sortedDataHasMore,
        sortedDataTotal,
        t,
        tableContainerStyle,
        tableHeaderStyle,
        tableScrollStyle,
        tableStyle,
        tdStyle,
        thStyle,
        titlesRefreshing,
        toggleButtonStyle,
        toggleGroup,
        togglePageExpand
    } = context;

    return (
                        /* Regular Table Section */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>
                                    {activeTab === 'daily' && t('每日成效', 'Daily Performance')}
                                    {activeTab === 'query' && t('關鍵字排行', 'Top Keywords')}
                                    {activeTab === 'page' && t('頁面排行', 'Top Pages')}
                                    {activeTab !== 'daily' && ` (${showGroupedView ? groupedData.length + ' 組' : sortedData.length})`}
                                </span>

                                {/* Load time display for page tab */}
                                {activeTab === 'page' && (
                                    <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        marginLeft: '12px',
                                        fontSize: '11px',
                                        color: 'var(--text-tertiary)'
                                    }}>
                                        {pageKeywordsLoading ? (
                                            <span style={{ color: '#3B82F6' }}>
                                                ⏳ {t('載入中...', 'Loading...')}
                                            </span>
                                        ) : pageKeywordsLoadTime !== null ? (
                                            <>
                                                <span style={{
                                                    background: 'rgba(16, 185, 129, 0.15)',
                                                    color: '#10B981',
                                                    padding: '2px 8px',
                                                    borderRadius: '10px',
                                                    fontWeight: '500'
                                                }}>
                                                    ⚡ {pageKeywordsLoadTime}ms
                                                </span>
                                                <span>
                                                    {t(`${pageKeywordsTotalCount.toLocaleString()} 組關鍵字`, `${pageKeywordsTotalCount.toLocaleString()} keyword pairs`)}
                                                </span>
                                                {pageKeywordsHasMore && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            loadMorePageKeywords();
                                                        }}
                                                        style={{
                                                            background: 'rgba(59, 130, 246, 0.15)',
                                                            border: '1px solid rgba(59, 130, 246, 0.3)',
                                                            color: '#3B82F6',
                                                            padding: '2px 8px',
                                                            borderRadius: '10px',
                                                            fontSize: '10px',
                                                            fontWeight: '500',
                                                            cursor: 'pointer'
                                                        }}
                                                        title={t('載入更多關鍵字資料', 'Load more keyword data')}
                                                    >
                                                        {t('載入更多', 'Load More')}
                                                    </button>
                                                )}
                                            </>
                                        ) : null}
                                    </span>
                                )}

                                {/* Controls for query/page tabs */}
                                {activeTab !== 'daily' && (
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                                        {/* Grouping Toggle (only for query tab) */}
                                        {activeTab === 'query' && (
                                            <button
                                                onClick={() => setGroupingEnabled(!groupingEnabled)}
                                                style={toggleButtonStyle(groupingEnabled)}
                                                title={t('將類似關鍵字歸為一組', 'Group similar keywords')}
                                            >
                                                📦 {t('群組', 'Group')}
                                            </button>
                                        )}

                                        {/* Download CSV button (only for query tab when grouping is enabled) */}
                                        {activeTab === 'query' && groupingEnabled && groupedData && groupedData.length > 0 && (
                                            <button
                                                onClick={() => {
                                                    // Prepare CSV content for grouped keywords
                                                    const headers = [
                                                        t('群組關鍵字', 'Group Keyword'),
                                                        t('群組總點擊', 'Group Total Clicks'),
                                                        t('群組總曝光', 'Group Total Impressions'),
                                                        t('子關鍵字數量', 'Sub-keywords Count'),
                                                        t('子關鍵字列表', 'Sub-keywords List')
                                                    ];
                                                    const csvRows = [headers.join(',')];

                                                    groupedData.forEach(group => {
                                                        // Collect all sub-keywords (excluding the main keyword)
                                                        const subKeywords = group.items
                                                            .map(item => item.keys?.[0] || '')
                                                            .filter(kw => kw !== group.mainKeyword)
                                                            .join(' | ');

                                                        csvRows.push([
                                                            escapeCSV(group.mainKeyword),
                                                            group.totalClicks,
                                                            group.totalImpressions,
                                                            group.items.length,
                                                            escapeCSV(subKeywords || '-')
                                                        ].join(','));
                                                    });

                                                    downloadCSV(
                                                        csvRows,
                                                        `gsc_keyword_groups_${new Date().toISOString().split('T')[0]}.csv`
                                                    );
                                                }}
                                                style={toggleButtonStyle(false)}
                                                title={t('下載群組關鍵字為 CSV', 'Download grouped keywords as CSV')}
                                            >
                                                📥 {t('下載 CSV', 'Download CSV')}
                                            </button>
                                        )}

                                        {/* Refresh Titles button (only for page tab) */}
                                        {activeTab === 'page' && (
                                            <button
                                                onClick={async () => {
                                                    setTitlesRefreshing(true);

                                                    // Get URLs based on current rowLimit setting
                                                    const limit = rowLimit === 99999 ? analytics.length : rowLimit;
                                                    const allUrls = analytics.slice(0, limit).map(row => row.keys?.[0]).filter(Boolean);

                                                    // Process in batches of 50 (API limit)
                                                    const batchSize = 50;
                                                    for (let i = 0; i < allUrls.length; i += batchSize) {
                                                        const batch = allUrls.slice(i, i + batchSize);
                                                        console.log(`[Refresh] Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(allUrls.length / batchSize)} (${batch.length} URLs)`);
                                                        await fetchPageTitles(batch, true); // force refresh
                                                    }

                                                    setTitlesRefreshing(false);
                                                }}
                                                disabled={titlesRefreshing}
                                                style={{
                                                    ...toggleButtonStyle(false),
                                                    opacity: titlesRefreshing ? 0.6 : 1,
                                                    cursor: titlesRefreshing ? 'wait' : 'pointer'
                                                }}
                                                title={t('重新抓取頁面標題（依照顯示數量）', 'Refresh page titles (based on display count)')}
                                            >
                                                {titlesRefreshing ? '⏳' : '🔄'} {t('刷新標題', 'Refresh Titles')}
                                            </button>
                                        )}

                                        {/* Download CSV button (only for page tab) */}
                                        {activeTab === 'page' && (
                                            <button
                                                onClick={() => {
                                                    // Get displayed data based on current settings
                                                    const limit = rowLimit === 99999 ? sortedData.length : rowLimit;
                                                    const displayData = sortedData.slice(0, limit);

                                                    // Prepare CSV content
                                                    const headers = ['URL', t('頁面標題', 'Page Title'), t('點擊', 'Clicks'), t('曝光', 'Impressions'), 'CTR', t('排名', 'Position')];
                                                    const csvRows = [headers.join(',')];

                                                    displayData.forEach(row => {
                                                        const pageUrl = row.keys?.[0] || '';
                                                        const title = pageTitles[pageUrl] || getTitleFromUrl(pageUrl);
                                                        const clicks = row.clicks || 0;
                                                        const impressions = row.impressions || 0;
                                                        const ctr = row.ctr ? (row.ctr * 100).toFixed(2) + '%' : '0%';
                                                        const position = row.position ? row.position.toFixed(1) : '-';

                                                        csvRows.push([
                                                            escapeCSV(pageUrl),
                                                            escapeCSV(title),
                                                            clicks,
                                                            impressions,
                                                            ctr,
                                                            position
                                                        ].join(','));
                                                    });

                                                    downloadCSV(
                                                        csvRows,
                                                        `gsc_page_analysis_${new Date().toISOString().split('T')[0]}.csv`
                                                    );
                                                }}
                                                style={toggleButtonStyle(false)}
                                                title={t('下載頁面分析資料為 CSV', 'Download page analysis data as CSV')}
                                            >
                                                📥 {t('下載 CSV', 'Download CSV')}
                                            </button>
                                        )}

                                        <input
                                            type="text"
                                            placeholder={t('搜尋...', 'Search...')}
                                            value={searchKeyword}
                                            onChange={(e) => setSearchKeyword(e.target.value)}
                                            style={searchInputStyle}
                                        />
                                        <select
                                            value={rowLimit}
                                            onChange={(e) => setRowLimit(Number(e.target.value) || 99999)}
                                            style={{ ...selectStyle, width: 'auto', padding: '8px 12px' }}
                                        >
                                            <option value={50}>Top 50</option>
                                            <option value={100}>Top 100</option>
                                            <option value={200}>Top 200</option>
                                            <option value={500}>Top 500</option>
                                            <option value={99999}>{t('全部', 'All')}</option>
                                        </select>
                                    </div>
                                )}
                            </div>

                            {/* Grouping Notice */}
                            {showGroupedView && (
                                <div style={{
                                    padding: '12px 16px',
                                    background: 'rgba(66, 133, 244, 0.1)',
                                    borderBottom: '1px solid var(--glass-border)',
                                    color: 'var(--accent-primary)',
                                    fontSize: '13px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}>
                                    💡 {t('系統已將類似的關鍵字歸為一組，點擊展開查看詳細。', 'Similar keywords are grouped together. Click to expand.')}
                                </div>
                            )}

                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle} onClick={() => activeTab === 'daily' && handleSort('date')}>
                                                {activeTab === 'daily' && <>{t('日期', 'Date')}{renderSortIndicator('date')}</>}
                                                {activeTab === 'query' && t('關鍵字', 'Keyword')}
                                                {activeTab === 'page' && t('頁面', 'Page')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('clicks')}>
                                                {t('點擊', 'Clicks')}{renderSortIndicator('clicks')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('impressions')}>
                                                {t('曝光', 'Impressions')}{renderSortIndicator('impressions')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('ctr')}>
                                                {t('點閱率', 'CTR')}{renderSortIndicator('ctr')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('position')}>
                                                {t('排名', 'Position')}{renderSortIndicator('position')}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {showGroupedView ? (
                                            // Grouped View
                                            groupedData.map((group, gIdx) => (
                                                <React.Fragment key={gIdx}>
                                                    {/* Group Header Row */}
                                                    <tr
                                                        style={groupRowStyle}
                                                        onClick={() => toggleGroup(gIdx)}
                                                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                        onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    >
                                                        <td style={{ ...tdStyle, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                            <span style={{
                                                                display: 'inline-block',
                                                                width: '20px',
                                                                textAlign: 'center',
                                                                transition: 'transform 0.2s',
                                                                transform: expandedGroups.has(gIdx) ? 'rotate(90deg)' : 'rotate(0deg)'
                                                            }}>
                                                                ▶
                                                            </span>
                                                            <span>{group.mainKeyword}</span>
                                                            {group.items.length > 1 && (
                                                                <span style={{
                                                                    background: 'var(--accent-primary)',
                                                                    color: 'white',
                                                                    padding: '2px 8px',
                                                                    borderRadius: '12px',
                                                                    fontSize: '11px',
                                                                    fontWeight: '500'
                                                                }}>
                                                                    +{group.items.length - 1}
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td style={tdStyle}>{group.totalClicks.toLocaleString()}</td>
                                                        <td style={tdStyle}>{group.totalImpressions.toLocaleString()}</td>
                                                        <td style={tdStyle}>-</td>
                                                        <td style={tdStyle}>-</td>
                                                    </tr>

                                                    {/* Child Rows (when expanded) */}
                                                    {expandedGroups.has(gIdx) && group.items.map((row, rIdx) => (
                                                        <tr
                                                            key={`${gIdx}-${rIdx}`}
                                                            style={childRowStyle}
                                                            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                            onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-primary)'}
                                                        >
                                                            <td style={{ ...tdStyle, paddingLeft: '48px', color: 'var(--text-secondary)' }}>
                                                                ↳ {row.keys && row.keys[0]}
                                                            </td>
                                                            <td style={tdStyle}>{row.clicks.toLocaleString()}</td>
                                                            <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                            <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                            <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                                        </tr>
                                                    ))}
                                                </React.Fragment>
                                            ))
                                        ) : (
                                            // Regular View
                                            sortedData.map((row, idx) => {
                                                const pageUrl = row.keys && row.keys[0];
                                                const indicator = activeTab === 'page' ? getPerformanceIndicator(idx, sortedData.length) : null;
                                                const keywords = activeTab === 'page' && pageUrl ? pageKeywords[pageUrl] : null;
                                                const hasKeywords = keywords && keywords.length > 0;
                                                const isExpanded = expandedPages.has(pageUrl);

                                                return (
                                                    <React.Fragment key={idx}>
                                                        <tr
                                                            style={{
                                                                transition: 'background 0.2s',
                                                                background: indicator ? `${indicator.color}10` : 'transparent',
                                                                cursor: hasKeywords ? 'pointer' : 'default'
                                                            }}
                                                            onClick={() => hasKeywords && togglePageExpand(pageUrl)}
                                                            onMouseEnter={(e) => e.currentTarget.style.background = indicator ? `${indicator.color}20` : 'var(--bg-hover)'}
                                                            onMouseLeave={(e) => e.currentTarget.style.background = indicator ? `${indicator.color}10` : 'transparent'}
                                                        >
                                                            <td style={{
                                                                ...tdStyle,
                                                                maxWidth: activeTab === 'page' ? '400px' : 'auto',
                                                                overflow: 'visible',
                                                                whiteSpace: 'normal'
                                                            }}>
                                                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flexWrap: 'wrap' }}>
                                                                    {/* Performance indicator */}
                                                                    {indicator && (
                                                                        <span style={{
                                                                            fontSize: '14px',
                                                                            flexShrink: 0
                                                                        }}>
                                                                            {indicator.label}
                                                                        </span>
                                                                    )}

                                                                    {/* Expand arrow for pages with keywords */}
                                                                    {hasKeywords && (
                                                                        <span style={{
                                                                            display: 'inline-block',
                                                                            width: '16px',
                                                                            textAlign: 'center',
                                                                            transition: 'transform 0.2s',
                                                                            transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                                                                            color: 'var(--text-secondary)',
                                                                            fontSize: '12px',
                                                                            flexShrink: 0
                                                                        }}>
                                                                            ▶
                                                                        </span>
                                                                    )}

                                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                                        {activeTab === 'page' && pageUrl ? (
                                                                            <a
                                                                                href={pageUrl}
                                                                                target="_blank"
                                                                                rel="noopener noreferrer"
                                                                                style={{
                                                                                    color: indicator ? indicator.color : 'var(--accent-primary)',
                                                                                    textDecoration: 'none',
                                                                                    fontWeight: indicator ? '600' : '400',
                                                                                    wordBreak: 'break-word'
                                                                                }}
                                                                                title={pageUrl}
                                                                                onClick={(e) => e.stopPropagation()}
                                                                            >
                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                                    {/* Page Title */}
                                                                                    <span style={{
                                                                                        fontWeight: '500',
                                                                                        color: indicator ? indicator.color : 'var(--text-primary)',
                                                                                        fontSize: '14px'
                                                                                    }}>
                                                                                        {pageTitles[pageUrl] || getTitleFromUrl(pageUrl)}
                                                                                    </span>
                                                                                    {/* URL Path */}
                                                                                    <span style={{
                                                                                        fontSize: '12px',
                                                                                        color: 'var(--text-secondary)',
                                                                                        fontWeight: '400'
                                                                                    }}>
                                                                                        {(() => {
                                                                                            try {
                                                                                                const path = pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                                                return decodeURIComponent(path);
                                                                                            } catch {
                                                                                                return pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                                            }
                                                                                        })()}
                                                                                    </span>
                                                                                </div>
                                                                            </a>
                                                                        ) : (
                                                                            row.keys && row.keys[0]
                                                                        )}

                                                                        {/* Search Intent Badge (AI-powered) */}
                                                                        {activeTab === 'page' && pageUrl && (
                                                                            <div style={{
                                                                                marginTop: '8px',
                                                                                display: 'flex',
                                                                                alignItems: 'center',
                                                                                gap: '8px',
                                                                                flexWrap: 'wrap'
                                                                            }}>
                                                                                {(() => {
                                                                                    // Dynamically calculate page intent based on current keywords
                                                                                    const pageIntent = getPageIntent(pageUrl);
                                                                                    const allKeywords = pageKeywords[pageUrl] || [];
                                                                                    const analyzedCount = allKeywords.filter(kw => {
                                                                                        const query = kw.keyword || kw.query;
                                                                                        return keywordIntents[query];
                                                                                    }).length;
                                                                                    const uncachedCount = allKeywords.length - analyzedCount;

                                                                                    if (pageIntent) {
                                                                                        // Show dynamically calculated intent result
                                                                                        return (
                                                                                            <>
                                                                                                <span
                                                                                                    style={{
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        background: `${INTENT_TYPES[pageIntent.primary_intent]?.color}20`,
                                                                                                        color: INTENT_TYPES[pageIntent.primary_intent]?.color,
                                                                                                        padding: '3px 10px',
                                                                                                        borderRadius: '12px',
                                                                                                        fontSize: '11px',
                                                                                                        fontWeight: '600'
                                                                                                    }}
                                                                                                    title={t('AI 分析的主要搜尋意圖', 'AI-analyzed primary search intent')}
                                                                                                >
                                                                                                    {INTENT_TYPES[pageIntent.primary_intent]?.emoji}
                                                                                                    {language === 'zh'
                                                                                                        ? INTENT_TYPES[pageIntent.primary_intent]?.label_zh
                                                                                                        : INTENT_TYPES[pageIntent.primary_intent]?.label_en}
                                                                                                </span>
                                                                                                {/* Horizontal distribution bar with labels */}
                                                                                                <div style={{
                                                                                                    display: 'flex',
                                                                                                    alignItems: 'center',
                                                                                                    gap: '4px',
                                                                                                    width: '160px',
                                                                                                    height: '18px',
                                                                                                    background: 'rgba(0,0,0,0.2)',
                                                                                                    borderRadius: '4px',
                                                                                                    overflow: 'hidden'
                                                                                                }}>
                                                                                                    {Object.entries(pageIntent.intent_distribution || {})
                                                                                                        .filter(([, value]) => value > 0.05)
                                                                                                        .sort((a, b) => b[1] - a[1])
                                                                                                        .map(([intent, value]) => (
                                                                                                            <div
                                                                                                                key={intent}
                                                                                                                style={{
                                                                                                                    display: 'flex',
                                                                                                                    alignItems: 'center',
                                                                                                                    justifyContent: 'center',
                                                                                                                    width: `${value * 100}%`,
                                                                                                                    height: '100%',
                                                                                                                    background: INTENT_TYPES[intent]?.color || '#666',
                                                                                                                    fontSize: '9px',
                                                                                                                    fontWeight: '500',
                                                                                                                    color: 'white',
                                                                                                                    whiteSpace: 'nowrap',
                                                                                                                    overflow: 'hidden',
                                                                                                                    textShadow: '0 1px 2px rgba(0,0,0,0.5)'
                                                                                                                }}
                                                                                                                title={`${language === 'zh' ? INTENT_TYPES[intent]?.label_zh : INTENT_TYPES[intent]?.label_en}: ${(value * 100).toFixed(0)}%`}
                                                                                                            >
                                                                                                                {value >= 0.15 && `${(value * 100).toFixed(0)}%`}
                                                                                                            </div>
                                                                                                        ))}
                                                                                                </div>
                                                                                                {/* Show analyzed count and continue button if needed */}
                                                                                                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>
                                                                                                    ({analyzedCount}/{allKeywords.length})
                                                                                                </span>
                                                                                                {/* Show loading indicator during continue analysis */}
                                                                                                {intentLoading[pageUrl] && (
                                                                                                    <span style={{
                                                                                                        fontSize: '10px',
                                                                                                        color: '#3B82F6',
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        animation: 'pulse 1.5s ease-in-out infinite'
                                                                                                    }}>
                                                                                                        ⏳ {t('分析中', 'Analyzing')}...
                                                                                                    </span>
                                                                                                )}
                                                                                                {/* Continue analysis button if there are uncached keywords */}
                                                                                                {uncachedCount > 0 && !intentLoading[pageUrl] && (
                                                                                                    <button
                                                                                                        onClick={(e) => {
                                                                                                            e.stopPropagation();
                                                                                                            // Check if using Gemini provider
                                                                                                            const provider = localStorage.getItem('ai_provider') || 'zeabur';
                                                                                                            const isGemini = provider === 'gemini';
                                                                                                            const batchCount = Math.ceil(uncachedCount / 10);
                                                                                                            const estimatedTime = isGemini && batchCount > 1 ? Math.round(batchCount * 6) : 0;

                                                                                                            // Show confirmation dialog for continue analysis (API cost warning)
                                                                                                            let message = language === 'zh'
                                                                                                                ? `⚠️ 繼續分析將分析剩餘 ${Math.min(uncachedCount, 100)} 個關鍵字\n\n這會消耗 AI API 額度，確定要繼續嗎？`
                                                                                                                : `⚠️ Continue analysis will analyze ${Math.min(uncachedCount, 100)} more keywords\n\nThis will consume AI API credits. Continue?`;

                                                                                                            // Add Gemini rate limit warning
                                                                                                            if (isGemini && batchCount > 1) {
                                                                                                                message += language === 'zh'
                                                                                                                    ? `\n\n💎 您正在使用 Google Gemini，因免費版有請求限制，\n分析將分 ${batchCount} 批次進行，預計需要 ${estimatedTime} 秒。`
                                                                                                                    : `\n\n💎 You're using Google Gemini. Due to free tier rate limits,\nanalysis will be processed in ${batchCount} batches (~${estimatedTime}s).`;
                                                                                                            }

                                                                                                            if (window.confirm(message)) {
                                                                                                                fetchPageIntent(pageUrl, true); // analyzeAll = true
                                                                                                            }
                                                                                                        }}
                                                                                                        style={{
                                                                                                            display: 'inline-flex',
                                                                                                            alignItems: 'center',
                                                                                                            gap: '4px',
                                                                                                            background: 'rgba(59, 130, 246, 0.15)',
                                                                                                            border: '1px solid rgba(59, 130, 246, 0.4)',
                                                                                                            color: '#3B82F6',
                                                                                                            padding: '3px 10px',
                                                                                                            borderRadius: '12px',
                                                                                                            fontSize: '10px',
                                                                                                            fontWeight: '500',
                                                                                                            cursor: 'pointer',
                                                                                                            transition: 'all 0.2s'
                                                                                                        }}
                                                                                                        onMouseEnter={(e) => {
                                                                                                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.25)';
                                                                                                        }}
                                                                                                        onMouseLeave={(e) => {
                                                                                                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                                                                                                        }}
                                                                                                        title={t(`還有 ${uncachedCount} 個關鍵字待分析`, `${uncachedCount} more keywords to analyze`)}
                                                                                                    >
                                                                                                        🔄 {t('繼續分析', 'Continue')} +{uncachedCount}
                                                                                                    </button>
                                                                                                )}
                                                                                            </>
                                                                                        );
                                                                                    } else if (intentLoading[pageUrl]) {
                                                                                        // Loading state
                                                                                        return (
                                                                                            <span style={{
                                                                                                fontSize: '11px',
                                                                                                color: 'var(--text-secondary)',
                                                                                                display: 'flex',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px'
                                                                                            }}>
                                                                                                <span style={{ animation: 'spin 1s linear infinite' }}>🔄</span>
                                                                                                {t('分析中...', 'Analyzing...')}
                                                                                            </span>
                                                                                        );
                                                                                    } else if (intentError[pageUrl]) {
                                                                                        // Error state
                                                                                        return (
                                                                                            <span style={{
                                                                                                fontSize: '11px',
                                                                                                color: '#EF4444',
                                                                                                display: 'flex',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px'
                                                                                            }}>
                                                                                                ⚠️ {t('分析失敗', 'Analysis failed')}
                                                                                            </span>
                                                                                        );
                                                                                    } else {
                                                                                        // Analyze button with keyword count
                                                                                        const allKeywords = pageKeywords[pageUrl] || [];
                                                                                        const analyzedCount = allKeywords.filter(kw => {
                                                                                            const query = kw.keyword || kw.query;
                                                                                            return keywordIntents[query];
                                                                                        }).length;
                                                                                        const uncachedCount = allKeywords.length - analyzedCount;

                                                                                        return (
                                                                                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                                                                <button
                                                                                                    onClick={(e) => {
                                                                                                        e.stopPropagation();
                                                                                                        fetchPageIntent(pageUrl);
                                                                                                    }}
                                                                                                    style={{
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        background: 'transparent',
                                                                                                        border: '1px dashed var(--glass-border)',
                                                                                                        color: 'var(--text-secondary)',
                                                                                                        padding: '3px 10px',
                                                                                                        borderRadius: '12px',
                                                                                                        fontSize: '11px',
                                                                                                        cursor: 'pointer',
                                                                                                        transition: 'all 0.2s'
                                                                                                    }}
                                                                                                    onMouseEnter={(e) => {
                                                                                                        e.currentTarget.style.borderColor = 'var(--accent-primary)';
                                                                                                        e.currentTarget.style.color = 'var(--accent-primary)';
                                                                                                    }}
                                                                                                    onMouseLeave={(e) => {
                                                                                                        e.currentTarget.style.borderColor = 'var(--glass-border)';
                                                                                                        e.currentTarget.style.color = 'var(--text-secondary)';
                                                                                                    }}
                                                                                                    title={t(`共 ${allKeywords.length} 個關鍵字，${uncachedCount} 個待分析`, `${allKeywords.length} keywords, ${uncachedCount} to analyze`)}
                                                                                                >
                                                                                                    🤖 {t('分析意圖', 'Analyze Intent')}
                                                                                                    <span style={{ opacity: 0.7 }}>
                                                                                                        ({allKeywords.length})
                                                                                                    </span>
                                                                                                </button>

                                                                                                <button
                                                                                                    onClick={(e) => {
                                                                                                        e.stopPropagation();
                                                                                                        fetchKeywordGap(pageUrl);
                                                                                                    }}
                                                                                                    style={{
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        background: 'rgba(139, 92, 246, 0.1)',
                                                                                                        border: '1px solid rgba(139, 92, 246, 0.3)',
                                                                                                        color: '#8B5CF6',
                                                                                                        padding: '3px 10px',
                                                                                                        borderRadius: '12px',
                                                                                                        fontSize: '11px',
                                                                                                        cursor: 'pointer',
                                                                                                        transition: 'all 0.2s'
                                                                                                    }}
                                                                                                    title={t('分析內容中缺少的關鍵字', 'Analyze missing keywords in content')}
                                                                                                >
                                                                                                    🎯 {t('缺口分析', 'Gap Analysis')}
                                                                                                </button>
                                                                                            </div>
                                                                                        );
                                                                                    }
                                                                                })()}
                                                                            </div>
                                                                        )}

                                                                        {/* Keyword tags (collapsed preview) */}
                                                                        {hasKeywords && !isExpanded && (
                                                                            <div style={{
                                                                                marginTop: '6px',
                                                                                display: 'flex',
                                                                                flexWrap: 'wrap',
                                                                                gap: '4px'
                                                                            }}>
                                                                                {keywords.slice(0, 3).map((kw, kIdx) => (
                                                                                    <span key={kIdx} style={{
                                                                                        background: 'var(--bg-hover)',
                                                                                        padding: '2px 8px',
                                                                                        borderRadius: '12px',
                                                                                        fontSize: '11px',
                                                                                        color: 'var(--text-secondary)'
                                                                                    }}>
                                                                                        {kw.keyword}
                                                                                    </span>
                                                                                ))}
                                                                                {keywords.length > 3 && (
                                                                                    <span style={{
                                                                                        padding: '2px 8px',
                                                                                        fontSize: '11px',
                                                                                        color: 'var(--text-secondary)'
                                                                                    }}>
                                                                                        +{keywords.length - 3}
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </td>
                                                            <td style={{ ...tdStyle, color: indicator?.color || 'inherit', fontWeight: indicator ? '600' : '400' }}>
                                                                {row.clicks.toLocaleString()}
                                                            </td>
                                                            <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                            <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                            <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                                        </tr>

                                                        {/* Expanded keywords list */}
                                                        {isExpanded && keywords && (
                                                            <tr style={{ background: 'var(--bg-primary)' }}>
                                                                <td colSpan={5} style={{ padding: '0 24px 16px 48px' }}>
                                                                    <div style={{
                                                                        background: 'var(--bg-secondary)',
                                                                        borderRadius: '8px',
                                                                        padding: '12px',
                                                                        border: '1px solid var(--glass-border)'
                                                                    }}>
                                                                        <div style={{
                                                                            fontSize: '12px',
                                                                            color: 'var(--text-secondary)',
                                                                            marginBottom: '8px',
                                                                            fontWeight: '500',
                                                                            display: 'flex',
                                                                            justifyContent: 'space-between',
                                                                            alignItems: 'center'
                                                                        }}>
                                                                            <span>🔍 {t('核心關鍵字', 'Core Keywords')}</span>
                                                                            {(() => {
                                                                                // Count how many keywords have been analyzed
                                                                                const analyzedCount = keywords.filter(kw => {
                                                                                    const query = kw.keyword || kw.query;
                                                                                    return keywordIntents[query];
                                                                                }).length;
                                                                                if (analyzedCount > 0) {
                                                                                    return (
                                                                                        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                                                                                            ✨ AI {t('意圖分析', 'Intent Analysis')} ({analyzedCount}/{keywords.length})
                                                                                        </span>
                                                                                    );
                                                                                }
                                                                                return null;
                                                                            })()}
                                                                        </div>
                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                                            {/* Show keywords with dynamic limit (default 5, increases with load more) */}
                                                                            {keywords.slice(0, expandedKeywordsCount[pageUrl] || 5).map((kw, kIdx) => {
                                                                                const query = kw.keyword || kw.query;
                                                                                // Lookup intent from keyword-level cache
                                                                                const cachedIntent = keywordIntents[query];
                                                                                const intent = cachedIntent?.intent || null;
                                                                                const intentType = INTENT_TYPES[intent];
                                                                                const clicks = kw.clicks || 0;
                                                                                const impressions = kw.impressions || 0;

                                                                                return (
                                                                                    <div key={kIdx} style={{
                                                                                        display: 'flex',
                                                                                        justifyContent: 'space-between',
                                                                                        alignItems: 'center',
                                                                                        padding: '6px 10px',
                                                                                        background: 'var(--bg-primary)',
                                                                                        borderRadius: '6px',
                                                                                        fontSize: '13px',
                                                                                        gap: '8px'
                                                                                    }}>
                                                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                                                                                            <span style={{ color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                {query}
                                                                                            </span>
                                                                                            {/* Intent badge for each keyword */}
                                                                                            {intentType && (
                                                                                                <span style={{
                                                                                                    display: 'inline-flex',
                                                                                                    alignItems: 'center',
                                                                                                    gap: '2px',
                                                                                                    background: `${intentType.color}15`,
                                                                                                    color: intentType.color,
                                                                                                    padding: '2px 6px',
                                                                                                    borderRadius: '8px',
                                                                                                    fontSize: '10px',
                                                                                                    fontWeight: '500',
                                                                                                    flexShrink: 0
                                                                                                }}>
                                                                                                    {intentType.emoji}
                                                                                                    {language === 'zh' ? intentType.label_zh : intentType.label_en}
                                                                                                </span>
                                                                                            )}
                                                                                        </div>
                                                                                        <div style={{ display: 'flex', gap: '12px', flexShrink: 0 }}>
                                                                                            <span style={{
                                                                                                color: 'var(--accent-primary)',
                                                                                                fontWeight: '500',
                                                                                                fontSize: '12px'
                                                                                            }}>
                                                                                                {clicks.toLocaleString()} {t('點擊', 'clicks')}
                                                                                            </span>
                                                                                            <span style={{
                                                                                                color: 'var(--text-secondary)',
                                                                                                fontSize: '12px'
                                                                                            }}>
                                                                                                {impressions.toLocaleString()} {t('曝光', 'impr.')}
                                                                                            </span>
                                                                                        </div>
                                                                                    </div>
                                                                                );
                                                                            })}
                                                                            {/* Show "Load More" button if there are more keywords (dynamic) */}
                                                                            {(() => {
                                                                                const currentLimit = expandedKeywordsCount[pageUrl] || 5;
                                                                                const remaining = keywords.length - currentLimit;

                                                                                if (remaining > 0) {
                                                                                    return (
                                                                                        <button
                                                                                            onClick={(e) => {
                                                                                                e.stopPropagation();
                                                                                                // Load more keywords (increase by 10)
                                                                                                setExpandedKeywordsCount(prev => ({
                                                                                                    ...prev,
                                                                                                    [pageUrl]: currentLimit + 10
                                                                                                }));
                                                                                            }}
                                                                                            style={{
                                                                                                display: 'flex',
                                                                                                justifyContent: 'center',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px',
                                                                                                padding: '6px 12px',
                                                                                                margin: '4px 0',
                                                                                                background: 'rgba(59, 130, 246, 0.1)',
                                                                                                border: '1px solid rgba(59, 130, 246, 0.3)',
                                                                                                borderRadius: '6px',
                                                                                                color: '#3B82F6',
                                                                                                fontSize: '11px',
                                                                                                fontWeight: '500',
                                                                                                cursor: 'pointer',
                                                                                                transition: 'all 0.2s'
                                                                                            }}
                                                                                        >
                                                                                            ⬇️ {t('載入更多', 'Load More')} (+{Math.min(remaining, 10)})
                                                                                        </button>
                                                                                    );
                                                                                }
                                                                                return null;
                                                                            })()}
                                                                        </div>
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                );
                                            })
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Load More from server (query tab, full dataset) */}
                            {activeTab === 'query' && rowLimit === 99999 && queryHasMore && (
                                <div style={{
                                    padding: '16px',
                                    borderTop: '1px solid var(--glass-border)',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {t(`已載入 ${analytics.length} 筆`, `Loaded ${analytics.length} rows`)}
                                    </span>
                                    <button
                                        onClick={loadMoreQueryData}
                                        disabled={queryLoadingMore}
                                        style={{
                                            padding: '8px 20px',
                                            background: 'var(--accent-primary)',
                                            border: 'none',
                                            borderRadius: '8px',
                                            color: 'white',
                                            fontSize: '13px',
                                            fontWeight: '500',
                                            cursor: queryLoadingMore ? 'wait' : 'pointer',
                                            opacity: queryLoadingMore ? 0.7 : 1,
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        {queryLoadingMore
                                            ? t('載入中...', 'Loading...')
                                            : `⬇️ ${t('載入更多資料', 'Load More Data')}`}
                                    </button>
                                </div>
                            )}

                            {/* Load More Button for progressive rendering */}
                            {!showGroupedView && sortedDataHasMore && (
                                <div style={{
                                    padding: '16px',
                                    borderTop: '1px solid var(--glass-border)',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {t(`顯示 ${sortedData.length} / ${sortedDataTotal} 筆`, `Showing ${sortedData.length} of ${sortedDataTotal}`)}
                                    </span>
                                    <button
                                        onClick={() => setDisplayLimit(prev => prev + 100)}
                                        style={{
                                            padding: '8px 20px',
                                            background: 'var(--accent-primary)',
                                            border: 'none',
                                            borderRadius: '8px',
                                            color: 'white',
                                            fontSize: '13px',
                                            fontWeight: '500',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        ⬇️ {t('載入更多', 'Load More')} (+{Math.min(100, sortedDataTotal - sortedData.length)})
                                    </button>
                                    <button
                                        onClick={() => setDisplayLimit(sortedDataTotal)}
                                        style={{
                                            padding: '8px 16px',
                                            background: 'transparent',
                                            border: '1px solid var(--glass-border)',
                                            borderRadius: '8px',
                                            color: 'var(--text-secondary)',
                                            fontSize: '13px',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                        title={sortedDataTotal > 1000
                                            ? t('大量資料可能導致瀏覽器變慢', 'Large data may slow down the browser')
                                            : ''}
                                    >
                                        {t('載入全部', 'Load All')}
                                        {sortedDataTotal > 1000 && ' ⚠️'}
                                    </button>
                                    {/* Warning for large datasets */}
                                    {sortedDataTotal > 5000 && (
                                        <span style={{
                                            fontSize: '11px',
                                            color: '#F59E0B',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px'
                                        }}>
                                            ⚠️ {t('大量資料載入可能較慢', 'Large dataset may be slow')}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
    );
};

export default RegularDataTab;
