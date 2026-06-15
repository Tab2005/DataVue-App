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

    const t = (en, zh) => (language === 'en' ? en : zh);

    const loadQueue = async ({ preserveSelection = true } = {}) => {
        setLoadingQueue(true);
        setError(null);
        try {
            const reviewed = reviewedFilter === 'all' ? null : reviewedFilter === 'reviewed';
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                reviewed,
                limit: 30,
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
            setError(err.message || 'Failed to load review queue');
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
            setError(err.message || 'Failed to load review detail');
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
            setError(err.message || 'Failed to submit feedback');
        } finally {
            setSubmittingFeedback(false);
        }
    };

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
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
                gridTemplateColumns: isMobile ? '1fr' : '0.95fr 1.05fr',
                gap: '16px'
            }}>
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Queue Items', '佇列項目')}</h2>
                    {loadingQueue ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading queue...', '載入佇列中...')}</div>
                    ) : queueItems.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('No queue items found.', '目前沒有符合條件的項目。')}</div>
                    ) : (
                        <div style={{ display: 'grid', gap: '12px' }}>
                            {queueItems.map((item) => (
                                <button
                                    key={item.score_event_id}
                                    type="button"
                                    onClick={() => setSelectedId(item.score_event_id)}
                                    style={{
                                        ...queueItemStyle,
                                        borderColor: selectedId === item.score_event_id
                                            ? 'var(--accent-primary)'
                                            : 'var(--glass-border)',
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '10px' }}>
                                        <strong style={{ color: 'var(--text-primary)' }}>{item.score_event_id}</strong>
                                        <span style={{
                                            padding: '4px 8px',
                                            borderRadius: '999px',
                                            background: statusToneMap[item.status] || 'rgba(255,255,255,0.08)',
                                            color: 'var(--text-primary)',
                                            fontSize: '0.8rem'
                                        }}>
                                            {item.status}
                                        </span>
                                    </div>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>
                                        {item.objective} / {item.placement_family} / {item.market}
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                        <span>score: {item.overall_score ?? '--'}</span>
                                        <span>{item.reviewed ? t('reviewed', '已審核') : t('pending', '待審核')}</span>
                                        {item.latest_feedback_decision ? <span>{item.latest_feedback_decision}</span> : null}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </section>

                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Selected Detail', '所選明細')}</h2>
                    {loadingDetail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Loading detail...', '載入明細中...')}</div>
                    ) : !detail ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{t('Select a queue item.', '請先選擇一筆佇列項目。')}</div>
                    ) : (
                        <div style={{ display: 'grid', gap: '16px' }}>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>score_event_id</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.score_event_id}</div>
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                                gap: '12px'
                            }}>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Status', '狀態')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.status}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Asset Type', '素材類型')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.asset_type}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Model Version', '模型版本')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.model_version || '--'}</div>
                                </div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Summary', '摘要')}</div>
                                <div style={{ color: 'var(--text-primary)' }}>
                                    {detail.explanations?.summary || t('No summary available yet.', '目前尚無摘要。')}
                                </div>
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                                gap: '12px'
                            }}>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Overall Score', '總分')}</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{detail.overall_score ?? '--'}</div>
                                </div>
                                <div style={detailCardStyle}>
                                    <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>ROAS band</div>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                        {detail.roas_prediction?.band || '--'}
                                    </div>
                                </div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Positive Drivers', '正向因素')}</div>
                                <ul style={listStyle}>
                                    {(detail.top_positive_drivers || []).map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>{t('Risk Drivers', '風險因素')}</div>
                                <ul style={listStyle}>
                                    {(detail.top_negative_drivers || []).map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '12px' }}>
                                    {t('Feedback Timeline', '回饋紀錄')}
                                </div>
                                <div style={{ display: 'grid', gap: '10px', marginBottom: '16px' }}>
                                    {feedback.length === 0 ? (
                                        <div style={{ color: 'var(--text-secondary)' }}>{t('No feedback yet.', '目前尚無回饋紀錄。')}</div>
                                    ) : feedback.map((item) => (
                                        <div key={item.feedback_event_id} style={feedbackItemStyle}>
                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px' }}>
                                                {item.decision} · {item.reviewer_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                                {item.reason_codes?.join(', ') || '--'}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)' }}>{item.comment || '--'}</div>
                                        </div>
                                    ))}
                                </div>

                                <form onSubmit={handleFeedbackSubmit} style={{ display: 'grid', gap: '12px' }}>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
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
    padding: '16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
    cursor: 'pointer',
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
    background: 'var(--bg-secondary)',
    color: 'var(--text-primary)',
};

const inputStyle = {
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'var(--bg-secondary)',
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
