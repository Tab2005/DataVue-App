/**
 * 廣告文案庫（docs/73）
 *
 * 類似 Meta 官方廣告檔案庫的卡片牆，但資料來自團隊自家廣告帳號，
 * 並多了曝光／花費／CTR 可排序。資料讀取走本地快取（/api/ad-library/ads），
 * 「重新抓取」觸發背景刷新後輪詢 job 狀態，完成後重新載入列表。
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiCopy, FiDownload, FiExternalLink, FiImage, FiPlay, FiRefreshCw, FiSearch } from 'react-icons/fi';

import {
    downloadCsv,
    fetchMediaBlobUrl,
    getRefreshJob,
    listAccounts,
    listAds,
    startRefresh,
} from '../services/adLibraryService';

const PAGE_SIZE = 24;
const POLL_INTERVAL_MS = 3000;
const ACTIVE_JOB = new Set(['queued', 'running']);

const t = (language, en, zh) => (language === 'en' ? en : zh);

const STYLES = `
.adlib-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
@media (max-width: 640px) { .adlib-grid { grid-template-columns: 1fr; } }
.adlib-card { background: var(--bg-secondary); border: 1px solid var(--glass-border); border-radius: var(--radius-lg, 12px);
  overflow: hidden; display: flex; flex-direction: column; min-width: 0; }
.adlib-media { position: relative; aspect-ratio: 1 / 1; background: var(--bg-primary); display: flex; align-items: center;
  justify-content: center; color: var(--text-muted); overflow: hidden; }
.adlib-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
.adlib-badge { font-size: 0.72rem; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--glass-border);
  color: var(--text-secondary); white-space: nowrap; }
.adlib-text { white-space: pre-wrap; word-break: break-word; color: var(--text-primary); font-size: 0.9rem; line-height: 1.6; }
.adlib-clamp { display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
.adlib-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 12px; border-radius: var(--radius-md, 8px);
  border: 1px solid var(--glass-border); background: var(--bg-secondary); color: var(--text-primary); cursor: pointer;
  font-size: 0.85rem; }
.adlib-btn:hover:not(:disabled) { background: var(--bg-hover); }
.adlib-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.adlib-btn-primary { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }
.adlib-btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.adlib-input { padding: 8px 10px; border-radius: var(--radius-md, 8px); border: 1px solid var(--glass-border);
  background: var(--bg-secondary); color: var(--text-primary); font-size: 0.85rem; min-width: 0; }
.adlib-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-variant-numeric: tabular-nums; }
.adlib-stats div { font-size: 0.75rem; color: var(--text-muted); }
.adlib-stats strong { display: block; font-size: 0.95rem; color: var(--text-primary); }
`;

const STATUS_LABELS = {
    ACTIVE: ['Active', '投放中'],
    PAUSED: ['Paused', '已暫停'],
    CAMPAIGN_PAUSED: ['Campaign paused', '活動已暫停'],
    ADSET_PAUSED: ['Ad set paused', '廣告組合已暫停'],
    ARCHIVED: ['Archived', '已封存'],
    DELETED: ['Deleted', '已刪除'],
    DISAPPROVED: ['Disapproved', '未通過審查'],
    WITH_ISSUES: ['With issues', '有問題'],
};

const MEDIA_TYPE_LABELS = {
    image: ['Image', '圖片'],
    video: ['Video', '影片'],
    carousel: ['Carousel', '輪播'],
    dynamic: ['Dynamic', '動態創意'],
};

const formatNumber = (n) => new Intl.NumberFormat('zh-TW').format(Math.round(n || 0));
const formatMoney = (n) => new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 }).format(n || 0);
const formatDate = (s) => (s ? new Date(`${s}Z`).toLocaleDateString('zh-TW') : '—');

const MediaThumb = ({ media, mediaType, previewLink, language }) => {
    const first = media?.[0];
    const [src, setSrc] = useState(null);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setSrc(null);
        setFailed(false);
        if (!first?.asset_id) return undefined;
        const controller = new AbortController();
        let objectUrl = null;
        fetchMediaBlobUrl(first.asset_id, controller.signal)
            .then((url) => {
                objectUrl = url;
                setSrc(url);
            })
            .catch((err) => {
                if (err.name !== 'AbortError') setFailed(true);
            });
        return () => {
            controller.abort();
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [first?.asset_id]);

    // 未落地的素材退回 FB CDN 原網址（可能已過期，載入失敗時顯示佔位圖）
    const displaySrc = src || (!first?.asset_id && first?.fb_url) || null;
    const isVideo = mediaType === 'video' || first?.kind === 'video_thumbnail';

    const body = displaySrc && !failed ? (
        <img src={displaySrc} alt="" loading="lazy" onError={() => setFailed(true)} />
    ) : (
        <FiImage size={36} aria-label={t(language, 'No preview', '無預覽')} />
    );

    return (
        <div className="adlib-media">
            {body}
            {isVideo && (
                <span style={{
                    position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    pointerEvents: 'none',
                }}>
                    <span style={{ background: 'rgba(0,0,0,0.55)', borderRadius: '50%', padding: 12, display: 'flex' }}>
                        <FiPlay size={24} color="#fff" />
                    </span>
                </span>
            )}
            {media?.length > 1 && (
                <span className="adlib-badge" style={{
                    position: 'absolute', top: 8, right: 8, background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none',
                }}>
                    1 / {media.length}
                </span>
            )}
            {previewLink && (
                <a
                    href={previewLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={t(language, 'Open preview on Facebook', '在 Facebook 開啟預覽')}
                    style={{ position: 'absolute', inset: 0 }}
                />
            )}
        </div>
    );
};

const AdCard = ({ item, language }) => {
    const [variant, setVariant] = useState(0);
    const [expanded, setExpanded] = useState(false);
    const [copied, setCopied] = useState(false);
    const texts = item.primary_texts || [];
    const text = texts[variant] || '';
    const status = STATUS_LABELS[item.effective_status];
    const mediaType = MEDIA_TYPE_LABELS[item.media_type];

    const handleCopy = async () => {
        const parts = [text, ...(item.headlines || []), ...(item.descriptions || [])].filter(Boolean);
        try {
            await navigator.clipboard.writeText(parts.join('\n\n'));
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            // 剪貼簿權限被拒時不中斷
        }
    };

    return (
        <article className="adlib-card">
            <MediaThumb media={item.media} mediaType={item.media_type} previewLink={item.preview_link} language={language} />
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {status && (
                        <span className="adlib-badge" style={item.effective_status === 'ACTIVE'
                            ? { color: '#16a34a', borderColor: '#16a34a' } : undefined}>
                            {t(language, status[0], status[1])}
                        </span>
                    )}
                    {!status && item.effective_status && <span className="adlib-badge">{item.effective_status}</span>}
                    {mediaType && <span className="adlib-badge">{t(language, mediaType[0], mediaType[1])}</span>}
                    <span className="adlib-badge">{formatDate(item.ad_created_at)}</span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                     title={`${item.campaign_name || ''} › ${item.ad_name || ''}`}>
                    {item.campaign_name || '—'} › {item.ad_name || item.ad_id}
                </div>

                {text ? (
                    <div>
                        <div className={`adlib-text ${expanded ? '' : 'adlib-clamp'}`}>{text}</div>
                        {text.split('\n').length > 5 || text.length > 180 ? (
                            <button type="button" onClick={() => setExpanded((v) => !v)}
                                    style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', padding: '4px 0', fontSize: '0.8rem' }}>
                                {expanded ? t(language, 'Show less', '收合') : t(language, 'Show more', '顯示更多')}
                            </button>
                        ) : null}
                    </div>
                ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{t(language, 'No primary text', '無主要文字')}</div>
                )}

                {texts.length > 1 && (
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t(language, 'Variants', '文案版本')}</span>
                        {texts.map((_, i) => (
                            <button key={i} type="button" onClick={() => { setVariant(i); setExpanded(false); }}
                                    className="adlib-badge"
                                    style={{ cursor: 'pointer', background: i === variant ? 'var(--accent-primary)' : 'transparent', color: i === variant ? '#fff' : undefined }}>
                                {i + 1}
                            </button>
                        ))}
                    </div>
                )}

                {(item.headlines?.length > 0 || item.descriptions?.length > 0) && (
                    <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: 10 }}>
                        {item.headlines?.length > 0 && (
                            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.9rem' }}>{item.headlines.join(' ／ ')}</div>
                        )}
                        {item.descriptions?.length > 0 && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: 2 }}>{item.descriptions.join(' ／ ')}</div>
                        )}
                    </div>
                )}

                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    {(item.cta_types || []).map((cta) => <span key={cta} className="adlib-badge">{cta}</span>)}
                    {item.link_url && (
                        <a href={item.link_url} target="_blank" rel="noopener noreferrer"
                           style={{ fontSize: '0.78rem', color: 'var(--accent-primary)', display: 'inline-flex', alignItems: 'center', gap: 4, minWidth: 0, overflow: 'hidden' }}>
                            <FiExternalLink size={12} style={{ flexShrink: 0 }} />
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.link_url}</span>
                        </a>
                    )}
                </div>

                <div className="adlib-stats" style={{ marginTop: 'auto' }}>
                    <div>{t(language, 'Impressions', '曝光')}<strong>{formatNumber(item.impressions)}</strong></div>
                    <div>{t(language, 'Spend', '花費')}<strong>{formatMoney(item.spend)}</strong></div>
                    <div>CTR<strong>{(item.ctr || 0).toFixed(2)}%</strong></div>
                </div>

                <button type="button" className="adlib-btn" onClick={handleCopy} style={{ justifyContent: 'center' }}>
                    <FiCopy size={14} />
                    {copied ? t(language, 'Copied', '已複製') : t(language, 'Copy text', '複製文案')}
                </button>
            </div>
        </article>
    );
};

const AdLibrary = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();

    const [accounts, setAccounts] = useState([]);
    const [accountsError, setAccountsError] = useState(null);
    const [accountId, setAccountId] = useState('');
    const [status, setStatus] = useState('');
    const [mediaType, setMediaType] = useState('');
    const [query, setQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');
    const [sort, setSort] = useState('impressions');
    const [page, setPage] = useState(1);

    const [data, setData] = useState({ items: [], total: 0, latest_job: null });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [job, setJob] = useState(null);
    const [exporting, setExporting] = useState(false);
    const pollRef = useRef(null);

    useEffect(() => {
        let cancelled = false;
        setAccountsError(null);
        listAccounts()
            .then((list) => {
                if (cancelled) return;
                setAccounts(list || []);
                setAccountId((prev) => (prev && list?.some((a) => a.id === prev) ? prev : list?.[0]?.id || ''));
            })
            .catch((err) => !cancelled && setAccountsError(err.message));
        return () => { cancelled = true; };
    }, [selectedTeamId]);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedQuery(query.trim()), 350);
        return () => clearTimeout(timer);
    }, [query]);

    useEffect(() => { setPage(1); }, [accountId, status, mediaType, debouncedQuery, sort]);

    const loadAds = useCallback(async () => {
        if (!accountId) return;
        setLoading(true);
        setError(null);
        try {
            const res = await listAds({
                accountId, status, mediaType, q: debouncedQuery, sort, order: 'desc', page, pageSize: PAGE_SIZE,
            });
            setData(res);
            setJob((prev) => (prev && ACTIVE_JOB.has(prev.status) ? prev : res.latest_job));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [accountId, status, mediaType, debouncedQuery, sort, page]);

    useEffect(() => { loadAds(); }, [loadAds]);

    // 輪詢刷新任務；完成後重新載入列表
    useEffect(() => {
        clearTimeout(pollRef.current);
        if (!job || !ACTIVE_JOB.has(job.status) || job.account_id !== accountId) return undefined;
        pollRef.current = setTimeout(async () => {
            try {
                const next = await getRefreshJob(job.job_id);
                setJob(next);
                if (!ACTIVE_JOB.has(next.status)) loadAds();
            } catch (err) {
                setError(err.message);
                setJob(null);
            }
        }, POLL_INTERVAL_MS);
        return () => clearTimeout(pollRef.current);
    }, [job, accountId, loadAds]);

    const handleRefresh = async () => {
        setError(null);
        try {
            setJob(await startRefresh(accountId));
        } catch (err) {
            setError(err.message);
        }
    };

    const handleExport = async () => {
        setExporting(true);
        try {
            await downloadCsv({ accountId, status, mediaType, q: debouncedQuery, sort, order: 'desc' });
        } catch (err) {
            setError(err.message);
        } finally {
            setExporting(false);
        }
    };

    const refreshing = job && ACTIVE_JOB.has(job.status) && job.account_id === accountId;
    const totalPages = Math.max(1, Math.ceil((data.total || 0) / PAGE_SIZE));
    const hasFilters = Boolean(status || mediaType || debouncedQuery);

    return (
        <>
            <style>{STYLES}</style>
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={{ marginBottom: 20 }}>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: 8 }}>
                        {t(language, 'Ad Library', '廣告文案庫')}
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)', fontSize: isMobile ? '1.4rem' : undefined }}>
                        {t(language, 'Your ad copy, all in one place', '自家廣告文案總覽')}
                    </h1>
                </div>

                {accountsError && <Notice tone="error">{t(language, 'Failed to load ad accounts: ', '載入廣告帳戶失敗：')}{accountsError}</Notice>}

                <div style={{
                    display: 'grid', gap: 10, marginBottom: 16,
                    gridTemplateColumns: isMobile ? '1fr' : 'minmax(200px, 1.2fr) repeat(3, minmax(120px, 0.8fr)) minmax(180px, 1.4fr)',
                }}>
                    <select className="adlib-input" value={accountId} onChange={(e) => setAccountId(e.target.value)}
                            aria-label={t(language, 'Ad account', '廣告帳戶')}>
                        {accounts.length === 0 && <option value="">{t(language, 'No ad accounts', '沒有可用的廣告帳戶')}</option>}
                        {accounts.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.id})</option>)}
                    </select>
                    <select className="adlib-input" value={status} onChange={(e) => setStatus(e.target.value)}
                            aria-label={t(language, 'Status', '狀態')}>
                        <option value="">{t(language, 'All statuses', '全部狀態')}</option>
                        <option value="active">{t(language, 'Active', '投放中')}</option>
                        <option value="paused">{t(language, 'Paused', '已暫停')}</option>
                        <option value="other">{t(language, 'Other', '其他')}</option>
                    </select>
                    <select className="adlib-input" value={mediaType} onChange={(e) => setMediaType(e.target.value)}
                            aria-label={t(language, 'Media type', '素材類型')}>
                        <option value="">{t(language, 'All media', '全部素材')}</option>
                        {Object.entries(MEDIA_TYPE_LABELS).map(([k, [en, zh]]) => (
                            <option key={k} value={k}>{t(language, en, zh)}</option>
                        ))}
                    </select>
                    <select className="adlib-input" value={sort} onChange={(e) => setSort(e.target.value)}
                            aria-label={t(language, 'Sort by', '排序')}>
                        <option value="impressions">{t(language, 'Most impressions', '曝光最多')}</option>
                        <option value="spend">{t(language, 'Highest spend', '花費最高')}</option>
                        <option value="ctr">{t(language, 'Highest CTR', 'CTR 最高')}</option>
                        <option value="created">{t(language, 'Newest', '最新建立')}</option>
                    </select>
                    <label style={{ position: 'relative', display: 'block' }}>
                        <FiSearch size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input className="adlib-input" type="search" value={query} onChange={(e) => setQuery(e.target.value)}
                               placeholder={t(language, 'Search copy, ad or campaign name', '搜尋文案、廣告或活動名稱')}
                               style={{ width: '100%', paddingLeft: 30, boxSizing: 'border-box' }} />
                    </label>
                </div>

                <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 }}>
                    <button type="button" className="adlib-btn adlib-btn-primary" onClick={handleRefresh}
                            disabled={!accountId || refreshing}>
                        <FiRefreshCw size={14} className={refreshing ? 'spin' : undefined} />
                        {refreshing ? t(language, 'Fetching…', '抓取中…') : t(language, 'Fetch from Facebook', '從 Facebook 重新抓取')}
                    </button>
                    <button type="button" className="adlib-btn" onClick={handleExport}
                            disabled={!accountId || exporting || !data.total}>
                        <FiDownload size={14} />
                        {t(language, 'Export CSV', '匯出 CSV')}
                    </button>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                        <JobStatus job={job} language={language} total={data.total} />
                    </span>
                </div>

                {error && <Notice tone="error">{error}</Notice>}
                {job?.status === 'partial' && job.error && <Notice tone="info">{job.error}</Notice>}
                {job?.status === 'failed' && job.error && (
                    <Notice tone="error">{t(language, 'Last fetch failed: ', '上次抓取失敗：')}{job.error}</Notice>
                )}

                {!loading && accountId && data.items.length === 0 && (
                    <Notice tone="info">
                        {hasFilters
                            ? t(language, 'No ads match these filters.', '沒有符合篩選條件的廣告。')
                            : t(language, 'No ads cached yet. Click "Fetch from Facebook" to build the library.', '尚未抓取資料，請按「從 Facebook 重新抓取」建立文案庫。')}
                    </Notice>
                )}

                <div className="adlib-grid" aria-busy={loading} style={{ opacity: loading ? 0.6 : 1 }}>
                    {data.items.map((item) => <AdCard key={item.id} item={item} language={language} />)}
                </div>

                {data.total > PAGE_SIZE && (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 20 }}>
                        <button type="button" className="adlib-btn" disabled={page <= 1 || loading} onClick={() => setPage((p) => p - 1)}>
                            {t(language, 'Previous', '上一頁')}
                        </button>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{page} / {totalPages}</span>
                        <button type="button" className="adlib-btn" disabled={page >= totalPages || loading} onClick={() => setPage((p) => p + 1)}>
                            {t(language, 'Next', '下一頁')}
                        </button>
                    </div>
                )}
            </div>
        </>
    );
};

const Notice = ({ tone, children }) => (
    <div role={tone === 'error' ? 'alert' : 'status'} style={{
        padding: '10px 14px', borderRadius: 8, marginBottom: 12, fontSize: '0.88rem',
        border: `1px solid ${tone === 'error' ? 'var(--text-error)' : 'var(--glass-border)'}`,
        color: tone === 'error' ? 'var(--text-error)' : 'var(--text-secondary)',
        background: 'var(--bg-secondary)',
    }}>
        {children}
    </div>
);

const JobStatus = ({ job, language, total }) => {
    if (job && ACTIVE_JOB.has(job.status)) {
        return t(language, `Fetched ${job.ads_fetched} ads so far…`, `已抓取 ${job.ads_fetched} 支廣告…`);
    }
    const parts = [t(language, `${total || 0} ads`, `共 ${total || 0} 支廣告`)];
    if (job?.finished_at) {
        parts.push(t(language, `last fetched ${new Date(`${job.finished_at}Z`).toLocaleString()}`,
            `上次抓取 ${new Date(`${job.finished_at}Z`).toLocaleString('zh-TW')}`));
    }
    return parts.join(' · ');
};

export default AdLibrary;
