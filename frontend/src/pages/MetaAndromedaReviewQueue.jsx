import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useModuleAccess } from '../hooks/usePermission';

import {
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewQueue,
} from '../services/metaAndromedaReviewQueueService';

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
    null: 'var(--text-secondary)',
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

const MetaAndromedaReviewQueue = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('meta_andromeda', selectedTeamId);
    const [statusFilter, setStatusFilter] = useState('completed');
    const [observationFilter, setObservationFilter] = useState('all');
    const [queueItems, setQueueItems] = useState([]);
    const [hasMore, setHasMore] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loadingQueue, setLoadingQueue] = useState(true);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const PAGE_SIZE = 50;

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

    const buildObsParam = () =>
        observationFilter === 'matched' ? true
        : observationFilter === 'unmatched' ? false
        : null;

    const loadQueue = async ({ preserveSelection = true } = {}) => {
        setLoadingQueue(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                has_observation: buildObsParam(),
                limit: PAGE_SIZE,
                offset: 0,
            });
            const items = data.items || [];
            setQueueItems(items);
            setHasMore(data.summary?.has_more ?? false);
            setSelectedId((current) => {
                if (preserveSelection && current && items.some((item) => item.score_event_id === current)) {
                    return current;
                }
                return items[0]?.score_event_id ?? null;
            });
        } catch (err) {
            setError(err.message || t('Failed to load records', '載入評估紀錄失敗'));
        } finally {
            setLoadingQueue(false);
        }
    };

    const loadMore = async () => {
        setLoadingMore(true);
        try {
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                has_observation: buildObsParam(),
                limit: PAGE_SIZE,
                offset: queueItems.length,
            });
            const newItems = data.items || [];
            setQueueItems((prev) => [...prev, ...newItems]);
            setHasMore(data.summary?.has_more ?? false);
        } catch (err) {
            setError(err.message || t('Failed to load more', '載入更多失敗'));
        } finally {
            setLoadingMore(false);
        }
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

    useEffect(() => { loadQueue(); }, [statusFilter, observationFilter]);
    useEffect(() => { loadDetail(selectedId); }, [selectedId]);

    const filteredItems = queueItems.filter((item) => {
        const term = searchTerm.toLowerCase().trim();
        return (
            item.score_event_id.toLowerCase().includes(term) ||
            item.objective.toLowerCase().includes(term) ||
            item.placement_family.toLowerCase().includes(term) ||
            item.market.toLowerCase().includes(term)
        );
    });

    if (accessLoading) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                        {t('Checking access...', '正在確認權限...')}
                    </div>
                </section>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={errorPanelStyle}>
                        {t('No access to Meta Andromeda in this workspace.', '此工作區無 Meta Andromeda 存取權限。')}
                    </div>
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
            `}</style>

            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                flexDirection: isMobile ? 'column' : 'row',
                gap: '16px',
                marginBottom: '20px'
            }}>
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>Meta Andromeda</div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                </div>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Statuses', '全部狀態')}</option>
                        <option value="completed">{t('Completed', '已完成')}</option>
                        <option value="queued">{t('Queued', '排隊中')}</option>
                        <option value="failed">{t('Failed', '失敗')}</option>
                    </select>
                    <select value={observationFilter} onChange={(e) => setObservationFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Records', '全部紀錄')}</option>
                        <option value="matched">{t('Matched with Actual Data', '已匹配實際成效')}</option>
                        <option value="unmatched">{t('Not Yet Matched', '尚未匹配')}</option>
                    </select>
                </div>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '0.9fr 1.1fr',
                gap: '16px'
            }}>
                {/* 左側清單 */}
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Scored Assets', '已評估素材')}</h2>
                    <input
                        type="text"
                        placeholder={t('Search by ID, objective, placement...', '搜尋 ID、目標、版位...')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={searchInputStyle}
                    />
                    {loadingQueue ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading...', '載入中...')}</div>
                    ) : filteredItems.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('No records found.', '目前沒有符合條件的紀錄。')}</div>
                    ) : (
                        <div
                            className="queue-scroll-box"
                            style={{
                                display: 'grid',
                                gap: '10px',
                                maxHeight: 'calc(100vh - 290px)',
                                minHeight: '300px',
                                overflowY: 'auto',
                                paddingRight: '4px'
                            }}
                        >
                            {filteredItems.map((item) => {
                                const previewUrl = resolvePreviewUrl(item);
                                const isVideo = item.asset_type === 'video';
                                return (
                                    <button
                                        key={item.score_event_id}
                                        type="button"
                                        onClick={() => setSelectedId(item.score_event_id)}
                                        style={{
                                            ...queueItemStyle,
                                            display: 'flex',
                                            gap: '12px',
                                            alignItems: 'center',
                                            borderColor: selectedId === item.score_event_id
                                                ? 'var(--accent-primary)'
                                                : 'var(--glass-border)',
                                            background: selectedId === item.score_event_id
                                                ? 'rgba(255,255,255,0.05)'
                                                : 'rgba(255,255,255,0.01)',
                                        }}
                                    >
                                        {/* 縮圖 */}
                                        <div style={{
                                            width: '60px', height: '60px', borderRadius: '8px',
                                            overflow: 'hidden', background: 'rgba(255,255,255,0.03)',
                                            border: '1px solid var(--glass-border)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            flexShrink: 0
                                        }}>
                                            {previewUrl ? (
                                                isVideo
                                                    ? <video src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted playsInline />
                                                    : <img src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" />
                                            ) : (
                                                <span style={{ fontSize: '1.4rem' }}>{isVideo ? '📹' : '🖼️'}</span>
                                            )}
                                        </div>
                                        {/* 資訊 */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                                                <strong style={{ color: 'var(--text-primary)', fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {item.score_event_id}
                                                </strong>
                                                <span style={{
                                                    padding: '2px 8px', borderRadius: '999px',
                                                    background: statusToneMap[item.status] || 'rgba(255,255,255,0.08)',
                                                    color: 'var(--text-primary)', fontSize: '0.72rem', fontWeight: 600, flexShrink: 0
                                                }}>
                                                    {getStatusLabel(item.status)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '6px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {item.objective} / {item.placement_family} / {item.market}
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                                                <span style={{ color: 'var(--text-secondary)' }}>
                                                    {t('Score: ', '評分: ')}
                                                    <strong style={{ color: 'var(--text-primary)' }}>{item.overall_score ?? '--'}</strong>
                                                    {item.roas_band && (
                                                        <span style={{ marginLeft: '6px', color: roasBandColor[item.roas_band] || 'var(--text-secondary)', fontWeight: 700 }}>
                                                            {item.roas_band.toUpperCase()}
                                                        </span>
                                                    )}
                                                </span>
                                                {item.has_observation && (
                                                    <span style={{
                                                        padding: '1px 7px', borderRadius: '999px',
                                                        background: 'rgba(16, 185, 129, 0.15)',
                                                        color: '#10b981', fontSize: '0.72rem', fontWeight: 600
                                                    }}>
                                                        {t('Matched', '已匹配')}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    )}

                    {/* 載入更多 */}
                    {hasMore && !loadingQueue && (
                        <button
                            type="button"
                            onClick={loadMore}
                            disabled={loadingMore}
                            style={{
                                marginTop: '12px', width: '100%',
                                padding: '10px', borderRadius: '10px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.02)',
                                color: 'var(--text-secondary)',
                                cursor: loadingMore ? 'not-allowed' : 'pointer',
                                fontSize: '0.85rem',
                            }}
                        >
                            {loadingMore ? t('Loading...', '載入中...') : t('Load More', '載入更多')}
                        </button>
                    )}
                    {!hasMore && queueItems.length > 0 && !loadingQueue && (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: '12px' }}>
                            {t(`Total ${queueItems.length} records`, `共 ${queueItems.length} 筆紀錄`)}
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
                        <div className="queue-scroll-box" style={{ display: 'grid', gap: '16px', maxHeight: 'calc(100vh - 290px)', overflowY: 'auto', paddingRight: '4px' }}>

                            {/* 素材預覽 */}
                            <div style={{
                                ...detailCardStyle, display: 'flex', flexDirection: 'column',
                                alignItems: 'center', justifyContent: 'center', minHeight: '180px',
                                background: 'rgba(0,0,0,0.2)', overflow: 'hidden'
                            }}>
                                {(() => {
                                    const url = resolvePreviewUrl(detail);
                                    if (!url) return (
                                        <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                                            <span style={{ fontSize: '2.5rem' }}>{detail.asset_type === 'video' ? '📹' : '🖼️'}</span>
                                            <span style={{ fontSize: '0.82rem' }}>{t('No preview available', '無預覽圖')}</span>
                                        </div>
                                    );
                                    return detail.asset_type === 'video'
                                        ? <video src={url} controls style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }} />
                                        : <img src={url} style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain', borderRadius: '8px' }} alt="" />;
                                })()}
                            </div>

                            {/* 基本資訊 */}
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '12px' }}>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Status', '狀態')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{getStatusLabel(detail.status)}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Asset Type', '素材類型')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                        {detail.asset_type === 'video' ? t('Video', '影片') : t('Image', '圖片')}
                                    </div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Model Version', '模型版本')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.model_version || '--'}</div>
                                </div>
                            </div>

                            {/* 評估核心 */}
                            {detail.lineage && (
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Scoring Engine', '評估核心')}</div>
                                    <div style={{
                                        color: detail.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                        fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px'
                                    }}>
                                        <span>{detail.lineage.scoring_mode === 'ai' ? '🤖' : '⚙️'}</span>
                                        <span>
                                            {detail.lineage.scoring_mode === 'ai'
                                                ? t(`OpenRouter (${detail.lineage.provider_model || '--'})`, `OpenRouter 聚合模型 (${detail.lineage.provider_model || '--'})`)
                                                : t('Heuristic Rule Engine', '啟發式模擬規則引擎')
                                            }
                                        </span>
                                    </div>
                                    {detail.lineage.fallback_reason && (
                                        <div style={{ color: '#ef4444', fontSize: '0.82rem', marginTop: '6px', lineHeight: 1.4 }}>
                                            ⚠️ {t('AI Unavailable. Fallback: ', 'AI 服務不可用，備用方案：')}{detail.lineage.fallback_reason}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 預估分數 */}
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '12px' }}>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Overall Score', '總評分')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '1.4rem' }}>{detail.overall_score ?? '--'}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Predicted ROAS Band', '預測 ROAS 區間')}</div>
                                    <div style={{ fontWeight: 700, fontSize: '1.1rem', color: roasBandColor[detail.roas_prediction?.band] || 'var(--text-secondary)' }}>
                                        {detail.roas_prediction?.band ? detail.roas_prediction.band.toUpperCase() : '--'}
                                    </div>
                                </div>
                            </div>

                            {/* 實際成效對照 */}
                            {detail.observation ? (
                                <div style={{ ...detailCardStyle, border: '1px solid rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.03)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                        <span style={{ color: '#10b981', fontWeight: 700 }}>✅ {t('Actual Performance Match', '實際成效對照')}</span>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
                                        <div style={innerCardStyle}>
                                            <div style={labelStyle}>{t('Predicted', '預測 ROAS')}</div>
                                            <div style={{ fontWeight: 700, color: roasBandColor[detail.observation.prediction_band] || 'var(--text-secondary)' }}>
                                                {detail.observation.prediction_band?.toUpperCase() || '--'}
                                            </div>
                                        </div>
                                        <div style={innerCardStyle}>
                                            <div style={labelStyle}>{t('Actual', '實際 ROAS')}</div>
                                            <div style={{ fontWeight: 700, color: roasBandColor[detail.observation.observed_band] || 'var(--text-secondary)' }}>
                                                {detail.observation.observed_band?.toUpperCase() || '--'}
                                            </div>
                                        </div>
                                        <div style={innerCardStyle}>
                                            <div style={labelStyle}>{t('Error', '誤差')}</div>
                                            <div style={{ fontWeight: 700, color: detail.observation.error === 0 ? '#10b981' : detail.observation.error <= 1 ? '#f59e0b' : '#ef4444' }}>
                                                {detail.observation.error ?? '--'}
                                            </div>
                                        </div>
                                    </div>
                                    {detail.observation.ad_name && (
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: '6px' }}>
                                            {t('Ad: ', '廣告：')}<span style={{ color: 'var(--text-primary)' }}>{detail.observation.ad_name}</span>
                                        </div>
                                    )}
                                    {detail.observation.observation_window_kind && (
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: '8px' }}>
                                            {t('Window: ', '觀測窗口：')}{detail.observation.observation_window_kind}
                                            {detail.observation.observation_window_start && ` (${detail.observation.observation_window_start} → ${detail.observation.observation_window_end})`}
                                        </div>
                                    )}
                                    {/* 關鍵績效指標 */}
                                    {detail.observation.performance_snapshot && Object.keys(detail.observation.performance_snapshot).length > 0 && (
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '8px' }}>
                                            {Object.entries(detail.observation.performance_snapshot)
                                                .filter(([, v]) => v !== null && v !== undefined)
                                                .slice(0, 8)
                                                .map(([key, value]) => (
                                                    <div key={key} style={innerCardStyle}>
                                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{key}</div>
                                                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                                                            {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                                        </div>
                                                    </div>
                                                ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ ...detailCardStyle, border: '1px solid rgba(245, 158, 11, 0.2)', background: 'rgba(245, 158, 11, 0.03)' }}>
                                    <div style={{ color: '#f59e0b', fontWeight: 600, marginBottom: '6px' }}>
                                        ⏳ {t('Awaiting Actual Performance Data', '等待實際成效匹配')}
                                    </div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                                        {t(
                                            'This asset has not been matched with real ad performance data yet. Import actual data via Analytics → Batch Import to enable comparison.',
                                            '此素材尚未與真實廣告成效數據匹配。透過「成效分析」→ 批次匯入後，系統會自動關聯實際 ROAS，即可在此查看預測準確度。'
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
                                            <div key={key} style={{ display: 'flex', gap: '8px' }}>
                                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', minWidth: '120px' }}>{key}</span>
                                                <span style={{ color: 'var(--text-primary)', fontSize: '0.82rem', lineHeight: 1.5 }}>{value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* 驅動因素 */}
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '12px' }}>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Positive Drivers', '正向因素')}</div>
                                    <ul style={listStyle}>
                                        {(detail.top_positive_drivers || []).length > 0
                                            ? (detail.top_positive_drivers || []).map((d) => <li key={d}>{d}</li>)
                                            : <li>--</li>}
                                    </ul>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={labelStyle}>{t('Risk Drivers', '風險因素')}</div>
                                    <ul style={listStyle}>
                                        {(detail.top_negative_drivers || []).length > 0
                                            ? (detail.top_negative_drivers || []).map((d) => <li key={d}>{d}</li>)
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
                                                <div key={key} style={{ display: 'flex', gap: '8px' }}>
                                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', minWidth: '80px' }}>{label}</span>
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

const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const queueItemStyle = {
    textAlign: 'left',
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'all 0.15s ease-in-out',
    width: '100%',
};

const detailCardStyle = {
    padding: '16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const innerCardStyle = {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const labelStyle = {
    color: 'var(--text-secondary)',
    fontSize: '0.82rem',
    marginBottom: '6px',
};

const selectStyle = {
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
};

const searchInputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    marginBottom: '16px',
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

export default MetaAndromedaReviewQueue;
