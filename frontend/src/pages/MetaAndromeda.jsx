import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { fetchMetaAndromedaOverview } from '../services/metaAndromedaService';

const OVERVIEW_LABELS = {
    zh: {
        module: '模組',
        currentSlice: '目前階段',
        nextSlice: '下一階段',
        capabilities: '功能能力',
        notes: '說明與備註',
        loadFailed: '總覽載入失敗',
        capabilityLabels: {
            creative_scoring: '創意評分',
            review_queue: '審核佇列',
            monitoring: '監控總覽',
            release_console: '版本控台',
        },
        statusLabels: {
            active: '啟用中',
            in_progress: '進行中',
            registry_backed: '已接入模型登錄',
            interactive: '可互動操作',
            worker_observable: '可追蹤工作程序',
            registry_aware: '已識別版本登錄',
            phase_2_workflow_actions: '第二階段：工作流程操作',
            queue_host_observability_enabled: '已啟用佇列主機觀測能力',
            external_queue_host_and_shared_storage_rollout: '外部佇列主機與共享儲存佈署中',
        },
        notesMap: {
            'Meta Andromeda is being integrated into DataVue incrementally.': 'Meta Andromeda 正逐步整合進 DataVue。',
            'Overview, review queue, monitoring, and release paths are mounted in DataVue.': '模組總覽、審核佇列、監控總覽與版本路徑已掛載到 DataVue。',
            'Feedback, release actions, filesystem storage, and queued scoring are active.': '回饋提交、版本操作、檔案系統儲存與排隊評分功能已啟用。',
            'Scoring runtime now resolves provider/model metadata from the local Meta Andromeda registry.': '評分執行程序目前會從本地 Meta Andromeda registry 解析 provider 與模型中繼資料。',
            'Queue host dispatch, worker audit, and dead-letter observability are now persisted in DataVue DB.': '佇列主機派送、工作程序稽核與死信觀測資料已寫入 DataVue 資料庫。',
            'Shared object storage and external worker deployment are still pending host alignment.': '共享物件儲存與外部 worker 部署仍待主機環境對齊。',
        },
    },
    en: {
        module: 'Module',
        currentSlice: 'Current Slice',
        nextSlice: 'Next Slice',
        capabilities: 'Capabilities',
        notes: 'Notes',
        loadFailed: 'Failed to load overview',
    },
};

const getOverviewCopy = (language) => OVERVIEW_LABELS[language === 'en' ? 'en' : 'zh'];

const translateOverviewValue = (value, language) => {
    if (!value || language === 'en') return value || '-';
    const copy = getOverviewCopy(language);
    return copy.statusLabels?.[value] || value;
};

const translateCapabilityLabel = (item, language) => {
    if (language === 'en') return item?.label || '-';
    const copy = getOverviewCopy(language);
    return copy.capabilityLabels?.[item?.key] || item?.label || '-';
};

const translateNote = (note, language) => {
    if (!note || language === 'en') return note || '-';
    const copy = getOverviewCopy(language);
    return copy.notesMap?.[note] || note;
};

const MetaAndromeda = () => {
    const { language, isMobile } = useOutletContext();
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadOverview = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchMetaAndromedaOverview();
                setOverview(data);
            } catch (err) {
                setError(err.message || 'Failed to load overview');
            } finally {
                setLoading(false);
            }
        };

        loadOverview();
    }, []);

    const title = language === 'en' ? 'Meta Andromeda Overview' : 'Meta Andromeda 整合總覽';
    const subtitle = language === 'en'
        ? 'Current integration status and the next implementation slice.'
        : '目前整合狀態與下一個實作切片。';
    const loadingLabel = language === 'en' ? 'Loading module overview...' : '載入模組總覽中...';
    const copy = getOverviewCopy(language);
    const errorLabel = language === 'en' ? copy.loadFailed : copy.loadFailed;

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--glass-border)',
                borderRadius: '16px',
                padding: '24px',
                marginBottom: '16px'
            }}>
                <div style={{ marginBottom: '12px', color: 'var(--accent-primary)', fontWeight: 700 }}>
                    Meta Andromeda
                </div>
                <h1 style={{ margin: '0 0 12px 0', color: 'var(--text-primary)' }}>
                    {title}
                </h1>
                <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{subtitle}</p>
            </div>

            {loading ? (
                <div style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '16px',
                    padding: '24px',
                    color: 'var(--text-secondary)'
                }}>
                    {loadingLabel}
                </div>
            ) : error ? (
                <div style={{
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    borderRadius: '16px',
                    padding: '24px',
                    color: 'var(--text-primary)'
                }}>
                    <div style={{ fontWeight: 700, marginBottom: '8px' }}>{errorLabel}</div>
                    <div style={{ color: 'var(--text-secondary)' }}>{error}</div>
                </div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        <OverviewCard
                            label={copy.module}
                            value={overview?.module?.name}
                            detail={translateOverviewValue(overview?.module?.status, language)}
                        />
                        <OverviewCard
                            label={copy.currentSlice}
                            value={translateOverviewValue(overview?.summary?.current_slice, language)}
                            detail={translateOverviewValue(overview?.summary?.integration_status, language)}
                        />
                        <OverviewCard
                            label={copy.nextSlice}
                            value={translateOverviewValue(overview?.summary?.next_slice, language)}
                            detail={translateOverviewValue(overview?.module?.phase, language)}
                        />
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : '1.2fr 0.8fr',
                        gap: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{copy.capabilities}</h2>
                            <div style={{ display: 'grid', gap: '12px' }}>
                                {(overview?.capabilities || []).map((item) => (
                                    <div key={item.key} style={capabilityStyle}>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                                            {translateCapabilityLabel(item, language)}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                            {translateOverviewValue(item.status, language)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{copy.notes}</h2>
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {(overview?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                                        {translateNote(note, language)}
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                </>
            )}
        </div>
    );
};

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

const capabilityStyle = {
    padding: '16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const OverviewCard = ({ label, value, detail }) => (
    <div style={panelStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '10px', fontSize: '0.9rem' }}>
            {label}
        </div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '1.15rem', marginBottom: '6px' }}>
            {value || '-'}
        </div>
        <div style={{ color: 'var(--accent-primary)', fontSize: '0.9rem' }}>
            {detail || '-'}
        </div>
    </div>
);

export default MetaAndromeda;
