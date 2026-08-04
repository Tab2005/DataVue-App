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
    dayButtonStyle,
    emptyState,
    inputStyle,
    tr,
    LANDING_CATEGORY_LABELS,
    LANDING_CATEGORY_ORDER,
} from '../components/GA4Insights/GA4InsightsShared';
// docs/64：表格主體與警示橫幅跟應用內分頁共用同一份實作。這頁只負責篩選 UI 與
// 版面，欄位/格式化/成長標示一律由共用元件決定，不再有第二套。
import {
    ChannelsTable,
    ItemLandingCrossTable,
    ItemsTable,
    LandingPagesTable,
    PayloadWarnings,
} from '../components/GA4Insights/GA4InsightsTables';

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

const ChannelsSection = ({ language, t, payload }) => {
    const channels = payload?.channels || [];
    if (!channels.length) return emptyState(t('No channel data.', '暫無渠道資料。'));
    return <ChannelsTable language={language} t={t} payload={payload} rows={channels} />;
};

// docs/53：分類篩選預設值來自分享網址的 ?category= 參數（由分享當下畫面
// 選的分類帶過來），但收件人仍可自由點其他分類按鈕切換，不是唯讀的凍結畫面。
const LandingPagesSection = ({ language, t, payload, initialCategory }) => {
    const allRows = payload?.landing_pages || [];
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
                        : tr(language, LANDING_CATEGORY_LABELS[cat].en, LANDING_CATEGORY_LABELS[cat].zh);
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
            {rows.length === 0
                ? emptyState(t('No landing page data.', '暫無到達頁資料。'))
                : <LandingPagesTable language={language} t={t} payload={payload} rows={rows} />}
        </div>
    );
};

// docs/53：商品分類是依 GA4 實際分類/自訂規則動態產生的清單（不像到達頁固定
// 4 種），選單選項直接從 payload.category_counts 的 key 產生；預設值來自分享
// 網址的 ?category= 參數，收件人仍可自由切換看其他分類。
const ItemsSection = ({ language, t, payload, initialCategory }) => {
    const allRows = payload?.items || [];
    const categoryCounts = payload?.category_counts || {};
    const categoryKeys = Object.keys(categoryCounts);
    const [category, setCategory] = useState(
        categoryKeys.includes(initialCategory) ? initialCategory : 'all'
    );
    const rows = category === 'all' ? allRows : allRows.filter((row) => row.item_category === category);

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
            {rows.length === 0
                ? emptyState(t('No item data.', '暫無商品資料。'))
                : <ItemsTable language={language} t={t} payload={payload} rows={rows} />}
        </div>
    );
};

const ItemLandingCrossSection = ({ t, payload }) => {
    const rows = payload?.items || [];
    if (!rows.length) return emptyState(t('No data.', '暫無資料。'));
    return <ItemLandingCrossTable t={t} payload={payload} rows={rows} />;
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
                    {/* docs/64：資料抓取失敗/截斷的但書。分享頁過去只有兩條，收件人
                        會看到沒有註腳的數字（例如「全部未分類」其實是抓取失敗）。 */}
                    <PayloadWarnings t={t} payload={payload} kind={group} />
                    {group === 'daily_channel' && <ChannelsSection language={language} t={t} payload={payload} />}
                    {group === 'landing_page' && <LandingPagesSection language={language} t={t} payload={payload} initialCategory={initialCategory} />}
                    {group === 'item' && <ItemsSection language={language} t={t} payload={payload} initialCategory={initialCategory} />}
                    {group === 'item_landing_cross' && <ItemLandingCrossSection t={t} payload={payload} />}
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
