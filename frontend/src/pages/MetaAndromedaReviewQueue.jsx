import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import {
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewFeedback,
    fetchMetaAndromedaReviewQueue,
    submitMetaAndromedaReviewFeedback,
} from '../services/metaAndromedaReviewQueueService';

const statusToneMap = {
    completed: 'rgba(16, 185, 129, 0.15)',
    queued: 'rgba(59, 130, 246, 0.15)',
    failed: 'rgba(239, 68, 68, 0.15)',
    processing: 'rgba(245, 158, 11, 0.15)',
};

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const resolvePreviewUrl = (item) => {
    if (!item) return null;
    const url = item.preview_url;
    if (url && (url.startsWith('http') || url.startsWith('/'))) {
        return url;
    }
    if (item.asset_uri) {
        const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
        return `${base}/api/meta-andromeda/assets/preview?uri=${encodeURIComponent(item.asset_uri)}`;
    }
    return null;
};

const defaultFeedbackForm = {
    decision: 'approve',
    reason_codes: '',
    comment: '',
};

const MetaAndromedaReviewQueue = () => {
    const { isMobile, language } = useOutletContext();
    const [statusFilter, setStatusFilter] = useState('completed');
    const [reviewedFilter, setReviewedFilter] = useState('unreviewed');
    const [queueItems, setQueueItems] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [feedback, setFeedback] = useState([]);
    const [loadingQueue, setLoadingQueue] = useState(true);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [submittingFeedback, setSubmittingFeedback] = useState(false);
    const [error, setError] = useState(null);
    const [feedbackForm, setFeedbackForm] = useState(defaultFeedbackForm);
    const [searchTerm, setSearchTerm] = useState('');

    const t = (en, zh) => (language === 'en' ? en : zh);

    const getTranslation = (key) => {
        if (!key) return '--';
        const keyLower = String(key).toLowerCase();
        switch (keyLower) {
            case 'status': return t('Status', '狀態');
            case 'attempts': return t('Attempts', '處理次數');
            case 'overall_score': return t('Overall Score', '總評分');
            case 'summary': return t('Summary', '評分摘要說明');
            case 'completed': return t('Completed', '已完成');
            case 'failed': return t('Failed', '失敗');
            case 'pending': return t('Pending', '待處理');
            case 'processing': return t('Processing', '處理中');
            case 'queued': return t('Queued', '排隊中');
            case 'unreviewed': return t('Unreviewed', '未審核');
            case 'reviewed': return t('Reviewed', '已審核');
            case 'approve': return t('Approve', '通過');
            case 'revise': return t('Revise', '修改');
            case 'reject': return t('Reject', '退回');
            default: return key;
        }
    };

    const loadQueue = async ({ preserveSelection = true } = {}) => {
        setLoadingQueue(true);
        setError(null);
        try {
            const reviewed = reviewedFilter === 'all' ? null : reviewedFilter === 'reviewed';
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                reviewed,
                limit: 50, // 稍微擴大載入筆數，配合滾動條與搜尋
            });
            const items = data.items || [];
            setQueueItems(items);
            setSelectedId((current) => {
                if (preserveSelection && current && items.some((item) => item.score_event_id === current)) {
                    return current;
                }
                return items[0]?.score_event_id ?? null;
            });
        } catch (err) {
            setError(err.message || t('Failed to load review queue', '載入審核佇列失敗'));
        } finally {
            setLoadingQueue(false);
        }
    };

    const loadDetail = async (scoreEventId) => {
        if (!scoreEventId) {
            setDetail(null);
            setFeedback([]);
            return;
        }

        setLoadingDetail(true);
        setError(null);
        try {
            const [detailData, feedbackData] = await Promise.all([
                fetchMetaAndromedaReviewDetail(scoreEventId),
                fetchMetaAndromedaReviewFeedback(scoreEventId),
            ]);
            setDetail(detailData);
            setFeedback(feedbackData.feedback || []);
        } catch (err) {
            setError(err.message || t('Failed to load review detail', '載入審核明細失敗'));
        } finally {
            setLoadingDetail(false);
        }
    };

    useEffect(() => {
        loadQueue();
    }, [statusFilter, reviewedFilter]);

    useEffect(() => {
        loadDetail(selectedId);
    }, [selectedId]);

    const handleFeedbackSubmit = async (event) => {
        event.preventDefault();
        if (!selectedId) return;

        setSubmittingFeedback(true);
        setError(null);
        try {
            await submitMetaAndromedaReviewFeedback(selectedId, {
                decision: feedbackForm.decision,
                reason_codes: feedbackForm.reason_codes
                    .split(',')
                    .map((item) => item.trim())
                    .filter(Boolean),
                comment: feedbackForm.comment || null,
            });
            setFeedbackForm(defaultFeedbackForm);
            await Promise.all([
                loadQueue({ preserveSelection: true }),
                loadDetail(selectedId),
            ]);
        } catch (err) {
            setError(err.message || t('Failed to submit feedback', '提交回饋失敗'));
        } finally {
            setSubmittingFeedback(false);
        }
    };

    // 前端動態篩選
    const filteredItems = queueItems.filter((item) => {
        const term = searchTerm.toLowerCase().strip ? searchTerm.toLowerCase().trim() : searchTerm.toLowerCase();
        return (
            item.score_event_id.toLowerCase().includes(term) ||
            item.objective.toLowerCase().includes(term) ||
            item.placement_family.toLowerCase().includes(term) ||
            item.market.toLowerCase().includes(term)
        );
    });

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            {/* 注入精美磨砂玻璃滾動條樣式 */}
            <style>{`
                .queue-scroll-box::-webkit-scrollbar {
                    width: 6px;
                }
                .queue-scroll-box::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.01);
                    border-radius: 999px;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb {
                    background: var(--glass-border);
                    border-radius: 999px;
                    transition: all 0.2s;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb:hover {
                    background: var(--accent-primary);
                }
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
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        Meta Andromeda
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t('Review Queue', '審核佇列')}
                    </h1>
                </div>

                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Statuses', '全部狀態')}</option>
                        <option value="completed">{t('Completed', '已完成')}</option>
                        <option value="queued">{t('Queued', '排隊中')}</option>
                        <option value="failed">{t('Failed', '失敗')}</option>
                    </select>
                    <select value={reviewedFilter} onChange={(e) => setReviewedFilter(e.target.value)} style={selectStyle}>
                        <option value="all">{t('All Reviews', '全部審核狀態')}</option>
                        <option value="unreviewed">{t('Unreviewed', '未審核')}</option>
                        <option value="reviewed">{t('Reviewed', '已審核')}</option>
                    </select>
                </div>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '0.9fr 1.1fr', // 微調比例，給右側詳情多一點空間
                gap: '16px'
            }}>
                {/* 左側清單面板 */}
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Queue Items', '佇列項目')}</h2>
                    
                    {/* 新增動態搜尋欄位 */}
                    <input
                        type="text"
                        placeholder={t('Search by ID, objective, placement...', '搜尋 ID、目標、版位...')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={searchInputStyle}
                    />

                    {loadingQueue ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading queue...', '載入佇列中...')}</div>
                    ) : filteredItems.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('No queue items found.', '目前沒有符合條件的項目。')}</div>
                    ) : (
                        /* 鎖定高度並具備精美滾動條的容器 */
                        <div 
                            className="queue-scroll-box"
                            style={{ 
                                display: 'grid', 
                                gap: '10px',
                                maxHeight: 'calc(100vh - 290px)', // 動態扣除頂部高度，完美適配螢幕
                                minHeight: '300px',
                                overflowY: 'auto',
                                paddingRight: '4px'
                            }}
                        >
                            {filteredItems.map((item) => {
                                const previewUrl = resolvePreviewUrl(item);
                                const isVideo = item.asset_type === 'video';
                                const hasRealPreview = !!previewUrl;
                                
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
                                                ? 'rgba(255, 255, 255, 0.05)'
                                                : 'rgba(255,255,255,0.01)',
                                        }}
                                    >
                                        {/* 素材縮圖/占位符 */}
                                        <div style={{
                                            width: '60px',
                                            height: '60px',
                                            borderRadius: '8px',
                                            overflow: 'hidden',
                                            background: 'rgba(255, 255, 255, 0.03)',
                                            border: '1px solid var(--glass-border)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0
                                        }}>
                                            {hasRealPreview ? (
                                                isVideo ? (
                                                    <video src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted playsInline />
                                                ) : (
                                                    <img src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="creative thumbnail" />
                                                )
                                            ) : (
                                                <span style={{ fontSize: '1.4rem' }}>
                                                    {isVideo ? '📹' : '🖼️'}
                                                </span>
                                            )}
                                        </div>

                                        {/* 資訊區 */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', marginBottom: '6px' }}>
                                                <strong style={{ 
                                                    color: 'var(--text-primary)', 
                                                    fontSize: '0.85rem',
                                                    whiteSpace: 'nowrap',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis'
                                                }}>
                                                    {item.score_event_id}
                                                </strong>
                                                <span style={{
                                                    padding: '2px 8px',
                                                    borderRadius: '999px',
                                                    background: statusToneMap[item.status] || 'rgba(255,255,255,0.08)',
                                                    color: 'var(--text-primary)',
                                                    fontSize: '0.72rem',
                                                    fontWeight: 600,
                                                    flexShrink: 0
                                                }}>
                                                    {getTranslation(item.status)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {item.objective} / {item.placement_family} / {item.market}
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                                                <span>{t('Score: ', '得分: ')}<strong style={{ color: 'var(--text-primary)' }}>{item.overall_score ?? '--'}</strong></span>
                                                <span style={{
                                                    color: item.reviewed ? '#10b981' : 'var(--text-secondary)',
                                                    fontWeight: item.reviewed ? 600 : 'normal'
                                                }}>
                                                    {item.reviewed ? t('Reviewed', '已審核') : t('Unreviewed', '未審核')}
                                                </span>
                                                {item.latest_feedback_decision ? (
                                                    <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
                                                        {getTranslation(item.latest_feedback_decision)}
                                                    </span>
                                                ) : null}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </section>

                {/* 右側詳細資料面板 */}
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Selected Detail', '所選明細')}</h2>
                    {loadingDetail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading detail...', '載入明細中...')}</div>
                    ) : !detail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Select a queue item.', '請先選擇一筆佇列項目。')}</div>
                    ) : (
                        /* 明細也加上滾動支持，確保左右對齊不溢出 */
                        <div 
                            className="queue-scroll-box"
                            style={{ 
                                display: 'grid', 
                                gap: '16px',
                                maxHeight: 'calc(100vh - 290px)',
                                overflowY: 'auto',
                                paddingRight: '4px'
                            }}
                        >
                            {/* 素材預覽 */}
                            <div style={{
                                ...detailCardStyle,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                minHeight: '180px',
                                background: 'rgba(0,0,0,0.2)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '12px',
                                overflow: 'hidden'
                            }}>
                                {(() => {
                                    const detailPreviewUrl = resolvePreviewUrl(detail);
                                    if (detailPreviewUrl) {
                                        return detail.asset_type === 'video' ? (
                                            <video 
                                                src={detailPreviewUrl} 
                                                controls 
                                                style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }} 
                                            />
                                        ) : (
                                            <img 
                                                src={detailPreviewUrl} 
                                                style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain', borderRadius: '8px' }} 
                                                alt="creative preview" 
                                            />
                                        );
                                    } else {
                                        return (
                                            <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                                                <span style={{ fontSize: '2.5rem' }}>{detail.asset_type === 'video' ? '📹' : '🖼️'}</span>
                                                <span style={{ fontSize: '0.82rem' }}>
                                                    {t('No online preview URL (asset_uri: ', '無線上預覽網址 (素材 URI: ')}
                                                    {detail.asset_uri ? detail.asset_uri.split('/').pop() : '--'})
                                                </span>
                                            </div>
                                        );
                                    }
                                })()}
                            </div>

                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>score_event_id</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.score_event_id}</div>
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                                gap: '12px'
                            }}>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Status', '狀態')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{getTranslation(detail.status)}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Asset Type', '素材類型')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                        {detail.asset_type === 'video' ? t('Video', '影片') : t('Image', '圖片')}
                                    </div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Model Version', '模型版本')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.model_version || '--'}</div>
                                </div>
                            </div>
                            
                            {/* 評估核心與 Fallback 警告 (同步 ScoreLab 優質體驗) */}
                            {detail.lineage && (
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Scoring Engine', '評估核心')}</div>
                                    <div style={{
                                        color: detail.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                        fontWeight: 700,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}>
                                        <span>{detail.lineage.scoring_mode === 'ai' ? '🤖' : '⚙️'}</span>
                                        <span>
                                            {detail.lineage.scoring_mode === 'ai'
                                                ? t(
                                                    `OpenRouter (${detail.lineage.provider_model || 'deepseek/deepseek-v4-flash'})`,
                                                    `OpenRouter 聚合模型 (${detail.lineage.provider_model || 'deepseek/deepseek-v4-flash'})`
                                                  )
                                                : t('Heuristic Rule Engine', '啟發式模擬規則引擎')
                                            }
                                        </span>
                                    </div>
                                    {detail.lineage.fallback_reason && (
                                        <div style={{ color: '#ef4444', fontSize: '0.82rem', marginTop: '6px', lineHeight: 1.4 }}>
                                            ⚠️ {t('AI Unavailable. Fallback engaged: ', 'AI 服務不可用，已啟用備用方案：')}{detail.lineage.fallback_reason}
                                        </div>
                                    )}
                                </div>
                            )}

                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Summary', '摘要')}</div>
                                <div style={{ color: 'var(--text-primary)', lineHeight: 1.6 }}>
                                    {detail.explanations?.summary || t('No summary available yet.', '目前尚無摘要。')}
                                </div>
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                                gap: '12px'
                            }}>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Overall Score', '總分')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.overall_score ?? '--'}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>ROAS band</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                        {detail.roas_prediction?.band || '--'}
                                    </div>
                                </div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Positive Drivers', '正向因素')}</div>
                                <ul style={listStyle}>
                                    {(detail.top_positive_drivers || []).map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                    {(detail.top_positive_drivers || []).length === 0 && <li>--</li>}
                                </ul>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px', fontSize: '0.85rem' }}>{t('Risk Drivers', '風險因素')}</div>
                                <ul style={listStyle}>
                                    {(detail.top_negative_drivers || []).map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                    {(detail.top_negative_drivers || []).length === 0 && <li>--</li>}
                                </ul>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '12px' }}>
                                    {t('Feedback Timeline', '回饋紀錄')}
                                </div>
                                <div style={{ display: 'grid', gap: '10px', marginBottom: '16px' }}>
                                    {feedback.length === 0 ? (
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('No feedback yet.', '目前尚無回饋紀錄。')}</div>
                                    ) : feedback.map((item) => (
                                        <div key={item.feedback_event_id} style={feedbackItemStyle}>
                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px', fontSize: '0.85rem' }}>
                                                {getTranslation(item.decision)} · {item.reviewer_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>
                                                {item.reason_codes?.join(', ') || '--'}
                                            </div>
                                            <div style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>{item.comment || '--'}</div>
                                        </div>
                                    ))}
                                </div>

                                <form onSubmit={handleFeedbackSubmit} style={{ display: 'grid', gap: '12px' }}>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.95rem' }}>
                                        {t('Submit Feedback', '提交回饋')}
                                    </div>
                                    <select
                                        value={feedbackForm.decision}
                                        onChange={(e) => setFeedbackForm((current) => ({ ...current, decision: e.target.value }))}
                                        style={selectStyle}
                                    >
                                        <option value="approve">{t('Approve', '通過')}</option>
                                        <option value="revise">{t('Revise', '修改')}</option>
                                        <option value="reject">{t('Reject', '退回')}</option>
                                    </select>
                                    <input
                                        value={feedbackForm.reason_codes}
                                        onChange={(e) => setFeedbackForm((current) => ({ ...current, reason_codes: e.target.value }))}
                                        placeholder={t('reason codes, comma separated', '原因代碼，逗號分隔')}
                                        style={inputStyle}
                                    />
                                    <textarea
                                        value={feedbackForm.comment}
                                        onChange={(e) => setFeedbackForm((current) => ({ ...current, comment: e.target.value }))}
                                        rows={4}
                                        placeholder={t('review notes', '審核備註')}
                                        style={inputStyle}
                                    />
                                    <button type="submit" style={buttonPrimaryStyle} disabled={submittingFeedback}>
                                        {submittingFeedback ? t('Submitting...', '提交中...') : t('Submit Feedback', '提交回饋')}
                                    </button>
                                </form>
                            </div>
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
};

const detailCardStyle = {
    padding: '16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const selectStyle = {
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.05)',
    color: 'var(--text-primary)',
};

const searchInputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.05)',
    color: 'var(--text-primary)',
    marginBottom: '16px',
    fontSize: '0.85rem',
};

const inputStyle = {
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.05)',
    color: 'var(--text-primary)',
};

const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.18)',
    color: 'var(--text-primary)',
};

const listStyle = {
    margin: 0,
    paddingLeft: '18px',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

const feedbackItemStyle = {
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

export default MetaAndromedaReviewQueue;
