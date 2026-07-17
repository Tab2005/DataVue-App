import React from 'react';
import { FiCheck, FiEdit } from 'react-icons/fi';
import { METRICS_REGISTRY, METRIC_CATEGORIES } from '../../constants/metricsRegistry';

const EditViewModal = ({
    isOpen,
    editingView,
    editViewName,
    editViewMetrics,
    language,
    txt,
    onClose,
    onNameChange,
    onToggleMetric,
    onUpdate
}) => {
    if (!isOpen || !editingView) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="save-modal edit-modal" onClick={e => e.stopPropagation()}>
                <h3><FiEdit /> {txt.editView}</h3>
                <input
                    type="text"
                    value={editViewName}
                    onChange={(e) => onNameChange(e.target.value)}
                    placeholder={txt.viewNamePlaceholder}
                    autoFocus
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') onUpdate();
                        if (e.key === 'Escape') onClose();
                    }}
                />

                <p className="edit-metrics-hint">
                    {txt.editMetricsHint} ({editViewMetrics.size} {txt.metricsCount})
                </p>

                <div className="edit-metrics-grid">
                    {Object.values(METRICS_REGISTRY).slice(0, 30).map(metric => {
                        const isSelected = editViewMetrics.has(metric.key);
                        const category = METRIC_CATEGORIES[metric.category];
                        return (
                            <div
                                key={metric.key}
                                className={`edit-metric-chip ${isSelected ? 'selected' : ''}`}
                                onClick={() => onToggleMetric(metric.key)}
                                style={{ borderColor: isSelected ? category?.color : 'transparent' }}
                            >
                                <span className="category-dot" style={{ backgroundColor: category?.color }} />
                                {language === 'zh' ? metric.label_zh : metric.label_en}
                                {isSelected && <FiCheck className="check-icon" />}
                            </div>
                        );
                    })}
                </div>

                {Object.values(METRICS_REGISTRY).length > 30 && (
                    <p className="edit-metrics-more">
                        {language === 'zh'
                            ? `… 及其他 ${Object.values(METRICS_REGISTRY).length - 30} 個指標`
                            : `... and ${Object.values(METRICS_REGISTRY).length - 30} more metrics`
                        }
                    </p>
                )}

                <div className="modal-actions">
                    <button onClick={onClose} className="btn-secondary">
                        {txt.cancel}
                    </button>
                    <button
                        onClick={onUpdate}
                        className="btn-primary"
                        disabled={!editViewName.trim() || editViewMetrics.size === 0}
                    >
                        <FiCheck /> {txt.update}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EditViewModal;
