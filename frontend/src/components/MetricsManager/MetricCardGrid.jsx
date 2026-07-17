import React from 'react';
import { FiCheck } from 'react-icons/fi';
import { METRIC_CATEGORIES } from '../../constants/metricsRegistry';

const MetricCardGrid = ({
    filteredMetrics,
    selectedMetrics,
    selectedCategory,
    categoryCounts,
    viewMode,
    language,
    txt,
    onSelectCategory,
    onToggleMetric
}) => (
    <>
        <div className="category-tabs">
            <button
                className={selectedCategory === 'all' ? 'active' : ''}
                onClick={() => onSelectCategory('all')}
            >
                {txt.all} ({categoryCounts.all})
            </button>
            {Object.entries(METRIC_CATEGORIES).map(([key, cat]) => (
                <button
                    key={key}
                    className={selectedCategory === key ? 'active' : ''}
                    onClick={() => onSelectCategory(key)}
                    style={{ borderColor: cat.color }}
                >
                    {cat.icon} {language === 'zh' ? cat.label_zh : cat.label_en} ({categoryCounts[key] || 0})
                </button>
            ))}
        </div>

        <div className={`metrics-container ${viewMode}`}>
            {filteredMetrics.length === 0 ? (
                <div className="empty-state">
                    {language === 'zh' ? '找不到符合的指標' : 'No metrics found'}
                </div>
            ) : (
                filteredMetrics.map(metric => {
                    const isSelected = selectedMetrics.has(metric.key);
                    const category = METRIC_CATEGORIES[metric.category];

                    return (
                        <div
                            key={metric.key}
                            className={`metric-card ${isSelected ? 'selected' : ''}`}
                            onClick={() => onToggleMetric(metric.key)}
                            style={{ borderColor: isSelected ? category?.color : 'transparent' }}
                        >
                            <div className="metric-header">
                                <span className="category-dot" style={{ backgroundColor: category?.color }} />
                                <span className="metric-key">{metric.key}</span>
                            </div>
                            <div className="metric-label">
                                {language === 'zh' ? metric.label_zh : metric.label_en}
                            </div>
                            {metric.description_zh && (
                                <div className="metric-desc">
                                    {language === 'zh' ? metric.description_zh : metric.description_en || metric.description_zh}
                                </div>
                            )}

                            <div className="check-indicator">
                                {isSelected ? <FiCheck /> : null}
                            </div>
                        </div>
                    );
                })
            )}
        </div>
    </>
);

export default MetricCardGrid;
