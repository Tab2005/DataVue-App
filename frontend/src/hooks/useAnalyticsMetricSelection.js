// frontend/src/hooks/useAnalyticsMetricSelection.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 指標選擇（自訂/預設檢視）狀態，原本內嵌在 Analytics.jsx。
import { useEffect, useState } from 'react';

import { VIEW_PRESETS } from '../constants/analyticsConfig';
import { ALL_METRIC_GROUPS, METRIC_GROUPS } from '../components/Analytics/analyticsMetrics';

export const useAnalyticsMetricSelection = () => {
    // Metric Selector State (Default: Select all keys from all groups)
    // Use composite keys "group:metric" to allow independent selection of same metric in different groups
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        METRIC_GROUPS.flatMap(g => g.metrics.map(m => `${g.id}:${m.key}`))
    ));

    // View State
    const [activeView, setActiveView] = useState('summary');

    // UI: Toggle Metric Panel
    const [showMetricPanel, setShowMetricPanel] = useState(false);

    const handleViewChange = (view) => {
        // Toggle logic if clicking "Custom" while already on "Custom"
        if (view === 'custom' && activeView === 'custom') {
            setShowMetricPanel(prev => !prev);
            return;
        }

        setActiveView(view);
        if (view !== 'custom') {
            const presetMetrics = VIEW_PRESETS[view].metrics;
            const newSet = new Set();

            // Map preset simple keys to composite keys
            // Strategy: Find the first occurrence of the metric in any group and add it.
            // This ensures standard presets work visually.
            presetMetrics.forEach(key => {
                for (const group of METRIC_GROUPS) {
                    const match = group.metrics.find(m => m.key === key);
                    if (match) {
                        newSet.add(`${group.id}:${key}`);
                        break; // Stop after first match to avoid duplicates in presets
                    }
                }
            });

            setSelectedMetrics(newSet);
            setShowMetricPanel(false); // Hide panel when using preset
        } else {
            // When switching to custom, always show the panel initially
            setShowMetricPanel(true);
        }
    };

    // Toggle Metric (Checkbox)
    const toggleMetric = (groupId, key) => {
        const compositeKey = `${groupId}:${key}`;
        const newSet = new Set(selectedMetrics);
        if (newSet.has(compositeKey)) {
            newSet.delete(compositeKey);
        } else {
            newSet.add(compositeKey);
        }
        setSelectedMetrics(newSet);
    };

    // Helper to get active columns based on order defined in ALL_METRIC_GROUPS
    const getActiveColumns = () => {
        const cols = [];
        // Flatten groups to preserve order (includes extended metrics)
        ALL_METRIC_GROUPS.forEach(group => {
            group.metrics.forEach(m => {
                const compositeKey = `${group.id}:${m.key}`;
                if (selectedMetrics.has(compositeKey)) {
                    // Add composite key for React unique mapping
                    cols.push({ ...m, uniqueKey: compositeKey });
                }
            });
        });
        return cols;
    };

    const activeCols = getActiveColumns();

    // Initial Load - Set default view to Summary to fix overflow
    useEffect(() => {
        handleViewChange('summary');
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return {
        selectedMetrics, setSelectedMetrics,
        activeView, setActiveView,
        showMetricPanel, setShowMetricPanel,
        handleViewChange,
        toggleMetric,
        activeCols,
    };
};

export default useAnalyticsMetricSelection;
