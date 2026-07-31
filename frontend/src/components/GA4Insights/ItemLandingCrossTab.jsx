import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    TablePager,
    badgeStyle,
    baseCardStyle,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
} from './GA4InsightsShared';

const ITEM_LANDING_PAGE_SIZE = 25;

// docs/57：跟上一期比較開啟時，讓使用者依「單一指標」的漲跌篩選表格列，
// 比照到達頁/商品分頁（docs/55）同一套邏輯。
const ITEM_LANDING_GROWTH_METRIC_OPTIONS = [
    { value: 'purchase_to_view_rate', field: 'purchase_to_view_rate_delta_pp', labelEn: 'Item purchase rate', labelZh: '商品購買率' },
    { value: 'page_session_key_event_rate', field: 'page_session_key_event_rate_delta_pp', labelEn: 'Page conversion rate', labelZh: '到達頁轉換率' },
    { value: 'page_sessions', field: 'page_sessions_growth_rate', labelEn: 'Page sessions', labelZh: '到達頁工作階段' },
];

// docs/56：跟上一期比較開啟時，告訴 AI 現在看到的數字已經有比較資訊可以提。
const compareScopeLabel = (payload, t) => {
    if (!payload?.compare_enabled) return null;
    if (payload.item_compare_query_error && payload.landing_compare_query_error) return null;
    return t(
        `compared to prior period (${payload.compare_start_date} ~ ${payload.compare_end_date})`,
        `已啟用上一期比較（${payload.compare_start_date} ~ ${payload.compare_end_date}）`
    );
};

// docs/56：次數類指標（到達頁工作階段）用相對成長率；比率類指標（商品購買率/
// 到達頁轉換率）改用百分點差異，跟到達頁/商品分頁同一套邏輯，pp 加滑鼠提示。
const GrowthBadge = ({ value, isPercentagePoint = false, t }) => {
    if (value == null) return null;
    const arrow = value > 0 ? '▲' : value < 0 ? '▼' : '';
    const color = value > 0 ? '#34d399' : value < 0 ? '#f87171' : 'var(--text-tertiary)';
    const magnitude = Math.abs(value);
    const text = isPercentagePoint ? `${magnitude.toFixed(1)}pp` : `${(magnitude * 100).toFixed(0)}%`;
    const title = isPercentagePoint
        ? t(
            'pp = percentage point, the absolute gap vs. the prior period (e.g. a rate going from 5% to 6% is +1.0pp, not a 20% increase).',
            'pp＝百分點，是跟上一期的絕對差距（例如比率從 5% 變 6% 是 +1.0pp，不是成長 20%）。'
        )
        : undefined;
    return (
        <span style={{ fontSize: '0.72rem', marginLeft: '4px', color, whiteSpace: 'nowrap', cursor: isPercentagePoint ? 'help' : 'default' }} title={title}>
            {arrow}{text}
        </span>
    );
};

