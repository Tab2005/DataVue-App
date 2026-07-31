// frontend/src/pages/SharedGA4Insight.jsx (docs/39)
import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { FiAlertCircle, FiZap } from 'react-icons/fi';

import { ga4InsightsService } from '../services/ga4InsightsService';
import PageLoading from '../components/PageLoading';
import {
    badgeStyle,
    dayButtonStyle,
    emptyState,
    inputStyle,
    tr,
    fmtNumber,
    fmtPct,
    CHANNEL_TAG_LABELS,
    ATTRIBUTION_MODEL_LABELS,
    channelClosingLabel,
    channelDimensionLabel,
    LANDING_CATEGORY_LABELS,
    LANDING_CATEGORY_ORDER,
    ITEM_CATEGORY_SOURCE_LABELS,
} from '../components/GA4Insights/GA4InsightsShared';

const KIND_LABELS = {
    daily_channel: { en: 'Channel Comparison', zh: '渠道對照' },
    landing_page: { en: 'Landing Pages', zh: '到達頁' },
    item: { en: 'Items', zh: '商品' },
    item_landing_cross: { en: 'Item x Landing Page', zh: '商品頁面比對' },
};

const kindGroup = (kind) => {
    if (!kind) return null;
    if (kind === 'item_landing_cross') return 'item_landing_cross';
    if (kind.startsWith('landing_page')) return 'landing_page';
    if (kind.startsWith('item')) return 'item';
    if (kind === 'daily_channel') return 'daily_channel';
    return null;
};

