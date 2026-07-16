import { useEffect, useMemo, useState } from 'react';
import { getSimilarity } from '../components/GSC/gscUtils';

export const useGscTableData = ({ analytics, activeTab, trendData, trendSubTab, selectedSite, dateRange, rowLimit }) => {
    const [searchKeyword, setSearchKeyword] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'clicks', direction: 'desc' });
    const [displayLimit, setDisplayLimit] = useState(100);
    const [groupingEnabled, setGroupingEnabled] = useState(false);
    const [expandedGroups, setExpandedGroups] = useState(new Set());
    const [expandedPages, setExpandedPages] = useState(new Set());

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setDisplayLimit(100);
    }, [selectedSite, dateRange, activeTab, rowLimit]);

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    const toggleGroup = (groupKey) => {
        setExpandedGroups(prev => {
            const next = new Set(prev);
            if (next.has(groupKey)) next.delete(groupKey);
            else next.add(groupKey);
            return next;
        });
    };

    const togglePageExpand = (pageUrl) => {
        setExpandedPages(prev => {
            const next = new Set(prev);
            if (next.has(pageUrl)) next.delete(pageUrl);
            else next.add(pageUrl);
            return next;
        });
    };

    const getPerformanceIndicator = (index, totalLength) => {
        if (totalLength < 10) return null;
        if (index < 5) return { type: 'top', label: '🏆', color: '#10B981' };
        if (index >= totalLength - 5) return { type: 'bottom', label: '⚠️', color: '#EF4444' };
        return null;
    };

    const groupedData = useMemo(() => {
        if (!groupingEnabled || activeTab !== 'query') return null;
        let data = [...analytics];
        if (searchKeyword) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row => row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch));
        }
        data.sort((a, b) => {
            const aVal = a[sortConfig.key] ?? 0;
            const bVal = b[sortConfig.key] ?? 0;
            return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal;
        });
        const groups = [];
        const assigned = new Set();
        for (let i = 0; i < Math.min(data.length, rowLimit * 2); i++) {
            if (assigned.has(i)) continue;
            const mainQuery = data[i].keys?.[0] || '';
            const group = {
                mainKeyword: mainQuery,
                items: [data[i]],
                totalClicks: data[i].clicks,
                totalImpressions: data[i].impressions
            };
            assigned.add(i);
            for (let j = i + 1; j < Math.min(data.length, rowLimit * 3); j++) {
                if (assigned.has(j)) continue;
                const otherQuery = data[j].keys?.[0] || '';
                if (getSimilarity(mainQuery, otherQuery) >= 0.4) {
                    group.items.push(data[j]);
                    group.totalClicks += data[j].clicks;
                    group.totalImpressions += data[j].impressions;
                    assigned.add(j);
                }
            }
            groups.push(group);
            if (groups.length >= rowLimit) break;
        }
        groups.sort((a, b) => b.totalClicks - a.totalClicks);
        return groups;
    }, [analytics, groupingEnabled, activeTab, searchKeyword, sortConfig, rowLimit]);

    const getSortedFilteredData = () => {
        let data = [...analytics];
        if (searchKeyword && (activeTab === 'query' || activeTab === 'page')) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row => row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch));
        }
        data.sort((a, b) => {
            if (sortConfig.key === 'date') {
                const aVal = a.keys?.[0] || '';
                const bVal = b.keys?.[0] || '';
                return sortConfig.direction === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            }
            const aVal = a[sortConfig.key] ?? 0;
            const bVal = b[sortConfig.key] ?? 0;
            return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal;
        });
        if (activeTab !== 'daily') data = data.slice(0, rowLimit);
        const totalCount = data.length;
        const effectiveLimit = Math.min(displayLimit, totalCount);
        return {
            displayData: data.slice(0, effectiveLimit),
            totalCount,
            hasMore: effectiveLimit < totalCount
        };
    };

    const getSortedTrendData = () => {
        let data = [...trendData];
        if (searchKeyword) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row => row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch));
        }
        switch (trendSubTab) {
            case 'top':
                data.sort((a, b) => b.clicks - a.clicks);
                break;
            case 'up':
                data = data.filter(row => (row.clicks - row.prevClicks) > 0);
                data.sort((a, b) => (b.clicks - b.prevClicks) - (a.clicks - a.prevClicks));
                break;
            case 'down':
                data = data.filter(row => (row.clicks - row.prevClicks) < 0);
                data.sort((a, b) => (a.clicks - a.prevClicks) - (b.clicks - b.prevClicks));
                break;
            default:
                data.sort((a, b) => b.clicks - a.clicks);
        }
        return data.slice(0, rowLimit);
    };

    return {
        searchKeyword,
        setSearchKeyword,
        sortConfig,
        displayLimit,
        setDisplayLimit,
        groupingEnabled,
        setGroupingEnabled,
        expandedGroups,
        expandedPages,
        handleSort,
        toggleGroup,
        togglePageExpand,
        getPerformanceIndicator,
        groupedData,
        getSortedFilteredData,
        getSortedTrendData
    };
};
