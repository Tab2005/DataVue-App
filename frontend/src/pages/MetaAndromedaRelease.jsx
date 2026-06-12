import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { usePermission } from '../hooks/usePermission';
import {
    approveMetaAndromedaRelease,
    fetchMetaAndromedaReleaseOverview,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
} from '../services/metaAndromedaReleaseService';

const MetaAndromedaRelease = () => {
    const { isMobile, language } = useOutletContext();
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);
    const { hasPermission: canRelease, loading: loadingReleasePermission } = usePermission('meta_andromeda:release');

    const t = (en, zh) => (language === 'en' ? en : zh);

    const loadOverview = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaReleaseOverview();
            setOverview(data);
        } catch (err) {
            setError(err.message || 'Failed to load release overview');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadOverview();
    }, []);

    const handleReleaseAction = async (action, modelVersion) => {
        const note = window.prompt(
            t('Optional note for this action', '請輸入這次操作的備註（可留空）'),
            ''
        );

        setSubmitting(true);
        setError(null);
        setActionMessage(null);
        try {
            const payload = { model_version: modelVersion, note: note || null };
            const result = action === 'approve'
                ? await approveMetaAndromedaRelease(payload)
                : action === 'reject'
                    ? await rejectMetaAndromedaRelease(payload)
                    : await rollbackMetaAndromedaRelease(payload);
            setActionMessage(`${result.action}: ${result.model_version}`);
            await loadOverview();
        } catch (err) {
            setError(err.message || 'Failed to execute release action');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div style={{ marginBottom: '20px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                    Meta Andromeda
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Release Overview', '版本釋出總覽')}
                </h1>
            </div>

            {actionMessage ? <div style={successPanelStyle}>{actionMessage}</div> : null}
            {loading ? (
                <div style={panelStyle}>{t('Loading release overview...', '載入版本總覽中...')}</div>
            ) : error ? (
                <div style={errorPanelStyle}>{error}</div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Current Production', '目前 Production')}</h2>
                            <ReleaseRecordCard record={overview?.current_production} />
                            {!loadingReleasePermission && canRelease ? (
                                <button
                                    type="button"
                                    style={{ ...buttonSecondaryStyle, marginTop: '16px' }}
                                    disabled={submitting}
                                    onClick={() => handleReleaseAction('rollback', overview?.current_production?.model_version)}
                                >
                                    {submitting ? t('Submitting...', '送出中...') : t('Rollback to Previous', '回滾到前一版')}
                                </button>
                            ) : null}
                        </section>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Previous Production', '前一版 Production')}</h2>
                            <ReleaseRecordCard record={overview?.previous_production} />
                        </section>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : '1.1fr 0.9fr',
                        gap: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Candidates', '候選版本')}</h2>
                            <div style={{ display: 'grid', gap: '12px' }}>
                                {(overview?.candidates || []).map((candidate) => (
                                    <div key={candidate.model_version} style={detailCardStyle}>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '8px' }}>
                                            {candidate.model_version}
                                        </div>
                                        <div style={{ display: 'grid', gap: '8px', color: 'var(--text-secondary)' }}>
                                            <div>status: {candidate.release_status}</div>
                                            <div>pairwise_ranking_accuracy: {candidate.pairwise_ranking_accuracy}</div>
                                            <div>mean_band_error: {candidate.mean_band_error}</div>
                                        </div>
                                        <div style={{ display: 'grid', gap: '6px', marginTop: '12px', fontSize: '0.9rem' }}>
                                            {Object.entries(candidate.promotion_gate_summary || {}).map(([key, value]) => (
                                                <div key={key} style={gateRowStyle}>
                                                    <span style={{ color: 'var(--text-secondary)' }}>{key}</span>
                                                    <strong style={{ color: value ? '#10b981' : '#ef4444' }}>
                                                        {String(value)}
                                                    </strong>
                                                </div>
                                            ))}
                                        </div>
                                        {!loadingReleasePermission && canRelease ? (
                                            <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
                                                <button
                                                    type="button"
                                                    style={buttonPrimaryStyle}
                                                    disabled={submitting}
                                                    onClick={() => handleReleaseAction('approve', candidate.model_version)}
                                                >
                                                    {t('Approve', '批准')}
                                                </button>
                                                <button
                                                    type="button"
                                                    style={buttonSecondaryStyle}
                                                    disabled={submitting}
                                                    onClick={() => handleReleaseAction('reject', candidate.model_version)}
                                                >
                                                    {t('Reject', '退回')}
                                                </button>
                                            </div>
                                        ) : null}
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Release History', '版本歷史')}</h2>
                            <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
                                {(overview?.history || []).map((item, index) => (
                                    <div key={index} style={detailCardStyle}>
                                        <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px' }}>
                                            {item.action} · {item.model_version}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {item.actor} · {item.created_at}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: '6px' }}>
                                            {item.note || '--'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'grid', gap: '8px' }}>
                                {(overview?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {note}
                                    </div>
                                ))}
                            </div>
                            {!loadingReleasePermission && !canRelease ? (
                                <div style={infoPanelStyle}>
                                    {t(
                                        'Release actions require meta_andromeda:release. You currently have read-only visibility.',
                                        '執行 release action 需要 meta_andromeda:release 權限，目前你只有唯讀可見權。'
                                    )}
                                </div>
                            ) : null}
                        </section>
                    </div>
                </>
            )}
        </div>
    );
};

const ReleaseRecordCard = ({ record }) => {
    if (!record) {
        return <div style={{ color: 'var(--text-secondary)' }}>--</div>;
    }

    return (
        <div style={{ display: 'grid', gap: '10px' }}>
            <div style={detailCardStyle}>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>model_version</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{record.model_version}</div>
            </div>
            <div style={metricGridStyle}>
                <Metric label="status" value={record.release_status} />
                <Metric label="approved_by" value={record.approved_by} />
                <Metric label="pairwise_ranking_accuracy" value={record.pairwise_ranking_accuracy} />
                <Metric label="mean_band_error" value={record.mean_band_error} />
            </div>
        </div>
    );
};

const Metric = ({ label, value }) => (
    <div style={detailCardStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value ?? '--'}</div>
    </div>
);

const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const metricGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
};

const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const gateRowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
};

const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

const buttonSecondaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
    color: 'var(--text-primary)',
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

const successPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(16, 185, 129, 0.12)',
    border: '1px solid rgba(16, 185, 129, 0.25)',
    color: 'var(--text-primary)',
};

const infoPanelStyle = {
    marginTop: '16px',
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.18)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

export default MetaAndromedaRelease;
