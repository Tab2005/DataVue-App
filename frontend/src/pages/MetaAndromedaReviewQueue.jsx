import React, { useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useModuleAccess } from '../hooks/usePermission';

import {
    batchDeleteMetaAndromedaReviewItems,
    deleteMetaAndromedaReviewItem,
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewQueue,
} from '../services/metaAndromedaReviewQueueService';
import { getDiagnosticLabel, getPerfMetricLabel, formatPerfValue, getPredictedBandLabel } from '../utils/metaAndromedaLabels';

const PAGE_SIZE = 25;

const statusToneMap = {
    completed: 'rgba(16, 185, 129, 0.15)',
    queued: 'rgba(59, 130, 246, 0.15)',
    failed: 'rgba(239, 68, 68, 0.15)',
    processing: 'rgba(245, 158, 11, 0.15)',
};

const roasBandColor = {
    high: '#10b981',
    mid: '#f59e0b',
    low: '#ef4444',
};

const sourceMeta = {
    analytics: {
        bg: 'rgba(59,130,246,0.15)',
        color: '#60a5fa',
    },
    score_lab: {
        bg: 'rgba(139,92,246,0.15)',
        color: '#a78bfa',
    },
};

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const resolvePreviewUrl = (item) => {
    if (!item) return null;
    const url = item.preview_url;
    if (url && (url.startsWith('http') || url.startsWith('/'))) return url;
    if (item.asset_uri) {
        const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
        return `${base}/api/meta-andromeda/assets/preview?uri=${encodeURIComponent(item.asset_uri)}`;
    }
    return null;
};

const Pagination = ({ page, totalPages, onPageChange, t }) => {
    if (totalPages <= 1) return null;

    const pages = [];
    const delta = 2;
    const left = Math.max(1, page - delta);
    const right = Math.min(totalPages, page + delta);

    if (left > 1) { pages.push(1); if (left > 2) pages.push('…'); }
    for (let i = left; i <= right; i++) pages.push(i);
    if (right < totalPages) { if (right < totalPages - 1) pages.push('…'); pages.push(totalPages); }

    return (
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', marginTop: '14px' }}>
            <button
                type="button"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                style={{ ...pagebtnStyle, opacity: page <= 1 ? 0.35 : 1 }}
            >‹</button>
            {pages.map((p, i) =>
                p === '…'
                    ? <span key={`ellipsis-${i}`} style={{ color: 'var(--text-secondary)', padding: '0 4px' }}>…</span>
                    : (
                        <button
                            key={p}
                            type="button"
                            onClick={() => onPageChange(p)}
                            style={{
                                ...pagebtnStyle,
                                background: p === page ? 'var(--accent-primary)' : 'rgba(255,255,255,0.04)',
                                color: p === page ? '#fff' : 'var(--text-primary)',
                                borderColor: p === page ? 'var(--accent-primary)' : 'var(--glass-border)',
                                fontWeight: p === page ? 700 : 400,
                            }}
                        >{p}</button>
                    )
            )}
            <button
                type="button"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                style={{ ...pagebtnStyle, opacity: page >= totalPages ? 0.35 : 1 }}
            >›</button>
        </div>
    );
};

