import React from 'react';
import { OVERVIEW_COLUMN_ORDER } from './constants';
import GA4StatsShared from './GA4StatsShared';

const OverviewSection = ({
    analyticsData,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getMetricLabel,
    isMobile,
    itemsPerPage,
    loadMoreGa4Data,
    setCurrentPage,
    setItemsPerPage,
    setSortConfig,
    sortConfig,
    t
}) => {
    const columns = OVERVIEW_COLUMN_ORDER.filter(col =>
        col === 'averageOrderValue'
        || col === 'purchaseConversionRate'
        || analyticsData.dimensions.includes(col)
        || analyticsData.metrics.includes(col)
    );

    return (
        <GA4StatsShared
            activeTab="overview"
            analyticsData={analyticsData}
            columns={columns}
            currentPage={currentPage}
            ga4HasMore={ga4HasMore}
            ga4LoadingMore={ga4LoadingMore}
            getColumnLabel={getMetricLabel}
            isMobile={isMobile}
            itemsPerPage={itemsPerPage}
            loadMoreGa4Data={loadMoreGa4Data}
            setCurrentPage={setCurrentPage}
            setItemsPerPage={setItemsPerPage}
            setSortConfig={setSortConfig}
            sortConfig={sortConfig}
            t={t}
        />
    );
};

export default OverviewSection;
