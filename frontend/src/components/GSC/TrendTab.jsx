import React from 'react';

const TrendTab = ({ context }) => {
    const {
        getDaysInRange,
        getSortedTrendData,
        getTitleFromUrl,
        language,
        pageTitles,
        rowLimit,
        searchInputStyle,
        searchKeyword,
        selectStyle,
        setRowLimit,
        setSearchKeyword,
        setTrendSubTab,
        t,
        tableContainerStyle,
        tableScrollStyle,
        tableStyle,
        tdStyle,
        thStyle,
        TREND_SUBTABS,
        trendSubTab
    } = context;

    return (
                        <div style={tableContainerStyle}>
                            {/* Trend Sub-tabs */}
                            <div style={{
                                padding: '12px 16px',
                                borderBottom: '1px solid var(--glass-border)',
                                display: 'flex',
                                gap: '8px',
                                flexWrap: 'wrap',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}>
                                <div style={{ display: 'flex', gap: '4px' }}>
                                    {TREND_SUBTABS.map(subtab => (
                                        <button
                                            key={subtab.key}
                                            onClick={() => setTrendSubTab(subtab.key)}
                                            style={{
                                                padding: '8px 16px',
                                                borderRadius: '6px',
                                                border: 'none',
                                                background: trendSubTab === subtab.key ? 'var(--accent-primary)' : 'var(--bg-primary)',
                                                color: trendSubTab === subtab.key ? 'white' : 'var(--text-secondary)',
                                                fontWeight: trendSubTab === subtab.key ? '600' : '400',
                                                fontSize: '13px',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            {language === 'zh' ? subtab.label_zh : subtab.label_en}
                                        </button>
                                    ))}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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
                            </div>

                            {/* Period comparison info */}
                            <div style={{
                                padding: '8px 16px',
                                background: 'var(--bg-primary)',
                                fontSize: '12px',
                                color: 'var(--text-secondary)',
                                borderBottom: '1px solid var(--glass-border)'
                            }}>
                                📊 {t(`比較期間: 本期 ${getDaysInRange()} 天 vs 前期 ${getDaysInRange()} 天`, `Comparing: Current ${getDaysInRange()} days vs Previous ${getDaysInRange()} days`)}
                            </div>

                            {/* Trend Table */}
                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle}>{t('頁面', 'Page')}</th>
                                            <th style={thStyle}>{t('點擊', 'Clicks')}</th>
                                            <th style={thStyle}>{t('變化', 'Change')}</th>
                                            <th style={thStyle}>{t('曝光', 'Impressions')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {getSortedTrendData().map((row, idx) => {
                                            const pageUrl = row.keys?.[0] || '';
                                            const isUp = row.clicksChange > 0;
                                            const isDown = row.clicksChange < 0;

                                            return (
                                                <tr
                                                    key={idx}
                                                    style={{
                                                        background: isUp ? 'rgba(16, 185, 129, 0.05)' : isDown ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                                                        transition: 'background 0.2s'
                                                    }}
                                                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    onMouseLeave={(e) => e.currentTarget.style.background = isUp ? 'rgba(16, 185, 129, 0.05)' : isDown ? 'rgba(239, 68, 68, 0.05)' : 'transparent'}
                                                >
                                                    <td style={{ ...tdStyle, maxWidth: '350px' }}>
                                                        <a
                                                            href={pageUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            style={{
                                                                color: 'var(--accent-primary)',
                                                                textDecoration: 'none',
                                                                wordBreak: 'break-word'
                                                            }}
                                                            title={pageUrl}
                                                        >
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                {/* Page Title */}
                                                                <span style={{
                                                                    fontWeight: '500',
                                                                    color: 'var(--text-primary)',
                                                                    fontSize: '14px'
                                                                }}>
                                                                    {pageTitles[pageUrl] || getTitleFromUrl(pageUrl)}
                                                                </span>
                                                                {/* URL Path */}
                                                                <span style={{
                                                                    fontSize: '12px',
                                                                    color: 'var(--text-secondary)'
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
                                                    </td>
                                                    <td style={tdStyle}>
                                                        {row.clicks.toLocaleString()}
                                                    </td>
                                                    <td style={{
                                                        ...tdStyle,
                                                        color: isUp ? '#10B981' : isDown ? '#EF4444' : 'var(--text-secondary)',
                                                        fontWeight: '600'
                                                    }}>
                                                        {isUp ? '↑' : isDown ? '↓' : ''} {Math.abs(row.clicksChange).toFixed(0)}%
                                                    </td>
                                                    <td style={tdStyle}>
                                                        {row.impressions.toLocaleString()}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
    );
};

export default TrendTab;
