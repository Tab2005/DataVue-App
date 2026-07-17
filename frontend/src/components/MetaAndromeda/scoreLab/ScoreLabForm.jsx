import {
    InputField,
    SelectField,
    TextAreaField,
} from './scoreLabComponents';
import {
    btnPriStyle,
    btnSecStyle,
    cardStyle,
    dropActiveStyle,
    dropStyle,
    labelSt,
    MARKETS,
    OBJECTIVES,
    panelStyle,
    PLACEMENTS,
    REQUEST_MODES,
    titleSt,
} from './scoreLabShared';

const ScoreLabForm = ({ lab, lang, t }) => (
    <section style={panelStyle}>
        <h2 style={titleSt}>{t('Upload & Submit', '上傳素材與送出評分')}</h2>

        <form onSubmit={lab.handleSubmit} style={{ display: 'grid', gap: '14px' }}>
            <AssetDropZone lab={lab} t={t} />

            {lab.selectedFile && !lab.uploadedAsset && !lab.loadingUpload && (
                <button
                    type="button"
                    onClick={() => lab.autoUpload(lab.selectedFile)}
                    style={{ ...btnSecStyle, borderColor: '#ef4444', color: '#ef4444', background: 'rgba(239,68,68,0.05)' }}
                >
                    {t('Upload failed - click to retry', '上傳失敗，點擊重試')}
                </button>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <SelectField label={t('Request Mode', '評分模式')} value={lab.form.request_mode}
                    onChange={v => lab.setForm({ ...lab.form, request_mode: v })}>
                    {REQUEST_MODES.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                </SelectField>
                <SelectField label={t('Objective', '行銷目標')} value={lab.form.objective}
                    onChange={v => lab.setForm({ ...lab.form, objective: v })}>
                    {OBJECTIVES.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                </SelectField>
                <SelectField label={t('Placement', '版位')} value={lab.form.placement_family}
                    onChange={v => lab.setForm({ ...lab.form, placement_family: v })}>
                    {PLACEMENTS.map(o => <option key={o.value} value={o.value}>{o.label[lang]}</option>)}
                </SelectField>
                <SelectField label={t('Market', '目標市場')} value={lab.form.market}
                    onChange={v => lab.setForm({ ...lab.form, market: v })}>
                    {MARKETS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </SelectField>
            </div>

            <div style={{ ...cardStyle, gap: '10px', display: 'grid' }}>
                <div style={{ ...labelSt, marginBottom: 0 }}>
                    {t('Ad Copy', '廣告文案')}
                    <span style={{ marginLeft: '6px', color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.72rem' }}>
                        {t('(optional - improves AI scoring accuracy)', '（選填，可提升 AI 評分準確度）')}
                    </span>
                </div>
                <InputField
                    label={t('Headline', '廣告標題')}
                    value={lab.form.headline}
                    onChange={v => lab.setForm({ ...lab.form, headline: v })}
                    placeholder={t('e.g. Limited-time offer', '例：限時優惠，立即搶購')}
                />
                <InputField
                    label="CTA"
                    value={lab.form.cta}
                    onChange={v => lab.setForm({ ...lab.form, cta: v })}
                    placeholder={t('e.g. Shop Now', '例：立即購買')}
                />
                <TextAreaField
                    label={t('Primary Text', '主要文字')}
                    value={lab.form.primary_text}
                    onChange={v => lab.setForm({ ...lab.form, primary_text: v })}
                    placeholder={t('Ad body copy...', '廣告主文...')}
                />
            </div>

            <button
                type="submit"
                disabled={!lab.uploadedAsset || lab.loadingSubmit || lab.polling || lab.loadingUpload}
                style={{
                    ...btnPriStyle,
                    opacity: (!lab.uploadedAsset || lab.loadingSubmit || lab.polling || lab.loadingUpload) ? 0.55 : 1,
                    cursor: (!lab.uploadedAsset || lab.loadingSubmit || lab.polling || lab.loadingUpload) ? 'not-allowed' : 'pointer',
                }}
            >
                {lab.loadingUpload ? t('Uploading...', '上傳中...')
                    : lab.loadingSubmit ? t('Submitting...', '送出中...')
                        : lab.polling ? t('Scoring in progress...', '評分進行中...')
                            : t('Submit Score', '送出評分')}
            </button>
        </form>
    </section>
);

const AssetDropZone = ({ lab, t }) => (
    <div
        onDragEnter={lab.handleDrag}
        onDragOver={lab.handleDrag}
        onDragLeave={lab.handleDrag}
        onDrop={lab.handleDrop}
        onClick={() => document.getElementById('sl-file-input')?.click()}
        style={lab.isDragActive ? dropActiveStyle : dropStyle}
    >
        <input
            id="sl-file-input"
            type="file"
            style={{ display: 'none' }}
            accept=".png,.jpg,.jpeg,.webp,.mp4,.mov"
            onChange={e => {
                const file = e.target.files?.[0];
                if (file) lab.handleFileSelect(file);
            }}
        />
        {lab.localPreviewUrl ? (
            <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                {lab.assetType === 'video'
                    ? <video src={lab.localPreviewUrl} style={{ maxHeight: '160px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} muted playsInline />
                    : <img src={lab.localPreviewUrl} style={{ maxHeight: '160px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain' }} alt="" />
                }
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    {lab.loadingUpload
                        ? t('Uploading...', '上傳中...')
                        : lab.uploadedAsset
                            ? <span style={{ color: '#10b981', fontWeight: 600 }}>{t('Uploaded', '上傳成功')}</span>
                            : lab.selectedFile?.name
                    }
                </div>
                {!lab.loadingUpload && (
                    <button
                        type="button"
                        onClick={e => {
                            e.stopPropagation();
                            lab.clearSelectedAsset();
                        }}
                        style={{ ...btnSecStyle, padding: '3px 12px', fontSize: '0.78rem' }}
                    >
                        {t('Remove', '移除')}
                    </button>
                )}
            </div>
        ) : (
            <>
                <span style={{ fontSize: '1.1rem', opacity: 0.75 }}>{t('Upload asset', '上傳素材')}</span>
                <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {t('Drag & drop or click to select', '拖放或點擊選取素材')}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                    PNG · JPG · WEBP · MP4 · MOV
                </div>
            </>
        )}
    </div>
);

export default ScoreLabForm;
