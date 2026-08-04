// frontend/src/components/GA4Insights/GA4InsightsTables.jsx (docs/64)
//
// 應用內分頁（*Tab.jsx）與分享頁（pages/SharedGA4Insight.jsx）共用的表格主體。
// 在這之前兩邊是各自獨立的實作，靠人工同步欄位，已經實際漏掉過：分享頁少了
// 商品的「瀏覽成長」整欄、少了三種「資料抓取失敗」橫幅（收件人看到未分類/
// 本地估算的數字卻沒有任何但書）。
//
// 這裡的元件是**純呈現層**：吃呼叫端已經篩選 / 排序 / 分頁完的 rows，加上整份
// payload（表頭定義文字、比較開關等列以外的資訊）。篩選 UI、分頁器、載入中與
// 空狀態都留在呼叫端——分享頁只有分類篩選，應用內分頁有一整排條件，那部分本來
// 就不該共用。
import React from 'react';

import {
    ITEM_CATEGORY_SOURCE_LABELS,
    LANDING_CATEGORY_LABELS,
    CHANNEL_TAG_LABELS,
    badgeStyle,
    channelClosingLabel,
    channelDimensionLabel,
    fmtNumber,
    fmtPct,
    tr,
} from './GA4InsightsShared';

const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' };
const headRowStyle = { color: 'var(--text-secondary)', textAlign: 'left' };
const bodyRowStyle = { borderTop: '1px solid var(--glass-border)' };
const thStyle = { padding: '6px' };
const tdPrimary = { padding: '6px', color: 'var(--text-primary)' };
const tdSecondary = { padding: '6px', color: 'var(--text-secondary)' };
const tdNumeric = { padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' };
const flagCellStyle = { display: 'flex', gap: '4px', flexWrap: 'wrap' };
const warningStyle = { color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' };

// docs/54：次數類指標（工作階段/轉換次數/營收）用相對成長率；比率類指標（轉換率/
// 跳出率/加購率）改用百分點差異，避免「5%→6%」被講成「成長20%」造成誤解。pp 是
// percentage point（百分點）的縮寫，不是每個使用者都認得，加 title 滑鼠提示說明
// 清楚，跟畫面上其他 ⓘ 提示同一套「用 cursor: help 提示可以看說明」慣例。
// docs/64：原本應用內三個分頁 + 分享頁各有一份完全相同的實作（docs/59 P2-2），
// 收成這一份。
export const GrowthBadge = ({ value, isPercentagePoint = false, t }) => {
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

const NewRowBadge = ({ t, title }) => (
    <span style={badgeStyle('flagged')} title={title}>
        🆕 {t('New', '新')}
    </span>
);

// docs/64：警示橫幅集中定義。`kinds` 決定哪種快照會檢查該條，`when` 是顯示條件。
// 集中的理由跟表格主體一樣：這些橫幅是數字的但書（「這欄是抓取失敗才全部未分類」
// 「這比率是本地算的不是 GA4 官方值」），分享頁過去少了三條，等於把報表的註腳
// 撕掉再寄出去。之後新增橫幅只要往這張表加一列，兩個表面同時生效。
const PAYLOAD_WARNINGS = [
    {
        id: 'truncated',
        kinds: ['daily_channel'],
        when: (payload) => !!payload.truncated,
        text: (payload, t) => t(
            `Showing top 20 of ${payload.total_row_count} (ranked by assisting + closing conversions).`,
            `顯示前 20 名（依開發+收單轉換數排序），共 ${payload.total_row_count} 個項目。`
        ),
    },
    {
        id: 'compare_query_error',
        kinds: ['landing_page', 'item'],
        when: (payload) => !!payload.compare_enabled && !!payload.compare_query_error,
        text: (payload, t) => t(
            'Could not fetch the prior period for comparison (temporary); showing this period only.',
            '暫時無法取得上一期資料做比較，以下僅顯示本期數字。'
        ),
    },
    {
        id: 'item_compare_query_error',
        kinds: ['item_landing_cross'],
        when: (payload) => !!payload.compare_enabled && !!payload.item_compare_query_error,
        text: (payload, t) => t(
            'Could not fetch the prior period for item comparison (temporary); item purchase rate comparison unavailable.',
            '暫時無法取得上一期商品資料做比較，商品購買率比較暫缺。'
        ),
    },
    {
        id: 'landing_compare_query_error',
        kinds: ['item_landing_cross'],
        when: (payload) => !!payload.compare_enabled && !!payload.landing_compare_query_error,
        text: (payload, t) => t(
            'Could not fetch the prior period for landing page comparison (temporary); page comparison unavailable.',
            '暫時無法取得上一期到達頁資料做比較，到達頁比較暫缺。'
        ),
    },
    {
        id: 'item_fallback_metrics',
        kinds: ['item'],
        when: (payload) => !!payload.used_fallback_conversion_metrics,
        text: (payload, t) => t(
            'GA4 could not return the official cart/purchase rate for this property; showing a locally computed rate instead.',
            '此屬性無法取得 GA4 官方加購/購買率，改顯示本地計算的比率。'
        ),
    },
    {
        id: 'category_breakdown_error',
        kinds: ['item'],
        when: (payload) => !!payload.category_breakdown_error,
        text: (payload, t) => t(
            'Could not fetch item category data from GA4 (temporary), so every item shows "Uncategorized" below.',
            '暫時無法從 GA4 取得商品分類資料，以下商品因此都顯示「未分類」（非您網站真的沒有分類）。'
        ),
    },
    {
        id: 'cross_fallback_metrics',
        kinds: ['item_landing_cross'],
        when: (payload) => !!payload.used_fallback_conversion_metrics,
        text: (payload, t) => t(
            'GA4 could not return the official purchase rate for this property; showing a locally computed rate instead.',
            '此屬性無法取得 GA4 官方購買率，改顯示本地計算的比率。'
        ),
    },
    {
        id: 'landing_match_error',
        kinds: ['item_landing_cross'],
        when: (payload) => !!(payload.mapping_query_error || payload.landing_query_error),
        text: (payload, t) => t(
            'Could not fetch landing page match data from GA4 (temporary), so some items below show no matched page.',
            '暫時無法從 GA4 取得商品與到達頁的對照資料，以下部分商品因此顯示「無對應到達頁」（非長期缺資料）。'
        ),
    },
];

export const PayloadWarnings = ({ t, payload, kind }) => {
    if (!payload) return null;
    const active = PAYLOAD_WARNINGS.filter((warning) => warning.kinds.includes(kind) && warning.when(payload));
    if (!active.length) return null;
    return (
        <>
            {active.map((warning) => (
                <div key={warning.id} style={warningStyle}>{warning.text(payload, t)}</div>
            ))}
        </>
    );
};

export const ChannelsTable = ({ language, t, payload, rows }) => {
    const totalClosing = payload?.total_closing_conversions || 0;
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
                <thead>
                    <tr style={headRowStyle}>
                        <th style={thStyle}>{channelDimensionLabel(payload?.dimension, language)}</th>
                        <th style={thStyle}>{t('Assisting', '開發')}</th>
                        <th style={thStyle}>{channelClosingLabel(payload?.attribution_model, language)}</th>
                        <th style={thStyle}>{t('Ratio', '比例')}</th>
                        <th style={thStyle}>{t('Tag', '標籤')}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.channel} style={bodyRowStyle}>
                            <td style={tdPrimary}>{row.channel}</td>
                            <td style={tdSecondary}>{fmtNumber(row.assisting_conversions)}</td>
                            <td style={tdSecondary}>{fmtNumber(row.closing_conversions)}</td>
                            <td style={tdSecondary}>{row.ratio != null ? row.ratio.toFixed(2) : '--'}</td>
                            <td style={thStyle}>
                                <span style={badgeStyle(row.tag)}>
                                    {tr(language, CHANNEL_TAG_LABELS[row.tag]?.en, CHANNEL_TAG_LABELS[row.tag]?.zh) || row.tag}
                                </span>
                                {totalClosing > 0 && (
                                    <span
                                        style={{ color: 'var(--text-secondary)', fontSize: '0.74rem', marginLeft: '6px' }}
                                        title={t(
                                            'Share of this channel\'s closing conversions out of all channels\' total.',
                                            '這個渠道的收單轉換數，佔全部渠道收單轉換數加總的比例。'
                                        )}
                                    >
                                        ({t('share', '佔收單')} {fmtPct(row.closing_conversions / totalClosing)})
                                    </span>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export const LandingPagesTable = ({ language, t, payload, rows }) => {
    const showCompare = !!payload?.compare_enabled && !payload?.compare_query_error;
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
                <thead>
                    <tr style={headRowStyle}>
                        <th style={thStyle}>{t('Page', '頁面')}</th>
                        <th style={thStyle}>{t('Category', '分類')}</th>
                        <th style={thStyle}>{t('Sessions', '工作階段')}</th>
                        <th style={{ ...thStyle, cursor: 'help' }} title={payload?.key_events_count_definition || ''}>
                            {t('Key events', '轉換次數')} ⓘ
                        </th>
                        <th style={{ ...thStyle, cursor: 'help' }} title={payload?.session_key_event_rate_definition || ''}>
                            {t('Conversion rate', '轉換率')} ⓘ
                        </th>
                        <th style={thStyle}>{t('Bounce rate', '跳出率')}</th>
                        <th style={thStyle}>{t('Flag', '標記')}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => {
                        const showGrowth = showCompare && !row.is_new;
                        return (
                            <tr key={row.landingPage} style={bodyRowStyle}>
                                <td style={{ ...tdPrimary, maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                    {row.landingPage}
                                </td>
                                <td style={thStyle}>
                                    <span style={badgeStyle(row.category)}>
                                        {tr(language, LANDING_CATEGORY_LABELS[row.category]?.en, LANDING_CATEGORY_LABELS[row.category]?.zh) || row.category}
                                    </span>
                                </td>
                                <td style={tdNumeric}>
                                    {fmtNumber(row.sessions)}
                                    {showGrowth && <GrowthBadge value={row.sessions_growth_rate} t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtNumber(row.conversions)}
                                    {showGrowth && <GrowthBadge value={row.conversions_growth_rate} t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.session_key_event_rate)}
                                    {showGrowth && <GrowthBadge value={row.session_key_event_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.bounceRate)}
                                    {showGrowth && <GrowthBadge value={row.bounce_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td style={thStyle}>
                                    <div style={flagCellStyle}>
                                        {row.is_high_traffic_low_conversion && (
                                            <span style={badgeStyle('flagged')}>{t('High traffic, low conversion', '高流量低轉換')}</span>
                                        )}
                                        {showCompare && row.is_new && (
                                            <NewRowBadge t={t} title={t('No data in the prior period', '上一期沒有這個頁面的資料')} />
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

// 靜態表頭：分享頁沒有排序功能，用這個當 renderHeader 的預設值。應用內分頁傳入
// 自己的可排序版本（帶排序箭頭與 onClick），欄位定義仍然只有下面這一份。
const staticHeader = (key, label, tooltip) => (
    <th style={tooltip ? { ...thStyle, cursor: 'help' } : thStyle} title={tooltip || undefined}>
        {label}{tooltip ? ' ⓘ' : ''}
    </th>
);

export const ItemsTable = ({ language, t, payload, rows, renderHeader = staticHeader }) => {
    const showCompare = !!payload?.compare_enabled && !payload?.compare_query_error;
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
                <thead>
                    <tr style={headRowStyle}>
                        {renderHeader('itemName', t('Item', '商品'))}
                        {renderHeader('item_category', t('Category', '分類'))}
                        {renderHeader('itemsViewed', t('Views', '瀏覽'))}
                        {renderHeader('cart_to_view_rate', t('Add-to-cart rate', '瀏覽後加購率'), payload?.cart_to_view_rate_definition || '')}
                        {renderHeader('purchase_to_view_rate', t('Purchase rate', '瀏覽後購買率'), payload?.purchase_to_view_rate_definition || '')}
                        {renderHeader('views_growth_rate', t('View growth', '瀏覽成長'))}
                        {renderHeader('itemRevenue', t('Revenue', '營收'))}
                        <th style={thStyle}>{t('Flag', '標記')}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => {
                        const isNewEntry = row.views_prior_7d === 0 && row.views_recent_7d > 0;
                        const showGrowth = showCompare && !row.is_new;
                        return (
                            <tr key={row.itemName} style={bodyRowStyle}>
                                <td style={tdPrimary}>{row.itemName}</td>
                                <td
                                    style={{ ...tdSecondary, cursor: 'help' }}
                                    title={tr(language, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.en, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.zh)}
                                >
                                    {row.item_category === '(not set)' ? t('Uncategorized', '未分類') : row.item_category}
                                    {row.item_category_source === 'custom_rule' && ' ✎'}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtNumber(row.itemsViewed)}
                                    {showGrowth && <GrowthBadge value={row.views_compare_growth_rate} t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.cart_to_view_rate)}
                                    {showGrowth && <GrowthBadge value={row.cart_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.purchase_to_view_rate)}
                                    {showGrowth && <GrowthBadge value={row.purchase_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td
                                    style={{ ...tdSecondary, cursor: 'help' }}
                                    title={t(
                                        `Last 7 days: ${fmtNumber(row.views_recent_7d)} / Prior 7 days: ${fmtNumber(row.views_prior_7d)}`,
                                        `近 7 天 ${fmtNumber(row.views_recent_7d)} 次 / 前 7 天 ${fmtNumber(row.views_prior_7d)} 次`
                                    )}
                                >
                                    {isNewEntry ? (
                                        <span style={badgeStyle('new_entry')}>{t('New entry', '新進榜')}</span>
                                    ) : (
                                        fmtPct(row.views_growth_rate)
                                    )}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtNumber(row.itemRevenue)}
                                    {showGrowth && <GrowthBadge value={row.revenue_growth_rate} t={t} />}
                                </td>
                                <td style={thStyle}>
                                    <div style={flagCellStyle}>
                                        {row.is_potential && <span style={badgeStyle('potential')}>{t('Potential', '潛力商品')}</span>}
                                        {showCompare && row.is_new && (
                                            <NewRowBadge t={t} title={t('No data in the prior period', '上一期沒有這個商品的資料')} />
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export const ItemLandingCrossTable = ({ t, payload, rows }) => {
    // 商品側與到達頁側的比較資料是兩支獨立查詢，任一支失敗只讓那一側的成長標示
    // 消失，另一側照常顯示（docs/59 列為值得保留的容錯粒度）。
    const showItemGrowthBase = !!payload?.compare_enabled && !payload?.item_compare_query_error;
    const showPageGrowth = !!payload?.compare_enabled && !payload?.landing_compare_query_error;
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
                <thead>
                    <tr style={headRowStyle}>
                        <th style={thStyle}>{t('Item', '商品')}</th>
                        <th style={thStyle}>{t('Primary landing page', '主要到達頁')}</th>
                        <th style={thStyle}>{t('Item purchase rate', '商品瀏覽後購買率')}</th>
                        <th style={thStyle}>{t('Page conversion rate', '到達頁轉換率')}</th>
                        <th style={thStyle}>{t('Page sessions', '到達頁工作階段')}</th>
                        <th style={thStyle}>{t('Flag', '標記')}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => {
                        const showItemGrowth = showItemGrowthBase && !row.item_is_new;
                        return (
                            <tr key={row.itemName} style={bodyRowStyle}>
                                <td style={tdPrimary}>{row.itemName}</td>
                                <td
                                    style={{ ...tdSecondary, maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                    title={row.primary_landing_page || ''}
                                >
                                    {row.primary_landing_page || t('No matched page', '無對應到達頁')}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.purchase_to_view_rate)}
                                    {showItemGrowth && <GrowthBadge value={row.purchase_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtPct(row.page_session_key_event_rate)}
                                    {showPageGrowth && <GrowthBadge value={row.page_session_key_event_rate_delta_pp} isPercentagePoint t={t} />}
                                </td>
                                <td style={tdNumeric}>
                                    {fmtNumber(row.page_sessions)}
                                    {showPageGrowth && <GrowthBadge value={row.page_sessions_growth_rate} t={t} />}
                                </td>
                                <td style={thStyle}>
                                    <div style={flagCellStyle}>
                                        {row.page_underperforms_item && (
                                            <span style={badgeStyle('flagged')}>{t('Page may be the issue', '頁面可能拖累')}</span>
                                        )}
                                        {payload?.compare_enabled && row.item_is_new && (
                                            <NewRowBadge t={t} title={t('No data in the prior period for this item', '上一期沒有這個商品的資料')} />
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
