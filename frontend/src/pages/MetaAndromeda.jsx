import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { fetchMetaAndromedaOverview } from '../services/metaAndromedaService';

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
    const errorLabel = language === 'en' ? 'Failed to load overview' : '總覽載入失敗';

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
                            label="Module"
                            value={overview?.module?.name}
                            detail={overview?.module?.status}
                        />
                        <OverviewCard
                            label="Current Slice"
                            value={overview?.summary?.current_slice}
                            detail={overview?.summary?.integration_status}
                        />
                        <OverviewCard
                            label="Next Slice"
                            value={overview?.summary?.next_slice}
                            detail={overview?.module?.phase}
                        />
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : '1.2fr 0.8fr',
                        gap: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>Capabilities</h2>
                            <div style={{ display: 'grid', gap: '12px' }}>
                                {(overview?.capabilities || []).map((item) => (
                                    <div key={item.key} style={capabilityStyle}>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                                            {item.label}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                            {item.status}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>Notes</h2>
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {(overview?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                                        {note}
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
