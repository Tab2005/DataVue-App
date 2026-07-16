import React from 'react';
import {
    BEHAVIOR_DIMENSIONS,
    CONTENT_DIMENSIONS,
    ECOMMERCE_DIMENSIONS,
    TRAFFIC_DIMENSIONS,
    TRAFFIC_SECONDARY_DIMENSIONS
} from './constants';
import { formatNumber } from './ga4Formatters';

const isDimensionColumn = (col) => (
    TRAFFIC_DIMENSIONS.some(d => d.key === col)
    || BEHAVIOR_DIMENSIONS.some(d => d.key === col)
    || ECOMMERCE_DIMENSIONS.some(d => d.key === col)
    || TRAFFIC_SECONDARY_DIMENSIONS.some(d => d.key === col)
    || CONTENT_DIMENSIONS.some(d => d.key === col)
);

const withCalculatedMetrics = (row, activeTab) => {
    const purchases = parseFloat(row.ecommercePurchases) || 0;
    const revenue = parseFloat(row.purchaseRevenue) || 0;
    const users = parseFloat(row.totalUsers) || 0;
    const itemsViewed = parseFloat(row.itemsViewed) || 0;
    const itemsPurchased = parseFloat(row.itemsPurchased) || 0;
    const itemsAddedToCart = parseFloat(row.itemsAddedToCart) || 0;

    return {
        ...row,
        averageOrderValue: purchases > 0 ? revenue / purchases : 0,
        purchaseConversionRate: users > 0 ? (purchases / users) * 100 : 0,
        conversionRate: activeTab === 'ecommerce'
            ? (itemsViewed > 0 ? (itemsPurchased / itemsViewed) * 100 : 0)
            : (users > 0 ? (purchases / users) * 100 : 0),
        addToCartRate: itemsViewed > 0 ? (itemsAddedToCart / itemsViewed) * 100 : 0,
        checkoutConversionRate: itemsAddedToCart > 0 ? (itemsPurchased / itemsAddedToCart) * 100 : 0
    };
};

const formatCellValue = (row, col) => {
    if (isDimensionColumn(col)) return row[col] || row.dimension || '-';
    if (col === 'date') return row[col];
    if (col === 'purchaseRevenue' || col === 'averageOrderValue' || col === 'itemRevenue') {
        return formatNumber(parseFloat(row[col]) || 0, 'currency');
    }
    if (col === 'purchaseConversionRate' || col === 'conversionRate' || col === 'addToCartRate' || col === 'checkoutConversionRate') {
        return `${(parseFloat(row[col]) || 0).toFixed(2)}%`;
    }
    if (col === 'engagementRate') return `${((parseFloat(row[col]) || 0) * 100).toFixed(1)}%`;
    if (col === 'bounceRate') return formatNumber(parseFloat(row[col]) || 0, 'percentage');
    if (col === 'averageSessionDuration') return formatNumber(parseFloat(row[col]) || 0, 'duration');
    return formatNumber(parseFloat(row[col]) || 0, 'number');
};

