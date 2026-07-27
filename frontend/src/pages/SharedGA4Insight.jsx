// frontend/src/pages/SharedGA4Insight.jsx (docs/39)
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { FiAlertCircle, FiZap } from 'react-icons/fi';

import { ga4InsightsService } from '../services/ga4InsightsService';
import PageLoading from '../components/PageLoading';
import {
    badgeStyle,
    emptyState,
    tr,
    fmtNumber,
    fmtPct,
    CHANNEL_TAG_LABELS,
    ATTRIBUTION_MODEL_LABELS,
    channelClosingLabel,
    channelDimensionLabel,
    LANDING_CATEGORY_LABELS,
    ITEM_CATEGORY_SOURCE_LABELS,
} from '../components/GA4Insights/GA4InsightsShared';

const KIND_LABELS = {
    daily_channel: { en: 'Channel Comparison', zh: '渠道對照' },
    landing_page: { en: 'Landing Pages', zh: '到達頁' },
    item: { en: 'Items', zh: '商品' },
};

const kindGroup = (kind) => {
    if (!kind) return null;
    if (kind.startsWith('landing_page')) return 'landing_page';
    if (kind === 'item') return 'item';
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

const LandingPagesTable = ({ t, payload }) => {
    const rows = payload?.landing_pages || [];
    if (!rows.length) return emptyState(t('No landing page data.', '暫無到達頁資料。'));
    return (
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
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.landingPage} style={{ borderTop: '1px solid var(--glass-border)' }}>
                            <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                {row.landingPage}
                            </td>
                            <td style={{ padding: '6px' }}>
                                <span style={badgeStyle(row.category)}>
                                    {tr('zh', LANDING_CATEGORY_LABELS[row.category]?.en, LANDING_CATEGORY_LABELS[row.category]?.zh) || row.category}
                                </span>
                            </td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.sessions)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.conversions)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.session_key_event_rate)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.bounceRate)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const ItemsTable = ({ t, payload }) => {
    const rows = payload?.items || [];
    if (!rows.length) return emptyState(t('No item data.', '暫無商品資料。'));
    return (
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
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                            <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }} title={tr('zh', ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.en, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.zh)}>
                                {row.item_category === '(not set)' ? t('Uncategorized', '未分類') : row.item_category}
                            </td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemsViewed)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.cart_to_view_rate)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.purchase_to_view_rate)}</td>
                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemRevenue)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const SharedGA4Insight = () => {
    const { token } = useParams();
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
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginLeft: 'auto' }}>
                        {t('GA4 Conversion Insights', 'GA4 轉換洞察')}
                    </span>
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
                    {group === 'landing_page' && <LandingPagesTable t={t} payload={payload} />}
                    {group === 'item' && <ItemsTable t={t} payload={payload} />}
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
