/**
 * MetricsLab - Experimental Metrics Registry UI
 * 
 * This is a standalone experimental page for testing the Metrics Registry.
 * It does NOT modify the existing Analytics page.
 * 
 * Access via: /lab
 */
import React, { useState, useMemo } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiSearch, FiCheck, FiX, FiFilter, FiGrid, FiList } from 'react-icons/fi';
import {
    METRICS_REGISTRY,
    METRIC_CATEGORIES,
    getMetricsByCategory,
    getDefaultMetrics,
    searchMetrics,
    REGISTRY_STATS
} from '../constants/metricsRegistry';
import './MetricsLab.css';

const MetricsLab = () => {
    const { language = 'zh' } = useOutletContext() || {};

    // State
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState('grid'); // grid | list
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        getDefaultMetrics().map(m => m.key)
    ));
    const [showOnlySelected, setShowOnlySelected] = useState(false);

    // Translations
    const t = {
        zh: {
            title: '🧪 指標實驗室',
            subtitle: '探索與選擇 Facebook 廣告指標',
            search: '搜尋指標...',
            all: '全部',
            selected: '已選擇',
            default: '預設',
            extended: '擴展',
            stats: '統計',
            totalMetrics: '總指標數',
            selectedCount: '已選擇',
            clear: '清除全部',
            selectDefaults: '選擇預設',
            selectAll: '全選',
            showSelected: '只顯示已選',
        },
        en: {
            title: '🧪 Metrics Lab',
            subtitle: 'Explore & Select Facebook Ads Metrics',
            search: 'Search metrics...',
            all: 'All',
            selected: 'Selected',
            default: 'Default',
            extended: 'Extended',
            stats: 'Stats',
            totalMetrics: 'Total Metrics',
            selectedCount: 'Selected',
            clear: 'Clear All',
            selectDefaults: 'Select Defaults',
            selectAll: 'Select All',
            showSelected: 'Show Selected Only',
        }
    };
    const txt = t[language] || t.zh;

    // Filtered metrics
    const filteredMetrics = useMemo(() => {
        let metrics = Object.values(METRICS_REGISTRY);

        // Filter by category
        if (selectedCategory !== 'all') {
            metrics = metrics.filter(m => m.category === selectedCategory);
        }

        // Filter by search query
        if (searchQuery) {
            const lowerQuery = searchQuery.toLowerCase();
            metrics = metrics.filter(m =>
                m.label_zh.toLowerCase().includes(lowerQuery) ||
                m.label_en.toLowerCase().includes(lowerQuery) ||
                m.key.toLowerCase().includes(lowerQuery)
            );
        }

        // Filter by selected only
        if (showOnlySelected) {
            metrics = metrics.filter(m => selectedMetrics.has(m.key));
        }

        return metrics;
    }, [selectedCategory, searchQuery, showOnlySelected, selectedMetrics]);

    // Handlers
    const toggleMetric = (key) => {
        const newSet = new Set(selectedMetrics);
        if (newSet.has(key)) {
            newSet.delete(key);
        } else {
            newSet.add(key);
        }
        setSelectedMetrics(newSet);
    };

    const selectDefaults = () => {
        setSelectedMetrics(new Set(getDefaultMetrics().map(m => m.key)));
    };

    const selectAll = () => {
        setSelectedMetrics(new Set(Object.keys(METRICS_REGISTRY)));
    };

    const clearAll = () => {
        setSelectedMetrics(new Set());
    };

    // Category counts
    const categoryCounts = useMemo(() => {
        const counts = { all: Object.keys(METRICS_REGISTRY).length };
        Object.keys(METRIC_CATEGORIES).forEach(cat => {
            counts[cat] = Object.values(METRICS_REGISTRY).filter(m => m.category === cat).length;
        });
        return counts;
    }, []);

    return (
        <div className="metrics-lab">
            {/* Header */}
            <div className="lab-header">
                <div className="lab-title">
                    <h1>{txt.title}</h1>
                    <p>{txt.subtitle}</p>
                </div>
                <div className="lab-stats">
                    <div className="stat-item">
                        <span className="stat-value">{REGISTRY_STATS.totalMetrics}</span>
                        <span className="stat-label">{txt.totalMetrics}</span>
                    </div>
                    <div className="stat-item highlight">
                        <span className="stat-value">{selectedMetrics.size}</span>
                        <span className="stat-label">{txt.selectedCount}</span>
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="lab-controls">
                {/* Search */}
                <div className="search-box">
                    <FiSearch />
                    <input
                        type="text"
                        placeholder={txt.search}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button onClick={() => setSearchQuery('')} className="clear-btn">
                            <FiX />
                        </button>
                    )}
                </div>

                {/* Actions */}
                <div className="action-buttons">
                    <button onClick={selectDefaults} className="btn-secondary">
                        {txt.selectDefaults}
                    </button>
                    <button onClick={selectAll} className="btn-secondary">
                        {txt.selectAll}
                    </button>
                    <button onClick={clearAll} className="btn-danger">
                        {txt.clear}
                    </button>
                </div>

                {/* View Toggle */}
                <div className="view-toggle">
                    <button
                        className={viewMode === 'grid' ? 'active' : ''}
                        onClick={() => setViewMode('grid')}
                    >
                        <FiGrid />
                    </button>
                    <button
                        className={viewMode === 'list' ? 'active' : ''}
                        onClick={() => setViewMode('list')}
                    >
                        <FiList />
                    </button>
                </div>

                {/* Show Selected Toggle */}
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={showOnlySelected}
                        onChange={(e) => setShowOnlySelected(e.target.checked)}
                    />
                    {txt.showSelected}
                </label>
            </div>

            {/* Category Tabs */}
            <div className="category-tabs">
                <button
                    className={selectedCategory === 'all' ? 'active' : ''}
                    onClick={() => setSelectedCategory('all')}
                >
                    {txt.all} ({categoryCounts.all})
                </button>
                {Object.entries(METRIC_CATEGORIES).map(([key, cat]) => (
                    <button
                        key={key}
                        className={selectedCategory === key ? 'active' : ''}
                        onClick={() => setSelectedCategory(key)}
                        style={{ borderColor: cat.color }}
                    >
                        {cat.icon} {language === 'zh' ? cat.label_zh : cat.label_en} ({categoryCounts[key] || 0})
                    </button>
                ))}
            </div>

            {/* Metrics Grid/List */}
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
                                onClick={() => toggleMetric(metric.key)}
                                style={{ borderColor: isSelected ? category?.color : 'transparent' }}
                            >
                                <div className="metric-header">
                                    <span
                                        className="category-dot"
                                        style={{ backgroundColor: category?.color }}
                                    />
                                    <span className="metric-key">{metric.key}</span>
                                    {metric.is_default && (
                                        <span className="default-badge">{txt.default}</span>
                                    )}
                                    {!metric.is_default && (
                                        <span className="extended-badge">{txt.extended}</span>
                                    )}
                                </div>
                                <div className="metric-label">
                                    {language === 'zh' ? metric.label_zh : metric.label_en}
                                </div>
                                {metric.description_zh && (
                                    <div className="metric-desc">
                                        {language === 'zh' ? metric.description_zh : metric.description_en || metric.description_zh}
                                    </div>
                                )}
                                <div className="metric-footer">
                                    <span className="format-badge">{metric.format}</span>
                                    <span className="source-badge">{metric.source}</span>
                                </div>
                                <div className="check-indicator">
                                    {isSelected ? <FiCheck /> : null}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Footer */}
            <div className="lab-footer">
                <p>
                    {language === 'zh'
                        ? '這是指標資料庫的實驗頁面，不會影響現有的 Analytics 頁面。'
                        : 'This is an experimental page for the Metrics Registry. It does not affect the existing Analytics page.'}
                </p>
            </div>
        </div>
    );
};

export default MetricsLab;
