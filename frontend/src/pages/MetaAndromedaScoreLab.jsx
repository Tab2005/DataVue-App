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
    const [isDragActive, setIsDragActive] = useState(false);
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

    const getTranslation = (key) => {
        if (!key) return '--';
        const keyLower = String(key).toLowerCase();
        switch (keyLower) {
            case 'status': return t('Status', '狀態');
            case 'attempts': return t('Attempts', '處理次數');
            case 'overall_score': return t('Overall Score', '總評分');
            case 'summary': return t('Summary', '評分摘要說明');
            case 'completed': return t('Completed', '評分完成');
            case 'failed': return t('Failed', '評分失敗');
            case 'pending': return t('Pending', '排隊中');
            case 'processing': return t('Processing', '處理中');
            case 'queued': return t('Queued', '已排隊');
            default: return key;
        }
    };

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
                setError(err.message || t('Polling failed', '輪詢評分狀態失敗'));
                window.clearInterval(intervalId);
            }
        }, 1500);

        return () => window.clearInterval(intervalId);
    }, [scoreResult?.score_event_id, scoreResult?.status]);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragActive(true);
        } else if (e.type === 'dragleave') {
            setIsDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setSelectedFile(e.dataTransfer.files[0]);
            setUploadedAsset(null); // 重設已上傳的素材
        }
    };

    const handleButtonClick = () => {
        document.getElementById('file-upload-input').click();
    };

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
            setError(err.message || t('Upload failed', '素材上傳失敗'));
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
            setError(err.message || t('Submit failed', '送出評分工作失敗'));
        } finally {
            setLoadingSubmit(false);
        }
    };

    const statusLabel = scoreResult?.status
        ? t(`Status: ${scoreResult.status}`, `狀態：${getTranslation(scoreResult.status)}`)
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
                    <h2 style={sectionTitleStyle}>{t('Upload and Submit', '上傳與送出評分')}</h2>
                    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '14px' }}>
                        {/* 拖放上傳區域 */}
                        <div
                            onDragEnter={handleDrag}
                            onDragOver={handleDrag}
                            onDragLeave={handleDrag}
                            onDrop={handleDrop}
                            onClick={handleButtonClick}
                            style={isDragActive ? dropZoneActiveStyle : dropZoneStyle}
                        >
                            <input
                                id="file-upload-input"
                                type="file"
                                style={{ display: 'none' }}
                                accept=".png,.jpg,.jpeg,.webp,.mp4,.mov"
                                onChange={(e) => {
                                    setSelectedFile(e.target.files?.[0] || null);
                                    setUploadedAsset(null);
                                }}
                            />
                            {selectedFile ? (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', width: '100%' }}>
                                    <span style={{ fontSize: '2rem' }}>
                                        {inferAssetType(selectedFile) === 'video' ? '🎥' : '🖼️'}
                                    </span>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 'bold', wordBreak: 'break-all' }}>
                                        {selectedFile.name}
                                    </div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                                    </div>
                                    <button
                                        type="button"
                                        style={{
                                            ...buttonSecondaryStyle,
                                            padding: '4px 12px',
                                            fontSize: '0.85rem',
                                            marginTop: '6px'
                                        }}
                                        onClick={(e) => {
                                            e.stopPropagation(); // 避免點擊清除時觸發彈出視窗
                                            setSelectedFile(null);
                                            setUploadedAsset(null);
                                        }}
                                    >
                                        {t('Clear', '清除重新選擇')}
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <span style={{ fontSize: '2.5rem', opacity: 0.7 }}>📤</span>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>
                                        {t('Drag & drop asset here, or click to select', '將廣告素材拖放到此處，或點擊瀏覽檔案')}
                                    </div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                        {t('Supports PNG, JPG, JPEG, WEBP, MP4, MOV', '支援 PNG, JPG, JPEG, WEBP, MP4, MOV')}
                                    </div>
                                </>
                            )}
                        </div>

                        {selectedFile && !uploadedAsset && (
                            <button
                                type="button"
                                onClick={handleUpload}
                                style={buttonSecondaryStyle}
                                disabled={loadingUpload}
                            >
                                {loadingUpload ? t('Uploading...', '上傳中...') : t('Upload Asset', '上傳素材')}
                            </button>
                        )}

                        {uploadedAsset ? (
                            <div style={{
                                ...detailCardStyle,
                                border: '1px solid rgba(16, 185, 129, 0.3)',
                                background: 'rgba(16, 185, 129, 0.02)'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10b981', fontWeight: 'bold', marginBottom: '8px' }}>
                                    <span>✅</span>
                                    <span>{t('Asset uploaded successfully', '素材上傳成功')}</span>
                                </div>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '4px', fontSize: '0.85rem' }}>
                                    {t('Asset URI', '素材網址 (asset_uri)')}
                                </div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.9rem', wordBreak: 'break-all' }}>
                                    {uploadedAsset.asset_uri}
                                </div>
                                <div style={{ color: 'var(--text-secondary)', marginTop: '8px', fontSize: '0.85rem' }}>
                                    {t('Storage Key: ', '儲存金鑰：')}{uploadedAsset.storage_key}
                                </div>
                            </div>
                        ) : null}

                        <Input label={t('Objective (e.g. purchase)', '行銷目標（例如 purchase）')} value={form.objective} onChange={(value) => setForm({ ...form, objective: value })} />
                        <Input label={t('Placement Family (e.g. all)', '版位系列（例如 all）')} value={form.placement_family} onChange={(value) => setForm({ ...form, placement_family: value })} />
                        <Input label={t('Target Market (e.g. TW)', '目標市場（例如 TW）')} value={form.market} onChange={(value) => setForm({ ...form, market: value })} />
                        <Input label={t('Headline', '廣告標題')} value={form.headline} onChange={(value) => setForm({ ...form, headline: value })} />
                        <Input label={t('CTA', '行動呼籲 (CTA)')} value={form.cta} onChange={(value) => setForm({ ...form, cta: value })} />
                        <TextArea label={t('Primary Text', '廣告主要文字')} value={form.primary_text} onChange={(value) => setForm({ ...form, primary_text: value })} />

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
                    <h2 style={sectionTitleStyle}>{t('Result', '評分結果')}</h2>
                    {!scoreResult ? (
                        <div style={{ color: 'var(--text-secondary)' }}>{statusLabel}</div>
                    ) : (
                        <div style={{ display: 'grid', gap: '12px' }}>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Score Event ID', '評分事件 ID (score_event_id)')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.score_event_id}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{getTranslation('status')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{getTranslation(scoreResult.status)}</div>
                                {polling ? (
                                    <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                        {t('Queued job is being processed by the scoring worker...', '排隊中的工作正在由評分 worker 處理中...')}
                                    </div>
                                ) : null}
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{getTranslation('attempts')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.attempt_count ?? 0}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{getTranslation('overall_score')}</div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{scoreResult.overall_score ?? '--'}</div>
                            </div>
                            <div style={detailCardStyle}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{getTranslation('summary')}</div>
                                <div style={{ color: 'var(--text-primary)', lineHeight: 1.6 }}>
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

const dropZoneStyle = {
    border: '2px dashed var(--glass-border)',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    background: 'rgba(255, 255, 255, 0.01)',
    cursor: 'pointer',
    transition: 'all 0.2s ease-in-out',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
};

const dropZoneActiveStyle = {
    ...dropZoneStyle,
    borderColor: 'var(--accent-primary)',
    background: 'rgba(59, 130, 246, 0.08)',
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
