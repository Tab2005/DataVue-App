import React from 'react';
import { GSCDataLoadingState, GSCErrorState } from './GSCUiStates';

const SearchAppearanceTab = ({ context }) => {
    const {
        searchAppearanceData,
        searchAppearanceLoading,
        searchAppearanceError,
        t,
        isMobile,
        cardStyle,
        cardLabelStyle,
        cardValueStyle,
        tableContainerStyle,
        tableHeaderStyle,
        tableScrollStyle,
        tableStyle,
        tdStyle,
        thStyle
    } = context;

    if (searchAppearanceLoading) return <GSCDataLoadingState t={t} />;
    if (searchAppearanceError) return <GSCErrorState error={searchAppearanceError} t={t} />;

    if (!searchAppearanceData || !searchAppearanceData.has_data) {
        return (
            <div style={tableContainerStyle}>
                <div style={tableHeaderStyle}>
                    <span>🎨 {t('搜尋外觀', 'Search Appearance')}</span>
                </div>
                <div style={{ padding: '32px 20px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                    {t(
                        '此網站在指定期間內，searchAppearance 維度沒有任何資料。可能是流量規模、語言或地區尚未涵蓋 AI Overview 等特殊搜尋外觀，或此站台目前沒有任何搜尋外觀類型的曝光紀錄。',
                        'No searchAppearance data found for this site in the selected period. This may be due to traffic volume, language/region coverage, or the site simply not having any search appearance impressions yet.'
                    )}
                </div>
            </div>
        );
    }

    const { types, total_clicks: totalClicks, total_impressions: totalImpressions } = searchAppearanceData;
    const aiRows = types.filter(row => row.is_ai_related_hint);
    const topCtrRow = [...types].sort((a, b) => b.ctr - a.ctr)[0];
    const topImpressionRow = [...types].sort((a, b) => b.impressions - a.impressions)[0];
    const aiClicks = aiRows.reduce((sum, row) => sum + row.clicks, 0);
    const aiClickShare = totalClicks > 0 ? (aiClicks / totalClicks * 100) : 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? '16px' : '24px' }}>
            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? 'calc(50% - 4px) calc(50% - 4px)' : 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: isMobile ? '8px' : '16px'
            }}>
                <div style={cardStyle}>
                    <div style={cardLabelStyle}>{t('搜尋外觀類型數', 'Appearance Types')}</div>
                    <div style={cardValueStyle}>{types.length}</div>
                </div>
                <div style={cardStyle}>
                    <div style={cardLabelStyle}>{t('最高 CTR 搜尋外觀', 'Highest CTR Appearance')}</div>
                    <div style={cardValueStyle}>{topCtrRow ? `${(topCtrRow.ctr * 100).toFixed(2)}%` : '-'}</div>
                    {topCtrRow && (
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                            {topCtrRow.search_appearance}
                        </div>
                    )}
                </div>
                <div style={cardStyle}>
                    <div style={cardLabelStyle}>{t('最大曝光搜尋外觀', 'Largest Impression Appearance')}</div>
                    <div style={cardValueStyle}>{topImpressionRow ? topImpressionRow.impressions.toLocaleString() : '-'}</div>
                    {topImpressionRow && (
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                            {topImpressionRow.search_appearance}
                        </div>
                    )}
                </div>
                <div style={{ ...cardStyle, background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05))' }}>
                    <div style={cardLabelStyle}>🪄 {t('疑似 AI Overview 點擊占比', 'AI Overview Click Share (hint)')}</div>
                    <div style={{ ...cardValueStyle, color: '#8B5CF6' }}>
                        {aiRows.length > 0 ? `${aiClickShare.toFixed(2)}%` : t('尚無資料', 'No data')}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {t('關鍵字比對提示，非官方分類', 'Keyword-hint only, not an official category')}
                    </div>
                </div>
            </div>

            <div style={tableContainerStyle}>
                <div style={tableHeaderStyle}>
                    <span>🎨 {t('搜尋外觀成效', 'Search Appearance Performance')} ({types.length})</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 'normal' }}>
                        {t(
                            `全站總計：${totalClicks.toLocaleString()} 點擊 / ${totalImpressions.toLocaleString()} 曝光`,
                            `Site total: ${totalClicks.toLocaleString()} clicks / ${totalImpressions.toLocaleString()} impressions`
                        )}
                    </span>
                </div>
                <div style={tableScrollStyle}>
                    <table style={tableStyle}>
                        <thead>
                            <tr style={{ background: 'var(--bg-hover)' }}>
                                <th style={thStyle}>{t('搜尋外觀', 'Search Appearance')}</th>
                                <th style={thStyle}>{t('點擊', 'Clicks')}</th>
                                <th style={thStyle}>{t('曝光', 'Impressions')}</th>
                                <th style={thStyle}>{t('點閱率', 'CTR')}</th>
                                <th style={thStyle}>{t('平均排名', 'Avg Position')}</th>
                                <th style={thStyle}>{t('點擊占比', 'Click Share')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {types.map((row, idx) => (
                                <tr
                                    key={idx}
                                    style={{ transition: 'background 0.2s' }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                >
                                    <td style={tdStyle}>
                                        {row.is_ai_related_hint && <span title={t('關鍵字比對提示，非官方分類', 'Keyword-hint only, not an official category')} style={{ marginRight: '6px' }}>🪄</span>}
                                        {row.search_appearance}
                                    </td>
                                    <td style={{ ...tdStyle, fontWeight: '600', color: 'var(--accent-primary)' }}>
                                        {row.clicks.toLocaleString()}
                                    </td>
                                    <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                    <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                    <td style={tdStyle}>{row.position.toFixed(1)}</td>
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
                                                    width: `${Math.min(row.click_share * 100, 100)}%`,
                                                    height: '100%',
                                                    background: 'var(--accent-primary)',
                                                    borderRadius: '4px'
                                                }} />
                                            </div>
                                            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                {(row.click_share * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default SearchAppearanceTab;
