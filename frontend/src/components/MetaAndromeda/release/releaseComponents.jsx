import React from 'react';

import { demoBadgeStyle, detailCardStyle, metricGridStyle } from './releaseShared';

export const ReleaseRecordCard = ({ record, getTranslation, t }) => {
    if (!record) {
        return <div style={{ color: 'var(--text-secondary)' }}>--</div>;
    }

    return (
        <div style={{ display: 'grid', gap: '10px' }}>
            <div style={detailCardStyle}>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Model Version', '模型版本')}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{record.model_version}</div>
                    {record.is_demo_data ? <span style={demoBadgeStyle}>{t('Demo Data', '示範資料')}</span> : null}
                </div>
            </div>
            <div style={metricGridStyle}>
                <Metric label={t('Status', '狀態')} value={getTranslation(record.release_status)} />
                <Metric label={t('Approved By', '核准人員')} value={record.approved_by} />
                <Metric label={t('Pairwise Ranking Accuracy', '成對排序準確率')} value={record.pairwise_ranking_accuracy} />
                <Metric label={t('Mean Band Error', '平均級距誤差')} value={record.mean_band_error} />
            </div>
        </div>
    );
};

export const Metric = ({ label, value }) => (
    <div style={detailCardStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value ?? '--'}</div>
    </div>
);