// frontend/src/hooks/useAnalyticsDateControls.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 日期範圍 + 比較期間狀態，原本內嵌在 Analytics.jsx。
import { useState } from 'react';
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths, differenceInDays } from 'date-fns';

export const useAnalyticsDateControls = () => {
    const [datePreset, setDatePreset] = useState('last_7d');
    const [dateRange, setDateRange] = useState({
        since: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        until: format(subDays(new Date(), 1), 'yyyy-MM-dd')
    });
    // Comparison State
    const [isCompareMode, setIsCompareMode] = useState(false);
    const [comparePreset, setComparePreset] = useState('previous_period');
    const [compareDateRange, setCompareDateRange] = useState({ since: '', until: '' });

    const handlePresetChange = (e) => {
        const preset = e.target.value;
        setDatePreset(preset);

        const today = new Date();
        let newRange = { since: '', until: '' };

        switch (preset) {
            case 'today': newRange.since = format(today, 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'yesterday': { const yest = subDays(today, 1); newRange.since = format(yest, 'yyyy-MM-dd'); newRange.until = format(yest, 'yyyy-MM-dd'); break; }
            case 'this_week': newRange.since = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_week': { const start = startOfWeek(subDays(today, 7), { weekStartsOn: 1 }); const end = endOfWeek(subDays(today, 7), { weekStartsOn: 1 }); newRange.since = format(start, 'yyyy-MM-dd'); newRange.until = format(end, 'yyyy-MM-dd'); break; }
            case 'this_month': newRange.since = format(startOfMonth(today), 'yyyy-MM-dd'); newRange.until = format(endOfMonth(today), 'yyyy-MM-dd'); break;
            case 'last_month': { const lm = subMonths(today, 1); newRange.since = format(startOfMonth(lm), 'yyyy-MM-dd'); newRange.until = format(endOfMonth(lm), 'yyyy-MM-dd'); break; }
            case 'last_7d': newRange.since = format(subDays(today, 7), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break; // Exclude today
            case 'last_14d': newRange.since = format(subDays(today, 14), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break;
            case 'last_30d': newRange.since = format(subDays(today, 30), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break;
            case 'custom': return;
        }

        setDateRange(newRange);
    };

    const handleComparePresetChange = (e) => {
        const preset = e.target.value;
        setComparePreset(preset);

        if (preset === 'custom' && (!compareDateRange.since || !compareDateRange.until)) {
            // Calculate previous period as default custom compare dates
            const startDate = new Date(dateRange.since);
            const endDate = new Date(dateRange.until);
            const diffDays = differenceInDays(endDate, startDate) + 1; // Inclusive
            const prevSince = format(subDays(startDate, diffDays), 'yyyy-MM-dd');
            const prevUntil = format(subDays(endDate, diffDays), 'yyyy-MM-dd');
            setCompareDateRange({ since: prevSince, until: prevUntil });
        }
    };

    return {
        datePreset, setDatePreset,
        dateRange, setDateRange,
        isCompareMode, setIsCompareMode,
        comparePreset, setComparePreset,
        compareDateRange, setCompareDateRange,
        handlePresetChange,
        handleComparePresetChange,
    };
};

export default useAnalyticsDateControls;
