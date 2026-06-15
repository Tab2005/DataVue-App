import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import {
    fetchMetaAndromedaScore,
    submitMetaAndromedaScore,
    uploadMetaAndromedaAsset,
} from '../services/metaAndromedaWorkflowService';

const inferAssetType = (file) => {
    if (!file) return null;
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    const lower = file.name.toLowerCase();
    if (['.png', '.jpg', '.jpeg', '.webp'].some((ext) => lower.endsWith(ext))) return 'image';
    if (['.mp4', '.mov'].some((ext) => lower.endsWith(ext))) return 'video';
    return null;
};

const terminalStatuses = new Set(['completed', 'failed']);

const MetaAndromedaScoreLab = () => {
    const { isMobile, language } = useOutletContext();
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploadedAsset, setUploadedAsset] = useState(null);
    const [scoreResult, setScoreResult] = useState(null);
    const [loadingUpload, setLoadingUpload] = useState(false);
    const [loadingSubmit, setLoadingSubmit] = useState(false);
    const [polling, setPolling] = useState(false);
    const [error, setError] = useState(null);
    const [form, setForm] = useState({
        request_mode: 'auto',
        objective: 'purchase',
        placement_family: 'all',
        market: 'TW',
        primary_text: '',
        headline: '',
        cta: '',
    });

    const t = (en, zh) => (language === 'en' ? en : zh);

    useEffect(() => {
        if (!scoreResult?.score_event_id || terminalStatuses.has(scoreResult?.status)) {
            setPolling(false);
            return undefined;
        }

        setPolling(true);
        const intervalId = window.setInterval(async () => {
            try {
                const latest = await fetchMetaAndromedaScore(scoreResult.score_event_id);
                setScoreResult(latest);
                if (terminalStatuses.has(latest.status)) {
                    setPolling(false);
                    window.clearInterval(intervalId);
                }
            } catch (err) {
                setPolling(false);
                setError(err.message || 'Polling failed');
                window.clearInterval(intervalId);
            }
        }, 1500);

        return () => window.clearInterval(intervalId);
    }, [scoreResult?.score_event_id, scoreResult?.status]);

    const handleUpload = async () => {
        if (!selectedFile) return;
        const assetType = inferAssetType(selectedFile);
        if (!assetType) {
            setError(t('Unsupported file type.', '不支援的檔案格式。'));
            return;
        }
        setLoadingUpload(true);
        setError(null);
        try {
            const uploaded = await uploadMetaAndromedaAsset(selectedFile, assetType);
            setUploadedAsset(uploaded);
        } catch (err) {
            setError(err.message || 'Upload failed');
        } finally {
            setLoadingUpload(false);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!uploadedAsset) {
            setError(t('Upload an asset first.', '請先上傳素材。'));
            return;
        }
        setLoadingSubmit(true);
        setError(null);
        try {
            const result = await submitMetaAndromedaScore({
                ...form,
                asset_uri: uploadedAsset.asset_uri,
                asset_id: uploadedAsset.asset_id,
                asset_type: uploadedAsset.asset_type,
            });
            setScoreResult(result);
        } catch (err) {
            setError(err.message || 'Submit failed');
        } finally {
            setLoadingSubmit(false);
        }
    };

    const statusLabel = scoreResult?.status
        ? t(`Status: ${scoreResult.status}`, `狀態：${scoreResult.status}`)
        : t('No score result yet.', '目前尚無評分結果。');

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div style={{ marginBottom: '20px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                    Meta Andromeda
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Score Lab', '評分工作台')}
                </h1>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
                gap: '16px'
            }}>
                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Upload and Submit', '上傳與送出')}</h2>
                    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '14px' }}>
                        <input
                            type="file"
                            aria-label="Asset File"
                            accept=".png,.jpg,.jpeg,.webp,.mp4,.mov"
                            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        />
                        <button
                            type="button"
                            onClick={handleUpload}
                            style={buttonSecondaryStyle}
                            disabled={!selectedFile || loadingUpload}
                        >
                            {loadingUpload ? t('Uploading...', '上傳中...') : t('Upload Asset', '上傳素材')}
                        </button>

                        {uploadedAsset ? (
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>asset_uri</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{uploadedAsset.asset_uri}</div>
                                <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                    storage_key: {uploadedAsset.storage_key}
                                </div>
                            </div>
                        ) : null}

                        <Input label="objective" value={form.objective} onChange={(value) => setForm({ ...form, objective: value })} />
                        <Input label="placement_family" value={form.placement_family} onChange={(value) => setForm({ ...form, placement_family: value })} />
                        <Input label="market" value={form.market} onChange={(value) => setForm({ ...form, market: value })} />
                        <Input label="headline" value={form.headline} onChange={(value) => setForm({ ...form, headline: value })} />
                        <Input label="cta" value={form.cta} onChange={(value) => setForm({ ...form, cta: value })} />
                        <TextArea label="primary_text" value={form.primary_text} onChange={(value) => setForm({ ...form, primary_text: value })} />

                        <button
                            type="submit"
                            style={buttonPrimaryStyle}
                            disabled={!uploadedAsset || loadingSubmit || polling}
                        >
                            {loadingSubmit ? t('Submitting...', '送出中...') : t('Submit Score', '送出評分')}
                        </button>
                    </form>
                </section>

                <section style={panelStyle}>
                    <h2 style={sectionTitleStyle}>{t('Result', '結果')}</h2>
                    {!scoreResult ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{statusLabel}</div>
                    ) : (
                        <div style={{ display: 'grid', gap: '12px' }}>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>score_event_id</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.score_event_id}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Status', '狀態')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.status}</div>
                                {polling ? (
                                    <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                        {t('Queued job is being processed by the scoring worker...', '排隊中的工作正在由評分 worker 處理中...')}
                                    </div>
                                ) : null}
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Attempts', '處理次數')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.attempt_count ?? 0}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Overall Score', '總分')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.overall_score ?? '--'}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Summary', '摘要')}</div>
                                <div style={{ color: 'var(--text-primary)' }}>
                                    {scoreResult.explanations?.summary || scoreResult.error_message || '--'}
                                </div>
                            </div>
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
};

const Input = ({ label, value, onChange }) => (
    <label style={{ display: 'grid', gap: '6px', color: 'var(--text-secondary)' }}>
        <span>{label}</span>
        <input value={value} onChange={(e) => onChange(e.target.value)} style={inputStyle} />
    </label>
);

const TextArea = ({ label, value, onChange }) => (
    <label style={{ display: 'grid', gap: '6px', color: 'var(--text-secondary)' }}>
        <span>{label}</span>
        <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={4} style={inputStyle} />
    </label>
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

const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
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

export default MetaAndromedaScoreLab;
