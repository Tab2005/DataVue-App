// frontend/src/pages/SharedAnalyticsInsight.jsx (docs/58)
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { FiAlertCircle, FiZap } from 'react-icons/fi';

import { analyticsAiService } from '../services/analyticsAiService';
import PageLoading from '../components/PageLoading';

const LEVEL_LABELS = {
    campaign: { en: 'By Campaign', zh: '按活動名稱' },
    adset: { en: 'By Ad Set', zh: '按廣告組合名稱' },
    ad: { en: 'By Ad', zh: '按廣告名稱' },
    account: { en: 'Account Overview', zh: '整體總覽' },
};

// docs/58：只有 selected_metrics 有帶 format 才需要格式化，跟 Analytics.jsx
// 的 renderMetricValue 同一套邏輯（複製小工具而非共用模組，跟這個資料夾
// 既有慣例一致）。
const formatMetricValue = (val, format) => {
    if (val === undefined || val === null || isNaN(val)) return '-';
    if (format === 'currency') return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    if (format === 'currency_decimal') {
        const isWholeNumber = Number.isInteger(val) || Math.abs(val - Math.round(val)) < 0.01;
        return `$${val.toLocaleString(undefined, { minimumFractionDigits: isWholeNumber ? 0 : 1, maximumFractionDigits: isWholeNumber ? 0 : 1 })}`;
    }
    if (format === 'percent') return `${val.toFixed(2)}%`;
    if (format === 'decimal') return val.toFixed(2);
    return val.toLocaleString();
};

const SharedAnalyticsInsight = () => {
    const { token } = useParams();
    const [snapshot, setSnapshot] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const language = 'zh';
    const t = (en, zh) => (language === 'zh' ? zh : en);

    useEffect(() => {
        const fetchShared = async () => {
            if (!token) return;
            try {
                const res = await analyticsAiService.getSharedSnapshot(token);
                setSnapshot(res);
            } catch (err) {
                console.error('Failed to fetch shared analytics insight:', err);
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

    const payload = snapshot.payload || {};
    const selectedMetrics = payload.selected_metrics || [];
    const rows = payload.rows || [];
    const levelLabel = LEVEL_LABELS[snapshot.level] ? t(LEVEL_LABELS[snapshot.level].en, LEVEL_LABELS[snapshot.level].zh) : snapshot.level;
    const period = `${snapshot.date_since} ~ ${snapshot.date_until}`;

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
                            {t('Ad Performance Analysis', '成效分析')}
                        </span>
                        {snapshot.account_id && (
                            <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>
                                {t(`Ad account ${snapshot.account_id}`, `廣告帳戶 ${snapshot.account_id}`)}
                            </span>
                        )}
                    </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                    <h1 style={{ fontSize: '1.8rem', marginBottom: '6px' }}>{levelLabel}</h1>
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
                        <div style={{ fontWeight: 700, marginBottom: '8px' }}>{t('AI Ad Analyst', 'AI 廣告分析')}</div>
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
                    {rows.length === 0 || selectedMetrics.length === 0 ? (
                        <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '24px', fontSize: '0.9rem' }}>
                            {t('No data.', '暫無資料。')}
                        </div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                    <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                        <th style={{ padding: '6px' }}>{t('Name', '名稱')}</th>
                                        {selectedMetrics.map((m) => (
                                            <th key={m.key} style={{ padding: '6px' }}>{m.label}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map((row, idx) => (
                                        <tr key={`${row.name}-${idx}`} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                            <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.name}>
                                                {row.name}
                                            </td>
                                            {selectedMetrics.map((m) => (
                                                <td key={m.key} style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                    {formatMetricValue(row[m.key], m.format)}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>

                <div style={{ marginTop: '60px', textAlign: 'center', padding: '40px 0', borderTop: '1px solid var(--glass-border)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    © {new Date().getFullYear()} DataVue Analytics. {t('All rights reserved.', '保留所有權利。')}
                </div>
            </div>
        </div>
    );
};

export default SharedAnalyticsInsight;
