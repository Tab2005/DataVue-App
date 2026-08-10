// frontend/src/hooks/useAnalyticsSort.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
import { useMemo, useState } from 'react';

export const useAnalyticsSort = ({ filteredData }) => {
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'desc' });

    const handleSort = (key) => {
        let direction = 'desc';
        if (sortConfig.key === key && sortConfig.direction === 'desc') {
            direction = 'asc';
        }
        setSortConfig({ key, direction });
    };

    const sortedData = useMemo(() => {
        if (!filteredData) return [];
        let sortableItems = [...filteredData];
        if (sortConfig.key !== null) {
            sortableItems.sort((a, b) => {
                let aValue = a[sortConfig.key];
                let bValue = b[sortConfig.key];

                // Handle missing values
                if (aValue === undefined || aValue === null) aValue = -Infinity; // Treat nulls as smallest
                if (bValue === undefined || bValue === null) bValue = -Infinity;

                // Numeric sort
                if (typeof aValue === 'number' && typeof bValue === 'number') {
                    return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
                }

                // String sort (fallback)
                aValue = String(aValue).toLowerCase();
                bValue = String(bValue).toLowerCase();
                if (aValue < bValue) {
                    return sortConfig.direction === 'asc' ? -1 : 1;
                }
                if (aValue > bValue) {
                    return sortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [filteredData, sortConfig]);

    return { sortConfig, handleSort, sortedData };
};

export default useAnalyticsSort;