const ItemLandingCrossTab = ({
    language,
    t,
    propertyId,
    itemLandingDays,
    setItemLandingDays,
    loadItemLandingCross,
    itemLandingError,
    itemLandingLoading,
    itemLandingSnapshot,
    itemLandingCompareEnabled,
    setItemLandingCompareEnabled,
    DaySelector,
}) => {
    const [page, setPage] = useState(1);
    // docs/57：指標＋方向兩個下拉，只有 itemLandingCompareEnabled 時才顯示/生效。
    const [itemLandingGrowthMetric, setItemLandingGrowthMetric] = useState('');
    const [itemLandingGrowthDirection, setItemLandingGrowthDirection] = useState('all');

    const rows = useMemo(() => {
        const growthField = ITEM_LANDING_GROWTH_METRIC_OPTIONS.find((m) => m.value === itemLandingGrowthMetric)?.field;
        return [...(itemLandingSnapshot?.payload?.items || [])]
            .filter((row) => {
                if (!itemLandingCompareEnabled || !growthField || itemLandingGrowthDirection === 'all') return true;
                // 商品購買率的新商品、或到達頁欄位缺上一期資料時，該指標值是 null，方向篩選下一律排除。
                if (row[growthField] == null) return false;
                if (itemLandingGrowthDirection === 'up') return row[growthField] > 0;
                if (itemLandingGrowthDirection === 'down') return row[growthField] < 0;
                return row[growthField] === 0;
            })
            .sort((a, b) => (b.itemsViewed || 0) - (a.itemsViewed || 0));
    }, [itemLandingSnapshot, itemLandingCompareEnabled, itemLandingGrowthMetric, itemLandingGrowthDirection]);

    const totalPages = Math.max(1, Math.ceil(rows.length / ITEM_LANDING_PAGE_SIZE));
    const pageClamped = Math.min(page, totalPages);
    const pagedRows = rows.slice((pageClamped - 1) * ITEM_LANDING_PAGE_SIZE, pageClamped * ITEM_LANDING_PAGE_SIZE);

    useEffect(() => {
        setPage(1);
    }, [itemLandingGrowthMetric, itemLandingGrowthDirection, itemLandingSnapshot?.snapshot_id]);

    return (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Item x Landing Page', '商品頁面比對')}</div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                    {t(
                                        'Each item is matched to its highest-traffic landing page, so you can see the item\'s own purchase rate next to that page\'s conversion rate.',
                                        '每個商品配對瀏覽量最高的到達頁，讓「商品本身的購買率」跟「該到達頁的轉換率」放在一起比較。'
                                    )}
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                {/* docs/56：跟上一期比較開關，預設關閉；比較會固定用「本期」算出來的
                                    商品-到達頁配對，上一期不重新判定主要到達頁（見文件說明）。 */}
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={itemLandingCompareEnabled}
                                        onChange={(event) => {
                                            const next = event.target.checked;
                                            setItemLandingCompareEnabled(next);
                                            if (!next) {
                                                // docs/57：關閉比較時重置篩選條件，避免下拉隱藏但殘留舊篩選。
                                                setItemLandingGrowthMetric('');
                                                setItemLandingGrowthDirection('all');
                                            }
                                            loadItemLandingCross(propertyId, itemLandingDays, next);
                                        }}
                                    />
                                    {t('Compare to prior period', '比較上一期')}
                                </label>
                                <DaySelector value={itemLandingDays} onChange={(d) => { setItemLandingDays(d); loadItemLandingCross(propertyId, d); }} />
                            </div>
                        </div>
                        {/* docs/57：指標＋方向篩選只有比較上一期開啟時才顯示，選了「全部」
                            以外的方向會篩掉沒有比較數值的列。 */}
                        {itemLandingCompareEnabled && (
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '12px' }}>
                                <select
                                    value={itemLandingGrowthMetric}
                                    onChange={(event) => setItemLandingGrowthMetric(event.target.value)}
                                    style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                >
                                    <option value="">{t('Growth metric…', '選擇成長指標…')}</option>
                                    {ITEM_LANDING_GROWTH_METRIC_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>{t(option.labelEn, option.labelZh)}</option>
                                    ))}
                                </select>
                                <select
                                    value={itemLandingGrowthDirection}
                                    onChange={(event) => setItemLandingGrowthDirection(event.target.value)}
                                    disabled={!itemLandingGrowthMetric}
                                    style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: itemLandingGrowthMetric ? 1 : 0.6 }}
                                >
                                    <option value="all">{t('All', '全部')}</option>
                                    <option value="up">{t('Up', '上升')}</option>
                                    <option value="flat">{t('Flat', '持平')}</option>
                                    <option value="down">{t('Down', '下降')}</option>
                                </select>
                            </div>
                        )}
                        {itemLandingError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{itemLandingError}</div>}
                        {itemLandingSnapshot?.payload?.compare_enabled && itemLandingSnapshot?.payload?.item_compare_query_error && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'Could not fetch the prior period for item comparison (temporary); item purchase rate comparison unavailable.',
                                    '暫時無法取得上一期商品資料做比較，商品購買率比較暫缺。'
                                )}
                            </div>
                        )}
                        {itemLandingSnapshot?.payload?.compare_enabled && itemLandingSnapshot?.payload?.landing_compare_query_error && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'Could not fetch the prior period for landing page comparison (temporary); page comparison unavailable.',
                                    '暫時無法取得上一期到達頁資料做比較，到達頁比較暫缺。'
                                )}
                            </div>
                        )}
                        {itemLandingSnapshot?.payload?.used_fallback_conversion_metrics && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'GA4 could not return the official purchase rate for this property; showing a locally computed rate instead.',
                                    '此屬性無法取得 GA4 官方購買率，改顯示本地計算的比率。'
                                )}
                            </div>
                        )}
                        {(itemLandingSnapshot?.payload?.mapping_query_error || itemLandingSnapshot?.payload?.landing_query_error) && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'Could not fetch landing page match data from GA4 (temporary), so some items below show no matched page.',
                                    '暫時無法從 GA4 取得商品與到達頁的對照資料，以下部分商品因此顯示「無對應到達頁」（非長期缺資料）。'
                                )}
                            </div>
                        )}
                        {itemLandingLoading && !itemLandingSnapshot ? (
                            emptyState(t('Loading…', '載入資料中…'))
                        ) : rows.length ? (
                            <>
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                                <th style={{ padding: '6px' }}>{t('Item', '商品')}</th>
                                                <th style={{ padding: '6px' }}>{t('Primary landing page', '主要到達頁')}</th>
                                                <th style={{ padding: '6px' }}>{t('Item purchase rate', '商品瀏覽後購買率')}</th>
                                                <th style={{ padding: '6px' }}>{t('Page conversion rate', '到達頁轉換率')}</th>
                                                <th style={{ padding: '6px' }}>{t('Page sessions', '到達頁工作階段')}</th>
                                                <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {pagedRows.map((row) => {
                                                const showItemGrowth = itemLandingSnapshot.payload.compare_enabled
                                                    && !itemLandingSnapshot.payload.item_compare_query_error
                                                    && !row.item_is_new;
                                                const showPageGrowth = itemLandingSnapshot.payload.compare_enabled
                                                    && !itemLandingSnapshot.payload.landing_compare_query_error;
                                                return (
                                                <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                                                    <td
                                                        style={{ padding: '6px', color: 'var(--text-secondary)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                                        title={row.primary_landing_page || ''}
                                                    >
                                                        {row.primary_landing_page || t('No matched page', '無對應到達頁')}
                                                    </td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                        {fmtPct(row.purchase_to_view_rate)}
                                                        {showItemGrowth && <GrowthBadge value={row.purchase_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                                    </td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                        {fmtPct(row.page_session_key_event_rate)}
                                                        {showPageGrowth && <GrowthBadge value={row.page_session_key_event_rate_delta_pp} isPercentagePoint t={t} />}
                                                    </td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                        {fmtNumber(row.page_sessions)}
                                                        {showPageGrowth && <GrowthBadge value={row.page_sessions_growth_rate} t={t} />}
                                                    </td>
                                                    <td style={{ padding: '6px' }}>
                                                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                                            {row.page_underperforms_item && (
                                                                <span style={badgeStyle('flagged')}>{t('Page may be the issue', '頁面可能拖累')}</span>
                                                            )}
                                                            {itemLandingSnapshot.payload.compare_enabled && row.item_is_new && (
                                                                <span style={badgeStyle('flagged')} title={t('No data in the prior period for this item', '上一期沒有這個商品的資料')}>
                                                                    🆕 {t('New', '新')}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                                <TablePager
                                    page={pageClamped}
                                    totalPages={totalPages}
                                    onPageChange={setPage}
                                    language={language}
                                    totalItems={rows.length}
                                />
                            </>
                        ) : (
                            emptyState(t('No data.', '暫無資料。'))
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={itemLandingSnapshot}
                        kind="item_landing_cross"
                        contextLabel={[
                            t(
                                `Property ${propertyId}; period ${itemLandingSnapshot?.payload?.start_date || ''} ~ ${itemLandingSnapshot?.payload?.end_date || ''}`,
                                `屬性 ${propertyId}；期間 ${itemLandingSnapshot?.payload?.start_date || ''} ~ ${itemLandingSnapshot?.payload?.end_date || ''}`
                            ),
                            compareScopeLabel(itemLandingSnapshot?.payload, t),
                        ].filter(Boolean).join('；')}
                        buildPayload={() => ({
                            items: itemLandingSnapshot?.payload?.items || [],
                            // docs/56：每列已經帶有 *_delta_pp/*_growth_rate/item_is_new 欄位，
                            // 這裡額外補上比較期間，AI 才知道「上一期」具體是哪段日期。
                            compare_enabled: itemLandingSnapshot?.payload?.compare_enabled || false,
                            compare_start_date: itemLandingSnapshot?.payload?.compare_start_date || null,
                            compare_end_date: itemLandingSnapshot?.payload?.compare_end_date || null,
                        })}
                    />
    </>
    );
};

export default ItemLandingCrossTab;
