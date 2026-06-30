import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useOutletContext } from 'react-router-dom';
import { useModuleAccess } from '../hooks/usePermission';
import {
    fetchMetaAndromedaScore,
    submitMetaAndromedaScore,
    uploadMetaAndromedaAsset,
} from '../services/metaAndromedaWorkflowService';
import { getDiagnosticLabel } from '../utils/metaAndromedaLabels';

/* ── constants ── */
const OBJECTIVES = [
    { value: 'purchase',    label: { zh: '購買轉換 (purchase)',    en: 'Purchase Conversion' } },
    { value: 'lead',        label: { zh: '潛在客戶 (lead)',        en: 'Lead Generation' } },
    { value: 'traffic',     label: { zh: '流量 (traffic)',         en: 'Traffic' } },
    { value: 'engagement',  label: { zh: '互動 (engagement)',      en: 'Engagement' } },
    { value: 'awareness',   label: { zh: '品牌知名度 (awareness)', en: 'Brand Awareness' } },
    { value: 'reach',       label: { zh: '觸及人數 (reach)',       en: 'Reach' } },
    { value: 'video_views', label: { zh: '影片觀看 (video_views)', en: 'Video Views' } },
];

const PLACEMENTS = [
    { value: 'all',       label: { zh: '全版位 (all)',         en: 'All Placements' } },
    { value: 'feed',      label: { zh: 'Feed 貼文',            en: 'Feed' } },
    { value: 'reels',     label: { zh: 'Reels / 短影音',       en: 'Reels' } },
    { value: 'stories',   label: { zh: 'Stories',              en: 'Stories' } },
    { value: 'search',    label: { zh: '搜尋結果',             en: 'Search' } },
    { value: 'instream',  label: { zh: 'In-stream 影音廣告',   en: 'In-stream' } },
];

const MARKETS = [
    { value: 'TW', label: 'TW — 台灣' },
    { value: 'US', label: 'US — 美國' },
    { value: 'JP', label: 'JP — 日本' },
    { value: 'HK', label: 'HK — 香港' },
    { value: 'SG', label: 'SG — 新加坡' },
    { value: 'MY', label: 'MY — 馬來西亞' },
    { value: 'TH', label: 'TH — 泰國' },
    { value: 'ID', label: 'ID — 印尼' },
    { value: 'VN', label: 'VN — 越南' },
    { value: 'PH', label: 'PH — 菲律賓' },
];

const REQUEST_MODES = [
    { value: 'auto',                label: { zh: '自動 (auto)',                       en: 'Auto' } },
    { value: 'diagnostic_plus_roas',label: { zh: '診斷 + ROAS 預測',                  en: 'Diagnostic + ROAS' } },
    { value: 'diagnostic_only',     label: { zh: '僅診斷 (不含 ROAS)',                 en: 'Diagnostic Only' } },
];

const ROAS_COLOR = { high: '#10b981', mid: '#f59e0b', low: '#ef4444' };
const TERMINAL = new Set(['completed', 'failed']);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ── helpers ── */
const inferAssetType = (file) => {
    if (!file) return null;
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    const low = file.name.toLowerCase();
    if (['.png', '.jpg', '.jpeg', '.webp'].some(e => low.endsWith(e))) return 'image';
    if (['.mp4', '.mov'].some(e => low.endsWith(e))) return 'video';
    return null;
};

const scoreColor = (score) => {
    if (score == null) return 'var(--text-secondary)';
    if (score >= 75) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
};

const statusLabel = (status, t) => {
    switch (String(status).toLowerCase()) {
        case 'completed':  return t('Completed', '評分完成');
        case 'failed':     return t('Failed', '評分失敗');
        case 'queued':     return t('Queued', '已排隊');
        case 'processing': return t('Processing', '處理中');
        default:           return status;
    }
};