const ChannelsTable = ({ language, t, payload }) => {
    const channels = payload?.channels || [];
    if (!channels.length) return emptyState(t('No channel data.', '暫無渠道資料。'));
    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                    <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                        <th style={{ padding: '6px' }}>{channelDimensionLabel(payload.dimension, language)}</th>
                        <th style={{ padding: '6px' }}>{t('Assisting', '開發')}</th>
                        <th style={{ padding: '6px' }}>{channelClosingLabel(payload.attribution_model, language)}</th>
                        <th style={{ padding: '6px' }}>{t('Ratio', '比例')}</th>
                        <th style={{ padding: '6px' }}>{t('Tag', '標籤')}</th>
                    </tr>
                </thead>
                <tbody>
                    {channels.map((row) => (
                        <tr key={row.channel} style={{ borderTop: '1px solid var(--glass-border)' }}>
                            <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.channel}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.assisting_conversions)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.closing_conversions)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{row.ratio != null ? row.ratio.toFixed(2) : '--'}</td>
                            <td style={{ padding: '6px' }}>
                                <span style={badgeStyle(row.tag)}>
                                    {tr(language, CHANNEL_TAG_LABELS[row.tag]?.en, CHANNEL_TAG_LABELS[row.tag]?.zh) || row.tag}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

// docs/54：跟到達頁/商品分頁同一套成長標示邏輯——次數/金額類指標用相對成長
// 率，比率類指標用百分點差異（pp），滑鼠提示說明 pp 的意思。
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

// docs/53：分類篩選預設值來自分享網址的 ?category= 參數（由分享當下畫面
// 選的分類帶過來），但收件人仍可自由點其他分類按鈕切換，不是唯讀的凍結畫面。
const LandingPagesTable = ({ t, payload, initialCategory }) => {
    const allRows = payload?.landing_pages || [];
    const showCompare = payload?.compare_enabled && !payload?.compare_query_error;
    const [category, setCategory] = useState(
        LANDING_CATEGORY_ORDER.includes(initialCategory) ? initialCategory : 'all'
    );
    const rows = category === 'all' ? allRows : allRows.filter((row) => row.category === category);

    if (!allRows.length) return emptyState(t('No landing page data.', '暫無到達頁資料。'));

    return (
        <div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                {['all', ...LANDING_CATEGORY_ORDER].map((cat) => {
                    const count = cat === 'all' ? allRows.length : (payload.category_counts?.[cat] || 0);
                    const label = cat === 'all'
                        ? t('All', '全部')
                        : tr('zh', LANDING_CATEGORY_LABELS[cat].en, LANDING_CATEGORY_LABELS[cat].zh);
                    return (
                        <button
                            key={cat}
                            type="button"
                            style={dayButtonStyle(category === cat)}
                            onClick={() => setCategory(cat)}
                        >
                            {label} ({count})
                        </button>
                    );
                })}
            </div>
            {payload?.compare_enabled && payload?.compare_query_error && (
                <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                    {t(
                        'Could not fetch the prior period for comparison (temporary); showing this period only.',
                        '暫時無法取得上一期資料做比較，以下僅顯示本期數字。'
                    )}
                </div>
            )}
            {rows.length === 0 ? emptyState(t('No landing page data.', '暫無到達頁資料。')) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                        <thead>
                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                <th style={{ padding: '6px' }}>{t('Landing Page', '到達頁')}</th>
                                <th style={{ padding: '6px' }}>{t('Category', '分類')}</th>
                                <th style={{ padding: '6px' }}>{t('Sessions', '工作階段')}</th>
                                <th style={{ padding: '6px' }}>{t('Conversions', '轉換')}</th>
                                <th style={{ padding: '6px' }}>{t('Key Event Rate', '轉換率')}</th>
                                <th style={{ padding: '6px' }}>{t('Bounce Rate', '跳出率')}</th>
                                <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((row) => {
                                const showGrowth = showCompare && !row.is_new;
                                return (
                                <tr key={row.landingPage} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                    <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                        {row.landingPage}
                                    </td>
                                    <td style={{ padding: '6px' }}>
                                        <span style={badgeStyle(row.category)}>
                                            {tr('zh', LANDING_CATEGORY_LABELS[row.category]?.en, LANDING_CATEGORY_LABELS[row.category]?.zh) || row.category}
                                        </span>
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtNumber(row.sessions)}
                                        {showGrowth && <GrowthBadge value={row.sessions_growth_rate} t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtNumber(row.conversions)}
                                        {showGrowth && <GrowthBadge value={row.conversions_growth_rate} t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtPct(row.session_key_event_rate)}
                                        {showGrowth && <GrowthBadge value={row.session_key_event_rate_delta_pp} isPercentagePoint t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtPct(row.bounceRate)}
                                        {showGrowth && <GrowthBadge value={row.bounce_rate_delta_pp} isPercentagePoint t={t} />}
                                    </td>
                                    <td style={{ padding: '6px' }}>
                                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                            {row.is_high_traffic_low_conversion && (
                                                <span style={badgeStyle('flagged')}>{t('High traffic, low conversion', '高流量低轉換')}</span>
                                            )}
                                            {showCompare && row.is_new && (
                                                <span style={badgeStyle('flagged')} title={t('No data in the prior period', '上一期沒有這個頁面的資料')}>
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
            )}
        </div>
    );
};

// docs/53：商品分類是依 GA4 實際分類/自訂規則動態產生的清單（不像到達頁固定
// 4 種），選單選項直接從 payload.category_counts 的 key 產生；預設值來自分享
// 網址的 ?category= 參數，收件人仍可自由切換看其他分類。
const ItemsTable = ({ t, payload, initialCategory }) => {
    const allRows = payload?.items || [];
    const categoryCounts = payload?.category_counts || {};
    const categoryKeys = Object.keys(categoryCounts);
    const [category, setCategory] = useState(
        categoryKeys.includes(initialCategory) ? initialCategory : 'all'
    );
    const rows = category === 'all' ? allRows : allRows.filter((row) => row.item_category === category);
    const showCompare = payload?.compare_enabled && !payload?.compare_query_error;

    if (!allRows.length) return emptyState(t('No item data.', '暫無商品資料。'));

    return (
        <div>
            <div style={{ marginBottom: '12px' }}>
                <select
                    value={category}
                    onChange={(event) => setCategory(event.target.value)}
                    style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                >
                    <option value="all">{t('All categories', '全部分類')} ({allRows.length})</option>
                    {categoryKeys.map((cat) => (
                        <option key={cat} value={cat}>
                            {cat === '(not set)' ? t('Uncategorized', '未分類') : cat} ({categoryCounts[cat]})
                        </option>
                    ))}
                </select>
            </div>
            {payload?.compare_enabled && payload?.compare_query_error && (
                <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                    {t(
                        'Could not fetch the prior period for comparison (temporary); showing this period only.',
                        '暫時無法取得上一期資料做比較，以下僅顯示本期數字。'
                    )}
                </div>
            )}
            {rows.length === 0 ? emptyState(t('No item data.', '暫無商品資料。')) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                        <thead>
                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                <th style={{ padding: '6px' }}>{t('Item', '商品')}</th>
                                <th style={{ padding: '6px' }}>{t('Category', '分類')}</th>
                                <th style={{ padding: '6px' }}>{t('Views', '瀏覽數')}</th>
                                <th style={{ padding: '6px' }}>{t('Add-to-cart Rate', '瀏覽後加購率')}</th>
                                <th style={{ padding: '6px' }}>{t('Purchase Rate', '瀏覽後購買率')}</th>
                                <th style={{ padding: '6px' }}>{t('Revenue', '營收')}</th>
                                <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((row) => {
                                const showGrowth = showCompare && !row.is_new;
                                return (
                                <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }} title={tr('zh', ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.en, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.zh)}>
                                        {row.item_category === '(not set)' ? t('Uncategorized', '未分類') : row.item_category}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtNumber(row.itemsViewed)}
                                        {showGrowth && <GrowthBadge value={row.views_compare_growth_rate} t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtPct(row.cart_to_view_rate)}
                                        {showGrowth && <GrowthBadge value={row.cart_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtPct(row.purchase_to_view_rate)}
                                        {showGrowth && <GrowthBadge value={row.purchase_to_view_rate_delta_pp} isPercentagePoint t={t} />}
                                    </td>
                                    <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                        {fmtNumber(row.itemRevenue)}
                                        {showGrowth && <GrowthBadge value={row.revenue_growth_rate} t={t} />}
                                    </td>
                                    <td style={{ padding: '6px' }}>
                                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                            {row.is_potential && <span style={badgeStyle('potential')}>{t('Potential', '潛力商品')}</span>}
                                            {showCompare && row.is_new && (
                                                <span style={badgeStyle('flagged')} title={t('No data in the prior period', '上一期沒有這個商品的資料')}>
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
            )}
        </div>
    );
};

const ItemLandingCrossTable = ({ t, payload }) => {
    const rows = payload?.items || [];
    if (!rows.length) return emptyState(t('No data.', '暫無資料。'));
    const showItemGrowthBase = payload?.compare_enabled && !payload?.item_compare_query_error;
    const showPageGrowth = payload?.compare_enabled && !payload?.landing_compare_query_error;
    return (
        <div>
            {payload?.compare_enabled && payload?.item_compare_query_error && (
                <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                    {t(
                        'Could not fetch the prior period for item comparison (temporary); item purchase rate comparison unavailable.',
                        '暫時無法取得上一期商品資料做比較，商品購買率比較暫缺。'
                    )}
                </div>
            )}
            {payload?.compare_enabled && payload?.landing_compare_query_error && (
                <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                    {t(
                        'Could not fetch the prior period for landing page comparison (temporary); page comparison unavailable.',
                        '暫時無法取得上一期到達頁資料做比較，到達頁比較暫缺。'
                    )}
                </div>
            )}
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
                        {rows.map((row) => {
                            const showItemGrowth = showItemGrowthBase && !row.item_is_new;
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
                                        {payload?.compare_enabled && row.item_is_new && (
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
        </div>
    );
};

const SharedGA4Insight = () => {
    const { token } = useParams();
    // docs/53：分享網址可能帶 ?category= 參數（產生連結當下畫面選的分類），
    // 當作到達頁/商品表格的預設篩選值；表格元件自己驗證合法性，這裡只負責讀取。
    const [searchParams] = useSearchParams();
    const initialCategory = searchParams.get('category') || 'all';
    const [snapshot, setSnapshot] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const language = 'zh';
    const t = (en, zh) => tr(language, en, zh);

    useEffect(() => {
        const fetchShared = async () => {
            if (!token) return;
            try {
                const res = await ga4InsightsService.getSharedSnapshot(token);
                setSnapshot(res);
            } catch (err) {
                console.error('Failed to fetch shared GA4 insight:', err);
                setError(t('This link is invalid or no longer available.', '此連結已失效或不存在。'));
            } finally {
                setLoading(false);
            }
        };
        fetchShared();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    if (loading) return <PageLoading />;

    if (error || !snapshot) {
        return (
            <div style={{
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                padding: '20px',
                textAlign: 'center',
            }}>
                <FiAlertCircle size={64} color="#ef4444" style={{ marginBottom: '20px' }} />
                <h1 style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{t('Not Found', '找不到此內容')}</h1>
                <p style={{ color: 'var(--text-secondary)', maxWidth: '400px' }}>{error}</p>
            </div>
        );
    }

    const group = kindGroup(snapshot.kind);
    const kindLabel = KIND_LABELS[group] ? tr(language, KIND_LABELS[group].en, KIND_LABELS[group].zh) : snapshot.kind;
    const payload = snapshot.payload || {};
    const period = payload.start_date && payload.end_date ? `${payload.start_date} ~ ${payload.end_date}` : snapshot.date;

    return (
        <div style={{
            minHeight: '100vh',
            backgroundColor: 'var(--bg-primary)',
            backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)',
            padding: '40px 20px',
            color: 'var(--text-primary)',
        }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px', paddingBottom: '20px', borderBottom: '1px solid var(--glass-border)', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <FiZap color="white" size={24} />
                        </div>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-primary)', letterSpacing: '1px' }}>DATAVUE</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px', marginLeft: 'auto' }}>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            {t('GA4 Conversion Insights', 'GA4 轉換洞察')}
                        </span>
                        {snapshot.property_id && (
                            <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>
                                {t(`GA4 property ${snapshot.property_id}`, `GA4 屬性 ${snapshot.property_id}`)}
                            </span>
                        )}
                    </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                    <h1 style={{ fontSize: '1.8rem', marginBottom: '6px' }}>{kindLabel}</h1>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{period}</div>
                </div>

                {snapshot.ai_summary && (
                    <div style={{
                        background: 'rgba(59, 130, 246, 0.05)',
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                        borderRadius: '12px',
                        padding: '18px 20px',
                        marginBottom: '24px',
                        lineHeight: 1.7,
                    }}>
                        <div style={{ fontWeight: 700, marginBottom: '8px' }}>{t('AI Plain-Language Insights', 'AI 白話解讀')}</div>
                        <div className="report-ai-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                {snapshot.ai_summary}
                            </ReactMarkdown>
                        </div>
                    </div>
                )}

                <section style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '14px',
                    padding: '20px',
                }}>
                    {group === 'daily_channel' && <ChannelsTable language={language} t={t} payload={payload} />}
                    {group === 'landing_page' && <LandingPagesTable t={t} payload={payload} initialCategory={initialCategory} />}
                    {group === 'item' && <ItemsTable t={t} payload={payload} initialCategory={initialCategory} />}
                    {group === 'item_landing_cross' && <ItemLandingCrossTable t={t} payload={payload} />}
                    {!group && emptyState(t('Unsupported content type.', '不支援的內容類型。'))}
                </section>

                <div style={{ marginTop: '60px', textAlign: 'center', padding: '40px 0', borderTop: '1px solid var(--glass-border)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    © {new Date().getFullYear()} DataVue Analytics. {t('All rights reserved.', '保留所有權利。')}
                </div>
            </div>
        </div>
    );
};

export default SharedGA4Insight;
