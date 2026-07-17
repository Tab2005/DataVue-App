import React from 'react';
import { GSCDataLoadingState, GSCErrorState } from './GSCUiStates';
import { SEARCH_APPEARANCE_NAMES } from './constants';

const getAppearanceLabel = (code, language) => {
    const entry = SEARCH_APPEARANCE_NAMES[code];
    if (!entry) return code;
    return language === 'zh' ? entry.zh : entry.en;
};

const SearchAppearanceTab = ({ context }) => {
    const {
        searchAppearanceData,
        searchAppearanceLoading,
        searchAppearanceError,
        t,
        language,
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

    const genAiNotice = (
        <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            background: 'rgba(139, 92, 246, 0.08)',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6
        }}>
            ℹ️ {t(
                'Google 於 2026 年 6 月推出的「生成式 AI 效能報表」（AI Overview／AI Mode 曝光數據）目前僅能在 GSC 後台查看（成效 > 搜尋結果 > 生成式 AI），Google 尚未透過 API 開放這份資料，因此下方數據不包含它，僅為既有「搜尋外觀」（Rich Result 等）的成效明細。',
                'Google\'s "Generative AI performance report" (launched June 2026, covering AI Overviews / AI Mode impressions) is currently only viewable in the Search Console UI (Performance > Search results > Generative AI). Google has not yet exposed this data via the API, so it is NOT included below — this tab only shows the existing "Search appearance" breakdown (rich results, etc.).'
            )}
        </div>
    );

    if (!searchAppearanceData || !searchAppearanceData.has_data) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? '16px' : '24px' }}>
                {genAiNotice}
                <div style={tableContainerStyle}>
                    <div style={tableHeaderStyle}>
                        <span>🎨 {t('搜尋外觀', 'Search Appearance')}</span>
                    </div>
                    <div style={{ padding: '32px 20px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                        {t(
                            '此網站在指定期間內，searchAppearance 維度沒有任何資料。可能是此站台目前沒有任何 Rich Result 等搜尋外觀類型的曝光紀錄。',
                            'No searchAppearance data found for this site in the selected period. This may simply mean the site has no rich-result style impressions yet.'
                        )}
                    </div>
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
            {genAiNotice}

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
                            {getAppearanceLabel(topCtrRow.search_appearance, language)}
                        </div>
                    )}
                </div>
                <div style={cardStyle}>
                    <div style={cardLabelStyle}>{t('最大曝光搜尋外觀', 'Largest Impression Appearance')}</div>
                    <div style={cardValueStyle}>{topImpressionRow ? topImpressionRow.impressions.toLocaleString() : '-'}</div>
                    {topImpressionRow && (
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                            {getAppearanceLabel(topImpressionRow.search_appearance, language)}
                        </div>
                    )}
                </div>
                <div style={{ ...cardStyle, background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05))' }}>
                    <div style={cardLabelStyle}>🪄 {t('關鍵字疑似 AI 相關點擊占比', 'Keyword-Hinted "AI" Click Share')}</div>
                    <div style={{ ...cardValueStyle, color: '#8B5CF6' }}>
                        {aiRows.length > 0 ? `${aiClickShare.toFixed(2)}%` : t('Google 尚未透過 API 開放', 'Not exposed via API yet')}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {t(
                            '僅對 searchAppearance 字串做關鍵字比對，並非 Google 官方的 AI Overview 分類（該分類目前不在 API 資料中）',
                            'Keyword match against searchAppearance strings only — not Google\'s official AI Overview category (which is not in the API data today)'
                        )}
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
                                    <td style={tdStyle} title={row.search_appearance}>
                                        {row.is_ai_related_hint && <span title={t('關鍵字比對提示，非官方分類', 'Keyword-hint only, not an official category')} style={{ marginRight: '6px' }}>🪄</span>}
                                        {getAppearanceLabel(row.search_appearance, language)}
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