const GA4StatsShared = ({
    activeTab,
    analyticsData,
    columns,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getColumnLabel,
    isMobile,
    itemsPerPage,
    loadMoreGa4Data,
    setCurrentPage,
    setItemsPerPage,
    setSortConfig,
    sortConfig,
    t
}) => {
    const sortedRows = [...analyticsData.rows]
        .map(row => withCalculatedMetrics(row, activeTab))
        .sort((a, b) => {
            const aVal = a[sortConfig.key];
            const bVal = b[sortConfig.key];
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);

            if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
                return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
            }

            const aStr = String(aVal || '');
            const bStr = String(bVal || '');
            return sortConfig.direction === 'asc'
                ? aStr.localeCompare(bStr)
                : bStr.localeCompare(aStr);
        });

    return (
        <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--glass-border)',
            borderRadius: '12px',
            padding: '20px'
        }}>
            <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
                {t('詳細數據', 'Detailed Data')}
            </h3>
            <div style={{
                overflowX: 'auto',
                maxHeight: '400px',
                overflowY: 'auto'
            }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '14px'
                }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                            {columns.map(col => (
                                <th
                                    key={col}
                                    onClick={() => {
                                        setSortConfig(prev => ({
                                            key: col,
                                            direction: prev.key === col && prev.direction === 'asc' ? 'desc' : 'asc'
                                        }));
                                    }}
                                    style={{
                                        padding: '12px 8px',
                                        textAlign: 'left',
                                        color: 'var(--text-secondary)',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        userSelect: 'none',
                                        whiteSpace: 'nowrap'
                                    }}
                                >
                                    {getColumnLabel(col)}
                                    {sortConfig.key === col && (
                                        <span style={{ marginLeft: '4px' }}>
                                            {sortConfig.direction === 'asc' ? '▲' : '▼'}
                                        </span>
                                    )}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sortedRows
                            .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                            .map((row, index) => (
                                <tr key={index} style={{
                                    borderBottom: '1px solid var(--glass-border)',
                                    background: index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                }}>
                                    {columns.map(col => (
                                        <td key={col} style={{
                                            padding: '12px 8px',
                                            color: 'var(--text-primary)'
                                        }}>
                                            {formatCellValue(row, col)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                    </tbody>
                </table>
            </div>

            {ga4HasMore && (
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    justifyContent: 'space-between',
                    alignItems: isMobile ? 'stretch' : 'center',
                    gap: '12px',
                    padding: '16px 0',
                    borderTop: '1px solid var(--glass-border)',
                    marginTop: '8px'
                }}>
                    <div style={{
                        color: 'var(--text-secondary)',
                        fontSize: '13px',
                        textAlign: isMobile ? 'center' : 'left'
                    }}>
                        {t(`已載入 ${analyticsData.rows.length} / ${analyticsData.total_row_count || analyticsData.rows.length} 筆`,
                            `Loaded ${analyticsData.rows.length} / ${analyticsData.total_row_count || analyticsData.rows.length}`)}
                    </div>
                    <button
                        onClick={loadMoreGa4Data}
                        disabled={ga4LoadingMore}
                        style={{
                            padding: '8px 20px',
                            background: 'var(--accent-primary)',
                            border: 'none',
                            borderRadius: '8px',
                            color: 'white',
                            fontSize: '13px',
                            fontWeight: '500',
                            cursor: ga4LoadingMore ? 'wait' : 'pointer',
                            opacity: ga4LoadingMore ? 0.7 : 1,
                            transition: 'all 0.2s'
                        }}
                    >
                        {ga4LoadingMore ? t('載入中...', 'Loading...') : `⬇️ ${t('載入更多資料', 'Load More Data')}`}
                    </button>
                </div>
            )}

            {analyticsData.rows.length > 0 && (() => {
                const totalRows = analyticsData.rows.length;
                const totalPages = Math.ceil(totalRows / itemsPerPage);
                const startRow = (currentPage - 1) * itemsPerPage + 1;
                const endRow = Math.min(currentPage * itemsPerPage, totalRows);

                return (
                    <div style={{
                        display: 'flex',
                        flexDirection: isMobile ? 'column' : 'row',
                        justifyContent: 'space-between',
                        alignItems: isMobile ? 'stretch' : 'center',
                        gap: '12px',
                        padding: '16px 0',
                        borderTop: '1px solid var(--glass-border)',
                        marginTop: '8px'
                    }}>
                        <div style={{
                            color: 'var(--text-secondary)',
                            fontSize: '13px',
                            textAlign: isMobile ? 'center' : 'left'
                        }}>
                            {t(`顯示第 ${startRow}-${endRow} 筆，共 ${totalRows} 筆`,
                                `Showing ${startRow}-${endRow} of ${totalRows}`)}
                        </div>

                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            justifyContent: isMobile ? 'center' : 'flex-end',
                            flexWrap: 'wrap'
                        }}>
                            <select
                                value={itemsPerPage}
                                onChange={(e) => {
                                    setItemsPerPage(Number(e.target.value));
                                    setCurrentPage(1);
                                }}
                                style={{
                                    padding: '6px 10px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '6px',
                                    background: 'rgba(255,255,255,0.05)',
                                    color: 'var(--text-primary)',
                                    fontSize: '13px',
                                    cursor: 'pointer'
                                }}
                            >
                                <option value={20} style={{ color: 'black' }}>20 / {t('頁', 'page')}</option>
                                <option value={50} style={{ color: 'black' }}>50 / {t('頁', 'page')}</option>
                                <option value={100} style={{ color: 'black' }}>100 / {t('頁', 'page')}</option>
                            </select>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <button
                                    onClick={() => setCurrentPage(1)}
                                    disabled={currentPage === 1}
                                    style={{
                                        padding: '6px 10px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '6px',
                                        background: currentPage === 1 ? 'transparent' : 'rgba(255,255,255,0.05)',
                                        color: currentPage === 1 ? 'var(--text-secondary)' : 'var(--text-primary)',
                                        cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                        opacity: currentPage === 1 ? 0.5 : 1,
                                        fontSize: '13px'
                                    }}
                                >
                                    ⏮
                                </button>
                                <button
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={currentPage === 1}
                                    style={{
                                        padding: '6px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '6px',
                                        background: currentPage === 1 ? 'transparent' : 'rgba(255,255,255,0.05)',
                                        color: currentPage === 1 ? 'var(--text-secondary)' : 'var(--text-primary)',
                                        cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                        opacity: currentPage === 1 ? 0.5 : 1,
                                        fontSize: '13px'
                                    }}
                                >
                                    ◀
                                </button>
                                <span style={{
                                    padding: '6px 12px',
                                    color: 'var(--text-primary)',
                                    fontSize: '13px',
                                    fontWeight: 600
                                }}>
                                    {currentPage} / {totalPages}
                                </span>
                                <button
                                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                    disabled={currentPage === totalPages}
                                    style={{
                                        padding: '6px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '6px',
                                        background: currentPage === totalPages ? 'transparent' : 'rgba(255,255,255,0.05)',
                                        color: currentPage === totalPages ? 'var(--text-secondary)' : 'var(--text-primary)',
                                        cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                        opacity: currentPage === totalPages ? 0.5 : 1,
                                        fontSize: '13px'
                                    }}
                                >
                                    ▶
                                </button>
                                <button
                                    onClick={() => setCurrentPage(totalPages)}
                                    disabled={currentPage === totalPages}
                                    style={{
                                        padding: '6px 10px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '6px',
                                        background: currentPage === totalPages ? 'transparent' : 'rgba(255,255,255,0.05)',
                                        color: currentPage === totalPages ? 'var(--text-secondary)' : 'var(--text-primary)',
                                        cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                        opacity: currentPage === totalPages ? 0.5 : 1,
                                        fontSize: '13px'
                                    }}
                                >
                                    ⏭
                                </button>
                            </div>
                        </div>
                    </div>
                );
            })()}
        </div>
    );
};

export default GA4StatsShared;
