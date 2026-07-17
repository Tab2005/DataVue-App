import React from 'react';
import { FiActivity } from 'react-icons/fi';
import { getGroupsByModule } from '../../../constants/analyticsConfig';

const StepMetricSelection = ({ formData, updateField, language, t }) => {
    const currentMetricGroups = getGroupsByModule(formData.module_type);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiActivity color="var(--accent-primary)" /> {t('Step 3: Metric Selection', '步驟 3：指標選擇')}
            </h2>
            <div style={{
                maxHeight: '450px',
                overflowY: 'auto',
                padding: '16px',
                backgroundColor: 'rgba(255,255,255,0.02)',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px'
            }}>
                {currentMetricGroups.map((group) => {
                    const groupKeys = group.metrics.map(m => m.key);
                    const isAllSelected = groupKeys.every(k => formData.selected_metrics.includes(k));

                    const handleToggleGroup = () => {
                        if (isAllSelected) {
                            updateField('selected_metrics', formData.selected_metrics.filter(k => !groupKeys.includes(k)));
                        } else {
                            const otherMetrics = formData.selected_metrics.filter(k => !groupKeys.includes(k));
                            updateField('selected_metrics', [...otherMetrics, ...groupKeys]);
                        }
                    };

                    return (
                        <div key={group.id} style={{ backgroundColor: 'rgba(255, 255, 255, 0.03)', border: `1px solid ${group.color}30`, borderRadius: '12px', padding: '16px' }}>
                            <div style={{ fontSize: '0.9rem', fontWeight: '600', color: group.color, marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: group.color }} />
                                    {language === 'zh' ? group.label_zh : group.label_en}
                                </div>

                                <label style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer',
                                    backgroundColor: isAllSelected ? `${group.color}20` : 'transparent',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    border: `1px solid ${group.color}40`,
                                    transition: 'all 0.2s'
                                }}>
                                    <input type="checkbox" checked={isAllSelected} onChange={handleToggleGroup} style={{ accentColor: group.color, scale: '0.8' }} />
                                    {t('Select All', '全選')}
                                </label>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                {group.metrics.map((metric) => (
                                    <label key={metric.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                                        <input
                                            type="checkbox"
                                            checked={formData.selected_metrics.includes(metric.key)}
                                            onChange={() => {
                                                const current = [...formData.selected_metrics];
                                                if (current.includes(metric.key)) {
                                                    updateField('selected_metrics', current.filter(k => k !== metric.key));
                                                } else {
                                                    updateField('selected_metrics', [...current, metric.key]);
                                                }
                                            }}
                                            style={{ width: '16px', height: '16px', accentColor: group.color, cursor: 'pointer' }}
                                        />
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            {language === 'zh' ? metric.label_zh : metric.label_en}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default StepMetricSelection;