const MetaAndromedaReviewQueue = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('meta_andromeda', selectedTeamId);

    const [statusFilter, setStatusFilter] = useState('completed');
    const [observationFilter, setObservationFilter] = useState('all');
    const [roasBandFilter, setRoasBandFilter] = useState('all');
    const [sourceFilter, setSourceFilter] = useState('all');
    const [scoringEngineFilter, setScoringEngineFilter] = useState('all');
    const [deletingId, setDeletingId] = useState(null);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [batchDeleting, setBatchDeleting] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    const [queueItems, setQueueItems] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loadingQueue, setLoadingQueue] = useState(true);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const searchTimerRef = useRef(null);

    const t = (en, zh) => (language === 'en' ? en : zh);

    const getStatusLabel = (key) => {
        switch (String(key).toLowerCase()) {
            case 'completed': return t('Completed', '已完成');
            case 'failed': return t('Failed', '失敗');
            case 'pending': return t('Pending', '待處理');
            case 'processing': return t('Processing', '處理中');
            case 'queued': return t('Queued', '排隊中');
            default: return key;
        }
    };

    const loadQueue = async (targetPage = 1, searchValue = searchTerm) => {
        setLoadingQueue(true);
        setError(null);
        try {
            const has_observation =
                observationFilter === 'matched' ? true
                : observationFilter === 'unmatched' ? false
                : null;
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                has_observation,
                roas_band: roasBandFilter === 'all' ? null : roasBandFilter,
                source: sourceFilter === 'all' ? null : sourceFilter,
                scoring_engine: scoringEngineFilter === 'all' ? null : scoringEngineFilter,
                search: searchValue.trim() || null,
                page: targetPage,
                page_size: PAGE_SIZE,
            });
            const items = data.items || [];
            setQueueItems(items);
            setTotalPages(data.summary?.total_pages ?? 1);
            setTotalCount(data.summary?.total ?? 0);
            setSelectedId(items[0]?.score_event_id ?? null);
            setSelectedIds(new Set());
        } catch (err) {
            setError(err.message || t('Failed to load records', '載入評估紀錄失敗'));
        } finally {
            setLoadingQueue(false);
        }
    };

    const handlePageChange = (newPage) => {
        if (newPage < 1 || newPage > totalPages) return;
        setPage(newPage);
        loadQueue(newPage);
    };

    const toggleSelect = (e, id) => {
        e.stopPropagation();
        setSelectedIds(prev => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === queueItems.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(queueItems.map(i => i.score_event_id)));
        }
    };

    const handleBatchDelete = async () => {
        const ids = [...selectedIds];
        if (ids.length === 0) return;
        if (!window.confirm(t(`Delete ${ids.length} selected records?`, `確定要刪除已選取的 ${ids.length} 筆紀錄？`))) return;
        setBatchDeleting(true);
        try {
            await batchDeleteMetaAndromedaReviewItems(ids);
            if (ids.includes(selectedId)) setSelectedId(null);
            await loadQueue(page);
        } catch (err) {
            setError(err.message || t('Batch delete failed', '批次刪除失敗'));
        } finally {
            setBatchDeleting(false);
        }
    };

    const handleDelete = async (e, scoreEventId) => {
        e.stopPropagation();
        if (!window.confirm(t(`Delete record ${scoreEventId}?`, `確定要刪除紀錄 ${scoreEventId}？`))) return;
        setDeletingId(scoreEventId);
        try {
            await deleteMetaAndromedaReviewItem(scoreEventId);
            if (selectedId === scoreEventId) setSelectedId(null);
            await loadQueue(page);
        } catch (err) {
            setError(err.message || t('Delete failed', '刪除失敗'));
        } finally {
            setDeletingId(null);
        }
    };

    // 篩選條件改變時重置頁碼
    useEffect(() => {
        setPage(1);
        loadQueue(1);
    }, [statusFilter, observationFilter, roasBandFilter, sourceFilter, scoringEngineFilter]);

    const handleSearchChange = (e) => {
        const val = e.target.value;
        setSearchTerm(val);
        clearTimeout(searchTimerRef.current);
        searchTimerRef.current = setTimeout(() => {
            setPage(1);
            loadQueue(1, val);
        }, 400);
    };

    const loadDetail = async (scoreEventId) => {
        if (!scoreEventId) { setDetail(null); return; }
        setLoadingDetail(true);
        setError(null);
        try {
            const detailData = await fetchMetaAndromedaReviewDetail(scoreEventId);
            setDetail(detailData);
        } catch (err) {
            setError(err.message || t('Failed to load detail', '載入明細失敗'));
        } finally {
            setLoadingDetail(false);
        }
    };

    useEffect(() => { loadDetail(selectedId); }, [selectedId]);


    if (accessLoading) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>{t('Checking access...', '正在確認權限...')}</div>
                </section>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={errorPanelStyle}>{t('No access to Meta Andromeda in this workspace.', '此工作區無 Meta Andromeda 存取權限。')}</div>
                </section>
            </div>
        );
    }

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <style>{`
                .queue-scroll-box::-webkit-scrollbar { width: 6px; }
                .queue-scroll-box::-webkit-scrollbar-track { background: rgba(255,255,255,0.01); border-radius: 999px; }
                .queue-scroll-box::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 999px; }
                .queue-scroll-box::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }
                .queue-item-wrap .queue-delete-btn { opacity: 0; transition: opacity 0.15s; }
                .queue-item-wrap:hover .queue-delete-btn { opacity: 1; }
            `}</style>

            {/* 標題列 */}
            <div style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                flexDirection: isMobile ? 'column' : 'row',
                gap: '16px', marginBottom: '20px'
            }}>
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>Meta Andromeda</div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                </div>

                {/* 篩選器列 */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Sources', '全部來源')}</option>
                        <option value="analytics">{t('Analytics Import', '成效分析匯入')}</option>
                        <option value="score_lab">{t('Score Lab', '評分工作台')}</option>
                    </select>
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Statuses', '全部狀態')}</option>
                        <option value="completed">{t('Completed', '已完成')}</option>
                        <option value="queued">{t('Queued', '排隊中')}</option>
                        <option value="failed">{t('Failed', '失敗')}</option>
                    </select>
                    <select value={roasBandFilter} onChange={(e) => setRoasBandFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Scores', '全部評分')}</option>
                        <option value="high">{t('High', '高')}</option>
                        <option value="mid">{t('Mid', '中')}</option>
                        <option value="low">{t('Low', '低')}</option>
                    </select>
                    <select value={observationFilter} onChange={(e) => setObservationFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Records', '全部紀錄')}</option>
                        <option value="matched">{t('Matched', '已匹配成效')}</option>
                        <option value="unmatched">{t('Not Matched', '尚未匹配')}</option>
                    </select>
                    <select value={scoringEngineFilter} onChange={(e) => setScoringEngineFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Engines', '全部引擎')}</option>
                        <option value="ai">{t('AI Model', 'AI 模型')}</option>
                        <option value="heuristic">{t('Heuristic', '啟發式引擎')}</option>
                    </select>
                </div>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '0.9fr 1.1fr', gap: '16px' }}>

                {/* 左側清單 */}
                <section style={panelStyle}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Scored Assets', '已評估素材')}</h2>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {!loadingQueue && queueItems.length > 0 && (
                                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)', fontSize: '0.78rem', cursor: 'pointer', userSelect: 'none' }}>
                                    <input
                                        type="checkbox"
                                        checked={selectedIds.size === queueItems.length && queueItems.length > 0}
                                        onChange={toggleSelectAll}
                                        style={{ cursor: 'pointer' }}
                                    />
                                    {t('All', '全選')}
                                </label>
                            )}
                            {selectedIds.size > 0 && (
                                <button
                                    type="button"
                                    onClick={handleBatchDelete}
                                    disabled={batchDeleting}
                                    style={{ padding: '4px 10px', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.35)', background: 'rgba(239,68,68,0.12)', color: '#ef4444', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, opacity: batchDeleting ? 0.5 : 1 }}
                                >
                                    {batchDeleting ? t('Deleting…', '刪除中…') : t(`Delete (${selectedIds.size})`, `刪除 (${selectedIds.size})`)}
                                </button>
                            )}
                            {!loadingQueue && selectedIds.size === 0 && (
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                                    {t(`${totalCount} total`, `共 ${totalCount} 筆`)}
                                </span>
                            )}
                        </div>
                    </div>

                    <input
                        type="text"
                        placeholder={t('Search ID, ad name, objective, market...', '搜尋 ID、廣告名稱、目標、市場...')}
                        value={searchTerm}
                        onChange={handleSearchChange}
                        style={searchInputStyle}
                    />

                    {loadingQueue ? (
                        <div style={{ color: 'var(--text-secondary)', padding: '16px 0' }}>{t('Loading...', '載入中...')}</div>
                    ) : queueItems.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)', padding: '16px 0' }}>{t('No records found.', '目前沒有符合條件的紀錄。')}</div>
                    ) : (
                        <div
                            className="queue-scroll-box"
                            style={{ display: 'grid', gap: '8px', maxHeight: 'calc(100vh - 360px)', minHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}
                        >
                            {queueItems.map((item) => {
                                const previewUrl = resolvePreviewUrl(item);
                                const isVideo = item.asset_type === 'video';
                                return (
                                    <div
                                        key={item.score_event_id}
                                        className="queue-item-wrap"
                                        style={{ position: 'relative' }}
                                    >
                                    <button
                                        type="button"
                                        onClick={() => setSelectedId(item.score_event_id)}
                                        style={{
                                            ...queueItemStyle,
                                            display: 'flex', gap: '10px', alignItems: 'center',
                                            borderColor: selectedIds.has(item.score_event_id) ? 'rgba(239,68,68,0.5)' : selectedId === item.score_event_id ? 'var(--accent-primary)' : 'var(--glass-border)',
                                            background: selectedIds.has(item.score_event_id) ? 'rgba(239,68,68,0.04)' : selectedId === item.score_event_id ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.01)',
                                        }}
                                    >
                                        {/* 勾選框 */}
                                        <input
                                            type="checkbox"
                                            checked={selectedIds.has(item.score_event_id)}
                                            onClick={(e) => toggleSelect(e, item.score_event_id)}
                                            onChange={() => {}}
                                            style={{ cursor: 'pointer', flexShrink: 0, accentColor: '#ef4444' }}
                                        />
                                        {/* 縮圖 */}
                                        <div style={{
                                            width: '52px', height: '52px', borderRadius: '8px', overflow: 'hidden',
                                            background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                                        }}>
                                            {previewUrl
                                                ? isVideo
                                                    ? <video src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted playsInline />
                                                    : <img src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" />
                                                : <span style={{ fontSize: '1.2rem' }}>{isVideo ? '📹' : '🖼️'}</span>
                                            }
                                        </div>

                                        {/* 資訊 */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px', alignItems: 'center', marginBottom: '4px' }}>
                                                <strong style={{ color: 'var(--text-primary)', fontSize: '0.82rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {item.score_event_id}
                                                </strong>
                                                <span style={{ padding: '1px 7px', borderRadius: '999px', background: statusToneMap[item.status] || 'rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.7rem', fontWeight: 600, flexShrink: 0 }}>
                                                    {getStatusLabel(item.status)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: item.ad_name ? '2px' : '5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {item.objective} · {item.placement_family} · {item.market}
                                            </div>
                                            {item.ad_name && (
                                                <div style={{ color: 'var(--text-primary)', fontSize: '0.73rem', marginBottom: '5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', opacity: 0.75 }}>
                                                    {item.ad_name}
                                                </div>
                                            )}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', flexWrap: 'wrap' }}>
                                                {(() => {
                                                    const sm = sourceMeta[item.source] || sourceMeta.score_lab;
                                                    const sourceLabel = item.source === 'analytics'
                                                        ? t('Analytics', '成效分析')
                                                        : t('Score Lab', '評分工作台');
                                                    return (
                                                        <span style={{ padding: '1px 7px', borderRadius: '999px', background: sm.bg, color: sm.color, fontWeight: 600 }}>
                                                            {sourceLabel}
                                                        </span>
                                                    );
                                                })()}
                                                <span style={{ color: 'var(--text-secondary)' }}>
                                                    {t('Score', '評分')}: <strong style={{ color: 'var(--text-primary)' }}>{item.overall_score ?? '--'}</strong>
                                                </span>
                                                {item.roas_band && (
                                                    <span style={{ padding: '1px 7px', borderRadius: '999px', background: `${roasBandColor[item.roas_band]}22`, color: roasBandColor[item.roas_band], fontWeight: 700 }}>
                                                        {item.roas_band.toUpperCase()}
                                                    </span>
                                                )}
                                                {item.has_observation && (
                                                    <span style={{ padding: '1px 7px', borderRadius: '999px', background: 'rgba(16,185,129,0.12)', color: '#10b981', fontWeight: 600 }}>
                                                        {t('Matched', '已匹配')}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                    <button
                                        type="button"
                                        className="queue-delete-btn"
                                        onClick={(e) => handleDelete(e, item.score_event_id)}
                                        disabled={deletingId === item.score_event_id}
                                        title={t('Delete record', '刪除紀錄')}
                                        style={{
                                            position: 'absolute', bottom: '8px', right: '8px',
                                            background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)',
                                            borderRadius: '6px', color: '#ef4444', cursor: 'pointer',
                                            fontSize: '0.72rem', padding: '2px 7px', lineHeight: 1.5,
                                            opacity: deletingId === item.score_event_id ? 0.5 : undefined,
                                        }}
                                    >
                                        {deletingId === item.score_event_id ? '…' : t('Delete', '刪除')}
                                    </button>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* 分頁選單 */}
                    <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} t={t} />
                    {totalPages > 1 && (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '8px' }}>
                            {t(`Page ${page} / ${totalPages}`, `第 ${page} 頁，共 ${totalPages} 頁`)}
                        </div>
                    )}
                </section>

                {/* 右側詳情 */}
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Evaluation Detail', '評估明細')}</h2>
                    {loadingDetail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading...', '載入中...')}</div>
                    ) : !detail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Select a record to view details.', '請選擇一筆紀錄查看明細。')}</div>
                    ) : (
                        <div className="queue-scroll-box" style={{ display: 'grid', gap: '14px', maxHeight: 'calc(100vh - 290px)', overflowY: 'auto', paddingRight: '4px' }}>

                            {/* 素材預覽 */}
                            <div style={{ ...detailCardStyle, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '160px', background: 'rgba(0,0,0,0.2)', overflow: 'hidden' }}>
                                {(() => {
                                    const url = resolvePreviewUrl(detail);
                                    if (!url) return (
                                        <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                                            <span style={{ fontSize: '2.5rem' }}>{detail.asset_type === 'video' ? '📹' : '🖼️'}</span>
                                            <span style={{ fontSize: '0.82rem' }}>{t('No preview', '無預覽圖')}</span>
                                        </div>
                                    );
                                    return detail.asset_type === 'video'
                                        ? <video src={url} controls style={{ maxWidth: '100%', maxHeight: '280px', borderRadius: '8px' }} />
                                        : <img src={url} style={{ maxWidth: '100%', maxHeight: '280px', objectFit: 'contain', borderRadius: '8px' }} alt="" />;
                                })()}
                            </div>

                            {/* 評分核心資訊 */}
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '10px' }}>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Overall Score', '總評分')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '1.5rem' }}>{detail.overall_score ?? '--'}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{getPredictedBandLabel(detail.objective_group, language)}</div>
                                    <div style={{ fontWeight: 700, fontSize: '1.1rem', color: roasBandColor[detail.roas_prediction?.band] || 'var(--text-secondary)' }}>
                                        {detail.roas_prediction?.band ? detail.roas_prediction.band.toUpperCase() : '--'}
                                    </div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Model', '模型版本')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.85rem' }}>{detail.model_version || '--'}</div>
                                </div>
                            </div>

                            {/* 評估核心 */}
                            {detail.lineage && (
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Scoring Engine', '評估核心')}</div>
                                    <div style={{ color: detail.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <span>{detail.lineage.scoring_mode === 'ai' ? '🤖' : '⚙️'}</span>
                                        <span style={{ fontSize: '0.88rem' }}>
                                            {detail.lineage.scoring_mode === 'ai'
                                                ? `OpenRouter (${detail.lineage.provider_model || '--'})`
                                                : t('Heuristic Rule Engine', '啟發式規則引擎')
                                            }
                                        </span>
                                    </div>
                                    {detail.lineage.fallback_reason && (
                                        <div style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>
                                            ⚠️ {detail.lineage.fallback_reason}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 實際成效對照 */}
                            {detail.observation ? (
                                <div style={{ ...detailCardStyle, border: '1px solid rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.03)' }}>
                                    <div style={{ fontWeight: 700, color: '#10b981', marginBottom: '10px' }}>✅ {t('Actual Performance Match', '實際成效對照')}</div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
                                        {[
                                            [t('Predicted', '預測'), detail.observation.prediction_band],
                                            [t('Actual', '實際'), detail.observation.observed_band],
                                            [t('Error', '誤差'), detail.observation.error],
                                        ].map(([label, val]) => (
                                            <div key={label} style={innerCardStyle}>
                                                <div style={labelStyle}>{label}</div>
                                                <div style={{ fontWeight: 700, color: typeof val === 'string' ? (roasBandColor[val] || 'var(--text-primary)') : (val === 0 ? '#10b981' : val <= 1 ? '#f59e0b' : '#ef4444') }}>
                                                    {typeof val === 'string' ? val.toUpperCase() : val ?? '--'}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    {detail.observation.ad_name && (
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>
                                            {t('Ad: ', '廣告：')}<span style={{ color: 'var(--text-primary)' }}>{detail.observation.ad_name}</span>
                                        </div>
                                    )}
                                    {detail.observation.observation_window_kind && (
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '8px' }}>
                                            {t('Window: ', '窗口：')}{detail.observation.observation_window_kind}
                                            {detail.observation.observation_window_start && ` (${detail.observation.observation_window_start} → ${detail.observation.observation_window_end})`}
                                        </div>
                                    )}
                                    {detail.observation.performance_snapshot && Object.keys(detail.observation.performance_snapshot).length > 0 && (
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '6px' }}>
                                            {Object.entries(detail.observation.performance_snapshot)
                                                .filter(([, v]) => v !== null && v !== undefined)
                                                .slice(0, 8)
                                                .map(([key, value]) => (
                                                    <div key={key} style={innerCardStyle}>
                                                        <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{getPerfMetricLabel(key, language)}</div>
                                                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                                                            {formatPerfValue(key, value)}
                                                        </div>
                                                    </div>
                                                ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ ...detailCardStyle, border: '1px solid rgba(245,158,11,0.2)', background: 'rgba(245,158,11,0.03)' }}>
                                    <div style={{ color: '#f59e0b', fontWeight: 600, marginBottom: '6px' }}>⏳ {t('Awaiting Match', '等待實際成效匹配')}</div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                                        {t(
                                            'Import actual ad data via Analytics → Batch Import to enable comparison.',
                                            '透過「成效分析」→ 批次匯入後，系統會自動關聯實際成效，即可在此查看預測準確度。'
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* AI 摘要 */}
                            <div style={detailCardStyle}>
                                <div style={labelStyle}>{t('AI Summary', 'AI 評分摘要')}</div>
                                <div style={{ color: 'var(--text-primary)', lineHeight: 1.6 }}>
                                    {detail.explanations?.summary || t('No summary available.', '尚無評分摘要。')}
                                </div>
                            </div>

                            {/* 診斷細項 */}
                            {detail.diagnostic_breakdown && Object.keys(detail.diagnostic_breakdown).length > 0 && (
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Diagnostic Breakdown', '診斷細項')}</div>
                                    <div style={{ display: 'grid', gap: '8px', marginTop: '8px' }}>
                                        {Object.entries(detail.diagnostic_breakdown).map(([key, value]) => (
                                            <div key={key} style={{ display: 'flex', gap: '10px' }}>
                                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', minWidth: '110px', flexShrink: 0 }}>{getDiagnosticLabel(key, language)}</span>
                                                <span style={{ color: 'var(--text-primary)', fontSize: '0.82rem', lineHeight: 1.5 }}>{value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* 驅動因素 */}
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '10px' }}>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Positive Drivers', '正向因素')}</div>
                                    <ul style={listStyle}>
                                        {(detail.top_positive_drivers || []).length > 0
                                            ? detail.top_positive_drivers.map((d) => <li key={d}>{d}</li>)
                                            : <li>--</li>}
                                    </ul>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Risk Drivers', '風險因素')}</div>
                                    <ul style={listStyle}>
                                        {(detail.top_negative_drivers || []).length > 0
                                            ? detail.top_negative_drivers.map((d) => <li key={d}>{d}</li>)
                                            : <li>--</li>}
                                    </ul>
                                </div>
                            </div>

                            {/* 廣告文案 */}
                            {detail.request_context && Object.values(detail.request_context).some(Boolean) && (
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Ad Copy Context', '廣告文案')}</div>
                                    <div style={{ display: 'grid', gap: '6px', marginTop: '8px' }}>
                                        {[['headline', t('Headline', '標題')], ['primary_text', t('Primary Text', '主要文字')], ['cta', 'CTA']].map(([key, label]) =>
                                            detail.request_context[key] ? (
                                                <div key={key} style={{ display: 'flex', gap: '10px' }}>
                                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', minWidth: '70px', flexShrink: 0 }}>{label}</span>
                                                    <span style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>{detail.request_context[key]}</span>
                                                </div>
                                            ) : null
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
};

/* ── styles ── */
const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const queueItemStyle = {
    textAlign: 'left',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'all 0.15s ease-in-out',
    width: '100%',
};

const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const innerCardStyle = {
    padding: '8px 10px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const sectionTitleStyle = {
    margin: '0 0 14px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const labelStyle = {
    color: 'var(--text-secondary)',
    fontSize: '0.8rem',
    marginBottom: '5px',
};

const selectStyle = {
    padding: '8px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
};

const searchInputStyle = {
    width: '100%',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    marginBottom: '12px',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.18)',
    color: 'var(--text-primary)',
};

const listStyle = {
    margin: 0,
    paddingLeft: '18px',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

const pagebtnStyle = {
    padding: '5px 10px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontSize: '0.85rem',
    minWidth: '32px',
    transition: 'all 0.15s',
};

export default MetaAndromedaReviewQueue;