/* ── sub-components ── */
const ScoreGauge = ({ score }) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
        <div style={{
            width: '88px', height: '88px', borderRadius: '50%',
            border: `5px solid ${scoreColor(score)}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: `${scoreColor(score)}18`,
        }}>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: scoreColor(score) }}>
                {score ?? '--'}
            </span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>/ 100</span>
    </div>
);

const Badge = ({ children, color }) => (
    <span style={{
        padding: '2px 9px', borderRadius: '999px', fontSize: '0.72rem', fontWeight: 700,
        background: `${color}22`, color,
    }}>{children}</span>
);

const DriverList = ({ items, color, t, labelKey }) => (
    <div style={cardStyle}>
        <div style={labelSt}>{labelKey}</div>
        {items && items.length > 0
            ? <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {items.map(d => <li key={d} style={{ color }}>{d}</li>)}
              </ul>
            : <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>--</div>
        }
    </div>
);

const HistoryItem = ({ item, selected, onClick, t }) => (
    <button
        type="button"
        onClick={onClick}
        style={{
            ...histItemStyle,
            borderColor: selected ? 'var(--accent-primary)' : 'var(--glass-border)',
            background: selected ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.01)',
        }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.score_event_id}
            </span>
            <div style={{ display: 'flex', gap: '5px', flexShrink: 0 }}>
                {item.overall_score != null && (
                    <Badge color={scoreColor(item.overall_score)}>{item.overall_score}</Badge>
                )}
                {item.roas_band && (
                    <Badge color={ROAS_COLOR[item.roas_band]}>{item.roas_band.toUpperCase()}</Badge>
                )}
            </div>
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', marginTop: '3px' }}>
            {item.objective} · {item.placement_family} · {item.market}
        </div>
    </button>
);

/* ── main component ── */
const MetaAndromedaScoreLab = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('meta_andromeda', selectedTeamId);

    const [selectedFile, setSelectedFile] = useState(null);
    const [localPreviewUrl, setLocalPreviewUrl] = useState(null);
    const [uploadedAsset, setUploadedAsset] = useState(null);
    const [scoreResult, setScoreResult] = useState(null);
    const [history, setHistory] = useState([]); // last 10 submissions this session
    const [loadingUpload, setLoadingUpload] = useState(false);
    const [loadingSubmit, setLoadingSubmit] = useState(false);
    const [polling, setPolling] = useState(false);
    const [error, setError] = useState(null);
    const [isDragActive, setIsDragActive] = useState(false);
    const localPreviewRef = useRef(null);

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
    const lang = language === 'en' ? 'en' : 'zh';

    /* local preview URL lifecycle */
    useEffect(() => {
        if (selectedFile) {
            const url = URL.createObjectURL(selectedFile);
            setLocalPreviewUrl(url);
            localPreviewRef.current = url;
            return () => URL.revokeObjectURL(url);
        }
        setLocalPreviewUrl(null);
    }, [selectedFile]);

    /* polling */
    useEffect(() => {
        if (!scoreResult?.score_event_id || TERMINAL.has(scoreResult?.status)) {
            setPolling(false);
            return undefined;
        }
        setPolling(true);
        const id = window.setInterval(async () => {
            try {
                const latest = await fetchMetaAndromedaScore(scoreResult.score_event_id);
                setScoreResult(latest);
                setHistory(prev => prev.map(h => h.score_event_id === latest.score_event_id ? latest : h));
                if (TERMINAL.has(latest.status)) {
                    setPolling(false);
                    window.clearInterval(id);
                }
            } catch (err) {
                setPolling(false);
                setError(err.message || t('Polling failed', '輪詢評分狀態失敗'));
                window.clearInterval(id);
            }
        }, 1800);
        return () => window.clearInterval(id);
    }, [scoreResult?.score_event_id, scoreResult?.status]);

    const autoUpload = async (file) => {
        const assetType = inferAssetType(file);
        if (!assetType) { setError(t('Unsupported file type.', '不支援的檔案格式。')); return; }
        setLoadingUpload(true);
        setError(null);
        try {
            const uploaded = await uploadMetaAndromedaAsset(file, assetType);
            setUploadedAsset(uploaded);
        } catch (err) {
            setError(err.message || t('Upload failed', '素材上傳失敗'));
        } finally {
            setLoadingUpload(false);
        }
    };

    const handleFileSelect = async (file) => {
        if (!file) return;
        setSelectedFile(file);
        setUploadedAsset(null);
        await autoUpload(file);
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(e.type === 'dragenter' || e.type === 'dragover');
    };

    const handleDrop = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(false);
        const file = e.dataTransfer.files?.[0];
        if (file) await handleFileSelect(file);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!uploadedAsset) { setError(t('Upload an asset first.', '請先上傳素材。')); return; }
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
            setHistory(prev => [result, ...prev].slice(0, 10));
        } catch (err) {
            setError(err.message || t('Submit failed', '送出評分失敗'));
        } finally {
            setLoadingSubmit(false);
        }
    };

    const resetForm = () => {
        setSelectedFile(null);
        setUploadedAsset(null);
        setScoreResult(null);
        setError(null);
    };

    if (accessLoading) return <AccessScreen isMobile={isMobile} t={t} loading />;
    if (!hasAccess)    return <AccessScreen isMobile={isMobile} t={t} />;

    const assetType = selectedFile ? inferAssetType(selectedFile) : null;

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <style>{`
                .sl-scroll::-webkit-scrollbar { width: 5px; }
                .sl-scroll::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 99px; }
                .sl-scroll::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }
                select option { background: #1a1a2e; color: #e2e8f0; }
            `}</style>

            <div style={{ marginBottom: '20px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>Meta Andromeda</div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Score Lab', '評分工作台')}</h1>
            </div>

            {error && <div style={errorPanelStyle}>⚠️ {error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '16px' }}>

                {/* ── LEFT: form ── */}
                <section style={panelStyle}>
                    <h2 style={titleSt}>{t('Upload & Submit', '上傳素材與送出評分')}</h2>

                    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '14px' }}>
                        {/* Drop zone with inline preview */}
                        <div
                            onDragEnter={handleDrag} onDragOver={handleDrag}
                            onDragLeave={handleDrag} onDrop={handleDrop}
                            onClick={() => document.getElementById('sl-file-input').click()}
                            style={isDragActive ? dropActiveStyle : dropStyle}
                        >
                            <input
                                id="sl-file-input"
                                type="file"
                                style={{ display: 'none' }}
                                accept=".png,.jpg,.jpeg,.webp,.mp4,.mov"
                                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
                            />
                            {localPreviewUrl ? (
                                <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                                    {assetType === 'video'
                                        ? <video src={localPreviewUrl} style={{ maxHeight: '160px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} muted playsInline />
                                        : <img src={localPreviewUrl} style={{ maxHeight: '160px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} alt="" />
                                    }
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                        {loadingUpload
                                            ? t('Uploading…', '上傳中…')
                                            : uploadedAsset
                                                ? <span style={{ color: '#10b981', fontWeight: 600 }}>✓ {t('Uploaded', '上傳成功')}</span>
                                                : selectedFile.name
                                        }
                                    </div>
                                    {!loadingUpload && (
                                        <button
                                            type="button"
                                            onClick={e => { e.stopPropagation(); setSelectedFile(null); setUploadedAsset(null); }}
                                            style={{ ...btnSecStyle, padding: '3px 12px', fontSize: '0.78rem' }}
                                        >
                                            {t('Remove', '移除')}
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <>
                                    <span style={{ fontSize: '2.2rem', opacity: 0.6 }}>📤</span>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                                        {t('Drag & drop or click to select', '拖放或點擊選取素材')}
                                    </div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                        PNG · JPG · WEBP · MP4 · MOV
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Upload retry */}
                        {selectedFile && !uploadedAsset && !loadingUpload && (
                            <button type="button" onClick={() => autoUpload(selectedFile)}
                                style={{ ...btnSecStyle, borderColor: '#ef4444', color: '#ef4444', background: 'rgba(239,68,68,0.05)' }}>
                                ⚠️ {t('Upload failed — click to retry', '上傳失敗，點擊重試')}
                            </button>
                        )}

                        {/* Dropdowns row */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <SelectField label={t('Request Mode', '評分模式')} value={form.request_mode}
                                onChange={v => setForm({ ...form, request_mode: v })}>
                                {REQUEST_MODES.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                            </SelectField>
                            <SelectField label={t('Objective', '行銷目標')} value={form.objective}
                                onChange={v => setForm({ ...form, objective: v })}>
                                {OBJECTIVES.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                            </SelectField>
                            <SelectField label={t('Placement', '版位')} value={form.placement_family}
                                onChange={v => setForm({ ...form, placement_family: v })}>
                                {PLACEMENTS.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                            </SelectField>
                            <SelectField label={t('Market', '目標市場')} value={form.market}
                                onChange={v => setForm({ ...form, market: v })}>
                                {MARKETS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </SelectField>
                        </div>

                        {/* Optional text fields */}
                        <div style={{ ...cardStyle, gap: '10px', display: 'grid' }}>
                            <div style={{ ...labelSt, marginBottom: 0 }}>
                                {t('Ad Copy', '廣告文案')}
                                <span style={{ marginLeft: '6px', color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.72rem' }}>
                                    {t('(optional — improves AI scoring accuracy)', '（選填，可提升 AI 評分準確度）')}
                                </span>
                            </div>
                            <InputField
                                label={t('Headline', '廣告標題')}
                                value={form.headline}
                                onChange={v => setForm({ ...form, headline: v })}
                                placeholder={t('e.g. Limited-time offer', '例：限時優惠，立即搶購')}
                            />
                            <InputField
                                label="CTA"
                                value={form.cta}
                                onChange={v => setForm({ ...form, cta: v })}
                                placeholder={t('e.g. Shop Now', '例：立即購買')}
                            />
                            <TextAreaField
                                label={t('Primary Text', '主要文字')}
                                value={form.primary_text}
                                onChange={v => setForm({ ...form, primary_text: v })}
                                placeholder={t('Ad body copy…', '廣告主文…')}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={!uploadedAsset || loadingSubmit || polling || loadingUpload}
                            style={{
                                ...btnPriStyle,
                                opacity: (!uploadedAsset || loadingSubmit || polling || loadingUpload) ? 0.55 : 1,
                                cursor: (!uploadedAsset || loadingSubmit || polling || loadingUpload) ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {loadingUpload ? t('Uploading…', '上傳中…')
                                : loadingSubmit ? t('Submitting…', '送出中…')
                                : polling ? t('Scoring in progress…', '評分進行中…')
                                : t('Submit Score', '送出評分')}
                        </button>
                    </form>
                </section>

                {/* ── RIGHT: result ── */}
                <section style={panelStyle}>
                    <h2 style={titleSt}>{t('Score Result', '評分結果')}</h2>

                    {!scoreResult ? (
                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                            {t('Upload an asset and submit to see the scoring result here.', '上傳素材並送出評分後，結果會顯示在此。')}
                        </div>
                    ) : (
                        <div className="sl-scroll" style={{ display: 'grid', gap: '12px', maxHeight: 'calc(100vh - 280px)', overflowY: 'auto', paddingRight: '4px' }}>

                            {/* Score summary row */}
                            <div style={{ ...cardStyle, display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                                <ScoreGauge score={scoreResult.overall_score} />
                                <div style={{ flex: 1, minWidth: '120px' }}>
                                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                                        {scoreResult.roas_band && (
                                            <Badge color={ROAS_COLOR[scoreResult.roas_band]}>
                                                ROAS {scoreResult.roas_band.toUpperCase()}
                                            </Badge>
                                        )}
                                        <Badge color={TERMINAL.has(scoreResult.status)
                                            ? (scoreResult.status === 'completed' ? '#10b981' : '#ef4444')
                                            : '#f59e0b'}>
                                            {statusLabel(scoreResult.status, t)}
                                        </Badge>
                                        {polling && <span style={{ color: '#f59e0b', fontSize: '0.75rem' }}>⏳ {t('Scoring…', '評分中…')}</span>}
                                    </div>
                                    {scoreResult.lineage && (
                                        <div style={{ color: scoreResult.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                            <span>{scoreResult.lineage.scoring_mode === 'ai' ? '🤖' : '⚙️'}</span>
                                            <span>
                                                {scoreResult.lineage.scoring_mode === 'ai'
                                                    ? `OpenRouter · ${scoreResult.lineage.provider_model || '--'}`
                                                    : t('Heuristic Rule Engine', '啟發式規則引擎')}
                                            </span>
                                        </div>
                                    )}
                                    {scoreResult.lineage?.fallback_reason && (
                                        <div style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '4px' }}>
                                            ⚠️ {scoreResult.lineage.fallback_reason}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* View in records link */}
                            {scoreResult.status === 'completed' && (
                                <Link
                                    to="/meta-andromeda/review-queue"
                                    style={{
                                        display: 'block', textAlign: 'center',
                                        padding: '8px', borderRadius: '10px',
                                        border: '1px solid var(--accent-primary)',
                                        color: 'var(--accent-primary)', fontWeight: 600,
                                        fontSize: '0.85rem', textDecoration: 'none',
                                        background: 'rgba(59,130,246,0.06)',
                                    }}
                                >
                                    {t('→ View in Evaluation Records', '→ 前往評估紀錄查看')}
                                </Link>
                            )}

                            {/* Summary */}
                            <div style={cardStyle}>
                                <div style={labelSt}>{t('AI Summary', 'AI 評分摘要')}</div>
                                <div style={{ color: 'var(--text-primary)', lineHeight: 1.7 }}>
                                    {scoreResult.explanations?.summary || scoreResult.error_message || '--'}
                                </div>
                            </div>

                            {/* Risk tags */}
                            {scoreResult.risk_tags?.length > 0 && (
                                <div style={cardStyle}>
                                    <div style={labelSt}>{t('Risk Tags', '風險標籤')}</div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                                        {scoreResult.risk_tags.map(tag => (
                                            <Badge key={tag} color="#ef4444">{tag}</Badge>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Positive / Negative drivers */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                <DriverList
                                    items={scoreResult.top_positive_drivers}
                                    color="#10b981"
                                    t={t}
                                    labelKey={t('Positive Drivers', '正向因素')}
                                />
                                <DriverList
                                    items={scoreResult.top_negative_drivers}
                                    color="#ef4444"
                                    t={t}
                                    labelKey={t('Risk Drivers', '風險因素')}
                                />
                            </div>

                            {/* Diagnostic breakdown */}
                            {scoreResult.diagnostic_breakdown && Object.keys(scoreResult.diagnostic_breakdown).length > 0 && (
                                <div style={cardStyle}>
                                    <div style={labelSt}>{t('Diagnostic Breakdown', '診斷細項')}</div>
                                    <div style={{ display: 'grid', gap: '7px', marginTop: '8px' }}>
                                        {Object.entries(scoreResult.diagnostic_breakdown).map(([k, v]) => (
                                            <div key={k} style={{ display: 'flex', gap: '10px' }}>
                                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', minWidth: '100px', flexShrink: 0 }}>{getDiagnosticLabel(k, lang)}</span>
                                                <span style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{v}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Reset button */}
                            <button type="button" onClick={resetForm} style={{ ...btnSecStyle, fontSize: '0.82rem' }}>
                                {t('Submit another asset', '評分另一個素材')}
                            </button>
                        </div>
                    )}
                </section>
            </div>

            {/* ── SESSION HISTORY ── */}
            {history.length > 0 && (
                <section style={{ ...panelStyle, marginTop: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h2 style={{ ...titleSt, margin: 0 }}>
                            {t('Session History', '本次 Session 評分記錄')}
                            <span style={{ marginLeft: '8px', color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.78rem' }}>
                                {t(`(${history.length} submissions, latest 10)`, `（共 ${history.length} 筆，最多保留 10 筆）`)}
                            </span>
                        </h2>
                        <button type="button" onClick={() => setHistory([])}
                            style={{ ...btnSecStyle, padding: '4px 10px', fontSize: '0.75rem' }}>
                            {t('Clear', '清除記錄')}
                        </button>
                    </div>
                    <div style={{ display: 'grid', gap: '6px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))' }}>
                        {history.map(item => (
                            <HistoryItem
                                key={item.score_event_id}
                                item={item}
                                selected={scoreResult?.score_event_id === item.score_event_id}
                                onClick={() => setScoreResult(item)}
                                t={t}
                            />
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
};

/* ── access gate ── */
const AccessScreen = ({ isMobile, t, loading }) => (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
        <section style={panelStyle}>
            <h1 style={{ margin: '0 0 8px', color: 'var(--text-primary)' }}>{t('Score Lab', '評分工作台')}</h1>
            <div style={{ color: 'var(--text-secondary)' }}>
                {loading
                    ? t('Checking workspace access…', '正在確認工作區權限…')
                    : t('No access to Meta Andromeda in this workspace.', '此工作區無 Meta Andromeda 存取權限。')}
            </div>
        </section>
    </div>
);

/* ── field sub-components ── */
const SelectField = ({ label, value, onChange, children }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{label}</span>
        <select value={value} onChange={e => onChange(e.target.value)} style={selStyle}>
            {children}
        </select>
    </label>
);

const InputField = ({ label, value, onChange, placeholder }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{label}</span>
        <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={inpStyle} />
    </label>
);

const TextAreaField = ({ label, value, onChange, placeholder }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{label}</span>
        <textarea value={value} onChange={e => onChange(e.target.value)} rows={3} placeholder={placeholder} style={inpStyle} />
    </label>
);

/* ── styles ── */
const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const cardStyle = {
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const titleSt = { margin: '0 0 16px', color: 'var(--text-primary)', fontSize: '1rem' };
const labelSt  = { color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px', fontWeight: 600 };

const dropBase = {
    border: '2px dashed var(--glass-border)',
    borderRadius: '12px',
    padding: '20px 16px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.18s',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    minHeight: '130px',
};
const dropStyle       = { ...dropBase, background: 'rgba(255,255,255,0.01)' };
const dropActiveStyle = { ...dropBase, borderColor: 'var(--accent-primary)', background: 'rgba(59,130,246,0.07)' };

const selStyle = {
    padding: '8px 10px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    appearance: 'auto',
};

const inpStyle = {
    padding: '8px 11px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    resize: 'vertical',
};

const btnPriStyle = {
    padding: '11px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: '#fff',
    fontWeight: 700,
    fontSize: '0.9rem',
    cursor: 'pointer',
    transition: 'opacity 0.15s',
};

const btnSecStyle = {
    padding: '9px 14px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.03)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontSize: '0.85rem',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '14px 16px',
    borderRadius: '12px',
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.2)',
    color: 'var(--text-primary)',
};

const histItemStyle = {
    textAlign: 'left',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'all 0.15s',
    width: '100%',
};

export default MetaAndromedaScoreLab;
