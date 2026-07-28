import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    TablePager,
    badgeStyle,
    baseCardStyle,
    emptyState,
    fmtNumber,
    fmtPct,
} from './GA4InsightsShared';

const ITEM_LANDING_PAGE_SIZE = 25;

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
    DaySelector,
}) => {
    const [page, setPage] = useState(1);

    const rows = useMemo(() => (
        [...(itemLandingSnapshot?.payload?.items || [])].sort((a, b) => (b.itemsViewed || 0) - (a.itemsViewed || 0))
    ), [itemLandingSnapshot]);

    const totalPages = Math.max(1, Math.ceil(rows.length / ITEM_LANDING_PAGE_SIZE));
    const pageClamped = Math.min(page, totalPages);
    const pagedRows = rows.slice((pageClamped - 1) * ITEM_LANDING_PAGE_SIZE, pageClamped * ITEM_LANDING_PAGE_SIZE);

    useEffect(() => {
        setPage(1);
    }, [itemLandingSnapshot?.snapshot_id]);

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
                            <DaySelector value={itemLandingDays} onChange={(d) => { setItemLandingDays(d); loadItemLandingCross(propertyId, d); }} />
                        </div>
                        {itemLandingError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{itemLandingError}</div>}
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
                                            {pagedRows.map((row) => (
                                                <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                                                    <td
                                                        style={{ padding: '6px', color: 'var(--text-secondary)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                                        title={row.primary_landing_page || ''}
                                                    >
                                                        {row.primary_landing_page || t('No matched page', '無對應到達頁')}
                                                    </td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.purchase_to_view_rate)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.page_session_key_event_rate)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.page_sessions)}</td>
                                                    <td style={{ padding: '6px' }}>
                                                        {row.page_underperforms_item && (
                                                            <span style={badgeStyle('flagged')}>{t('Page may be the issue', '頁面可能拖累')}</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <TablePager
                                    page={pageClamped}
                                    totalPages={totalPages}
                                    onPageChange={setPage}
                                    language={language}
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
                        contextLabel={t(
                            `Property ${propertyId}; period ${itemLandingSnapshot?.payload?.start_date || ''} ~ ${itemLandingSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；期間 ${itemLandingSnapshot?.payload?.start_date || ''} ~ ${itemLandingSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({
                            items: itemLandingSnapshot?.payload?.items || [],
                        })}
                    />
    </>
    );
};

export default ItemLandingCrossTab;
