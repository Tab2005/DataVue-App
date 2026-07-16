import React from 'react';

const CountryTab = ({ context }) => {
    const {
        analytics,
        COUNTRY_NAMES,
        getSortedFilteredData,
        handleSort,
        language,
        renderSortIndicator,
        t,
        tableContainerStyle,
        tableHeaderStyle,
        tableScrollStyle,
        tableStyle,
        tdStyle,
        thStyle
    } = context;

    return (
                        /* Country Distribution Tab */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>🌍 {t('地區流量分佈', 'Traffic by Country')} ({analytics.length})</span>
                            </div>
                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle}>{t('國家/地區', 'Country')}</th>
                                            <th style={thStyle} onClick={() => handleSort('clicks')}>
                                                {t('點擊', 'Clicks')}{renderSortIndicator('clicks')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('impressions')}>
                                                {t('曝光', 'Impressions')}{renderSortIndicator('impressions')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('ctr')}>
                                                {t('點閱率', 'CTR')}{renderSortIndicator('ctr')}
                                            </th>
                                            <th style={thStyle}>{t('佔比', 'Share')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(() => {
                                            const totalClicks = analytics.reduce((sum, row) => sum + row.clicks, 0);
                                            const { displayData } = getSortedFilteredData();
                                            return displayData.map((row, idx) => {
                                                const countryCode = (row.keys?.[0] || '').toLowerCase();
                                                const countryName = COUNTRY_NAMES[countryCode]?.[language] || countryCode.toUpperCase();
                                                const sharePercent = totalClicks > 0 ? (row.clicks / totalClicks * 100) : 0;

                                                return (
                                                    <tr
                                                        key={idx}
                                                        style={{ transition: 'background 0.2s' }}
                                                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                                    >
                                                        <td style={tdStyle}>
                                                            <span style={{ fontSize: '16px', marginRight: '8px' }}>🏳️</span>
                                                            {countryName}
                                                        </td>
                                                        <td style={{ ...tdStyle, fontWeight: '600', color: 'var(--accent-primary)' }}>
                                                            {row.clicks.toLocaleString()}
                                                        </td>
                                                        <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                        <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                        <td style={tdStyle}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <div style={{
                                                                    width: '60px',
                                                                    height: '8px',
                                                                    background: 'var(--bg-hover)',
                                                                    borderRadius: '4px',
                                                                    overflow: 'hidden'
                                                                }}>
                                                                    <div style={{
                                                                        width: `${Math.min(sharePercent, 100)}%`,
                                                                        height: '100%',
                                                                        background: 'var(--accent-primary)',
                                                                        borderRadius: '4px'
                                                                    }} />
                                                                </div>
                                                                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                                    {sharePercent.toFixed(1)}%
                                                                </span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                );
                                            });
                                        })()}
                                    </tbody>
                                </table>
                            </div>
                        </div>
    );
};

export default CountryTab;
