/**
 * MetricsManager - Metrics Management Page
 *
 * This page allows users to browse, select and save metric configurations.
 * Saved views can be used in the Analytics page.
 *
 * Access via: /metrics
 */
import React, { useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiCheck, FiGrid, FiList, FiSave, FiSearch, FiX } from 'react-icons/fi';
import EditViewModal from '../components/MetricsManager/EditViewModal';
import MetricCardGrid from '../components/MetricsManager/MetricCardGrid';
import SaveViewModal from '../components/MetricsManager/SaveViewModal';
import SavedViewsSection from '../components/MetricsManager/SavedViewsSection';
import metricsManagerTranslations from '../components/MetricsManager/metricsManagerTranslations';
import { METRICS_REGISTRY, METRIC_CATEGORIES, getDefaultMetrics, REGISTRY_STATS } from '../constants/metricsRegistry';
import useSavedMetricViews from '../hooks/useSavedMetricViews';
import './MetricsManager.css';

const MetricsManager = () => {
    const { language = 'zh', user, selectedTeamId } = useOutletContext() || {};
    const txt = metricsManagerTranslations[language] || metricsManagerTranslations.zh;

    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState('grid');
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        getDefaultMetrics().map(m => m.key)
    ));
    const [showOnlySelected, setShowOnlySelected] = useState(false);

    const savedViewState = useSavedMetricViews({
        user,
        selectedTeamId,
        language,
        selectedMetrics,
        setSelectedMetrics,
        txt
    });

    const filteredMetrics = useMemo(() => {
        let metrics = Object.values(METRICS_REGISTRY);

        if (selectedCategory !== 'all') {
            metrics = metrics.filter(m => m.category === selectedCategory);
        }

        if (searchQuery) {
            const lowerQuery = searchQuery.toLowerCase();
            metrics = metrics.filter(m =>
                m.label_zh.toLowerCase().includes(lowerQuery) ||
                m.label_en.toLowerCase().includes(lowerQuery) ||
                m.key.toLowerCase().includes(lowerQuery)
            );
        }

        if (showOnlySelected) {
            metrics = metrics.filter(m => selectedMetrics.has(m.key));
        }

        return metrics;
    }, [selectedCategory, searchQuery, showOnlySelected, selectedMetrics]);

    const categoryCounts = useMemo(() => {
        const counts = { all: Object.keys(METRICS_REGISTRY).length };
        Object.keys(METRIC_CATEGORIES).forEach(cat => {
            counts[cat] = Object.values(METRICS_REGISTRY).filter(m => m.category === cat).length;
        });
        return counts;
    }, []);

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

    return (
        <div className="metrics-lab">
            {savedViewState.saveMessage && (
                <div className="toast-message">
                    <FiCheck /> {savedViewState.saveMessage}
                </div>
            )}

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

            <div className="lab-controls">
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
                    <button
                        onClick={() => savedViewState.setShowSaveModal(true)}
                        className="btn-primary"
                        disabled={selectedMetrics.size === 0}
                    >
                        <FiSave /> {txt.saveView}
                    </button>
                </div>

                <div className="view-toggle">
                    <button className={viewMode === 'grid' ? 'active' : ''} onClick={() => setViewMode('grid')}>
                        <FiGrid />
                    </button>
                    <button className={viewMode === 'list' ? 'active' : ''} onClick={() => setViewMode('list')}>
                        <FiList />
                    </button>
                </div>

                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={showOnlySelected}
                        onChange={(e) => setShowOnlySelected(e.target.checked)}
                    />
                    {txt.showSelected}
                </label>
            </div>

            <SavedViewsSection
                savedViews={savedViewState.savedViews}
                txt={txt}
                onLoadView={savedViewState.handleLoadView}
                onEditView={savedViewState.handleEditView}
                onDeleteView={savedViewState.handleDeleteView}
            />

            <SaveViewModal
                isOpen={savedViewState.showSaveModal}
                selectedMetrics={selectedMetrics}
                selectedTeamId={selectedTeamId}
                newViewName={savedViewState.newViewName}
                saveToTeam={savedViewState.saveToTeam}
                txt={txt}
                onClose={() => savedViewState.setShowSaveModal(false)}
                onNameChange={savedViewState.setNewViewName}
                onSaveToTeamChange={savedViewState.setSaveToTeam}
                onSave={savedViewState.handleSaveView}
            />

            <EditViewModal
                isOpen={savedViewState.showEditModal}
                editingView={savedViewState.editingView}
                editViewName={savedViewState.editViewName}
                editViewMetrics={savedViewState.editViewMetrics}
                language={language}
                txt={txt}
                onClose={() => savedViewState.setShowEditModal(false)}
                onNameChange={savedViewState.setEditViewName}
                onToggleMetric={savedViewState.toggleEditMetric}
                onUpdate={savedViewState.handleUpdateView}
            />

            <MetricCardGrid
                filteredMetrics={filteredMetrics}
                selectedMetrics={selectedMetrics}
                selectedCategory={selectedCategory}
                categoryCounts={categoryCounts}
                viewMode={viewMode}
                language={language}
                txt={txt}
                onSelectCategory={setSelectedCategory}
                onToggleMetric={toggleMetric}
            />

            <div className="lab-footer">
                <p>
                    {language === 'zh'
                        ? '✅ 已選擇的指標可以儲存為自訂視角，稍後可在 Analytics 頁面使用。'
                        : '✅ Selected metrics can be saved as custom views for later use in the Analytics page.'}
                </p>
            </div>
        </div>
    );
};

export default MetricsManager;
