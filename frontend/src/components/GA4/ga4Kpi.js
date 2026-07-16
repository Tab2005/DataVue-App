import { filterByContentGroup } from '../../utils/contentGroups';
import {
    TRAFFIC_METRICS,
    TRAFFIC_COLUMN_HEADERS,
    BEHAVIOR_METRICS,
    BEHAVIOR_COLUMN_HEADERS,
    ECOMMERCE_METRICS,
    ECOMMERCE_COLUMN_HEADERS,
    CONTENT_METRICS,
    CONTENT_COLUMN_HEADERS
} from './constants';
import {
    calculateChange,
    formatNumber,
    getMetricIcon,
    getMetricLabel as getMetricLabelForLanguage
} from './ga4Formatters';

// Get KPI data from analytics
// 使用 summaryData（不帶 dimension 的去重數據）來顯示 KPI 卡片
export const getOverviewKPIData = ({ analyticsData, summaryData, compareData, compareSummaryData, compareMode, language }) => {
const getMetricLabel = (metric) => getMetricLabelForLanguage(metric, language);
    if (!analyticsData || !analyticsData.rows) return [];

    // 優先使用 summaryData（去重總數），如果沒有則 fallback 到加總
    const currentTotals = {};

    if (summaryData && summaryData.rows && summaryData.rows.length > 0) {
        // 使用去重的總數（正確的方式）
        const summaryRow = summaryData.rows[0];
        analyticsData.metrics.forEach(metric => {
            currentTotals[metric] = parseFloat(summaryRow[metric]) || 0;
        });
        console.log('📊 Using summary data for KPIs (deduplicated)');
    } else {
        // Fallback: 加總每日數據（對於 sessions, pageviews 等可加總指標是正確的）
        analyticsData.rows.forEach(row => {
            analyticsData.metrics.forEach(metric => {
                if (!currentTotals[metric]) currentTotals[metric] = 0;
                currentTotals[metric] += parseFloat(row[metric]) || 0;
            });
        });
        console.log('⚠️ Fallback: summing daily data for KPIs');
    }

    // Determine comparison data source based on compare mode
    let previousTotals = {};

    if (compareMode !== 'none') {
        if (compareSummaryData && compareSummaryData.rows && compareSummaryData.rows.length > 0) {
            // 使用去重的比較總數
            const compareSummaryRow = compareSummaryData.rows[0];
            analyticsData.metrics.forEach(metric => {
                previousTotals[metric] = parseFloat(compareSummaryRow[metric]) || 0;
            });
        } else if (compareData && compareData.rows) {
            // Fallback: 加總比較期間數據
            compareData.rows.forEach(row => {
                analyticsData.metrics.forEach(metric => {
                    if (!previousTotals[metric]) previousTotals[metric] = 0;
                    previousTotals[metric] += parseFloat(row[metric]) || 0;
                });
            });
        }
    }
    // When compare mode is 'none', do not calculate any comparison

    const kpis = [];
    analyticsData.metrics.forEach(metric => {
        const current = currentTotals[metric] || 0;
        const previous = previousTotals[metric] || 0;
        const change = calculateChange(current, previous);

        let type = 'number';
        if (metric === 'bounceRate') type = 'percentage';
        if (metric === 'averageSessionDuration') type = 'duration';
        if (metric === 'purchaseRevenue') type = 'currency';

        kpis.push({
            label: getMetricLabel(metric),
            value: formatNumber(current, type),
            change: compareMode !== 'none' ? change : null,
            icon: getMetricIcon(metric),
            previousValue: compareMode !== 'none' ? formatNumber(previous, type) : null
        });
    });

    // Add derived metric: 客單價 (AOV = purchaseRevenue / ecommercePurchases)
    const currentRevenue = currentTotals['purchaseRevenue'] || 0;
    const currentPurchases = currentTotals['ecommercePurchases'] || 0;
    const currentAOV = currentPurchases > 0 ? currentRevenue / currentPurchases : 0;

    const previousRevenue = previousTotals['purchaseRevenue'] || 0;
    const previousPurchases = previousTotals['ecommercePurchases'] || 0;
    const previousAOV = previousPurchases > 0 ? previousRevenue / previousPurchases : 0;

    const aovChange = calculateChange(currentAOV, previousAOV);

    kpis.push({
        label: getMetricLabel('averageOrderValue'),
        value: formatNumber(currentAOV, 'currency'),
        change: compareMode !== 'none' ? aovChange : null,
        icon: getMetricIcon('averageOrderValue'),
        previousValue: compareMode !== 'none' ? formatNumber(previousAOV, 'currency') : null
    });

    // Add derived metric: 購買轉換率 (Purchase Conversion Rate = ecommercePurchases / totalUsers)
    const currentUsers = currentTotals['totalUsers'] || 0;
    const currentConversionRate = currentUsers > 0 ? (currentPurchases / currentUsers) * 100 : 0;

    const previousUsers = previousTotals['totalUsers'] || 0;
    const previousConversionRate = previousUsers > 0 ? (previousPurchases / previousUsers) * 100 : 0;

    const conversionRateChange = calculateChange(currentConversionRate, previousConversionRate);

    kpis.push({
        label: getMetricLabel('purchaseConversionRate'),
        value: `${currentConversionRate.toFixed(2)}%`,
        change: compareMode !== 'none' ? conversionRateChange : null,
        icon: getMetricIcon('purchaseConversionRate'),
        previousValue: compareMode !== 'none' ? `${previousConversionRate.toFixed(2)}%` : null
    });

    return kpis;
};

// Get Traffic Tab KPI data with source filter
export const getTrafficKPIData = ({ analyticsData, compareData, compareMode, sourceFilter, sourceGroups, trafficDimension, language }) => {
const getMetricLabel = (metric) => getMetricLabelForLanguage(metric, language);
    if (!analyticsData || !analyticsData.rows) return [];

    // Filter rows by source if a specific source is selected
    let filteredRows = analyticsData.rows;
    if (sourceFilter !== 'all') {
        if (sourceFilter.startsWith('group_') || sourceFilter.startsWith('custom_')) {
            // Group filter - match against patterns
            const group = sourceGroups.find(g => g.key === sourceFilter);
            if (group) {
                filteredRows = analyticsData.rows.filter(row => {
                    const dimValue = (row[trafficDimension] || row.dimension || '').toLowerCase();
                    return group.patterns.some(pattern => dimValue.includes(pattern.toLowerCase()));
                });
            }
        } else {
            // Individual source filter - exact match
            filteredRows = analyticsData.rows.filter(row => {
                const dimValue = row[trafficDimension] || row.dimension || '';
                return dimValue === sourceFilter;
            });
        }
    }


    // Calculate totals from filtered rows
    const totals = {};
    TRAFFIC_METRICS.forEach(metric => {
        totals[metric] = 0;
    });

    filteredRows.forEach(row => {
        TRAFFIC_METRICS.forEach(metric => {
            totals[metric] += parseFloat(row[metric]) || 0;
        });
    });

    // Average for rate metrics
    const rowCount = filteredRows.length || 1;
    totals['engagementRate'] = totals['engagementRate'] / rowCount;
    totals['averageSessionDuration'] = totals['averageSessionDuration'] / rowCount;

    // Calculate conversion rate
    const conversionRate = totals['totalUsers'] > 0
        ? (totals['ecommercePurchases'] / totals['totalUsers']) * 100 : 0;

    // Calculate compare period totals if compare mode is active
    let prevTotals = {};
    let prevConversionRate = 0;

    if (compareMode !== 'none' && compareData && compareData.rows) {
        // Apply same source filter to compare data
        let filteredCompareRows = compareData.rows;
        if (sourceFilter !== 'all') {
            if (sourceFilter.startsWith('group_') || sourceFilter.startsWith('custom_')) {
                const group = sourceGroups.find(g => g.key === sourceFilter);
                if (group) {
                    filteredCompareRows = compareData.rows.filter(row => {
                        const dimValue = (row[trafficDimension] || row.dimension || '').toLowerCase();
                        return group.patterns.some(pattern => dimValue.includes(pattern.toLowerCase()));
                    });
                }
            } else {
                filteredCompareRows = compareData.rows.filter(row => {
                    const dimValue = row[trafficDimension] || row.dimension || '';
                    return dimValue === sourceFilter;
                });
            }
        }

        TRAFFIC_METRICS.forEach(metric => {
            prevTotals[metric] = 0;
        });
        filteredCompareRows.forEach(row => {
            TRAFFIC_METRICS.forEach(metric => {
                prevTotals[metric] += parseFloat(row[metric]) || 0;
            });
        });

        const prevRowCount = filteredCompareRows.length || 1;
        prevTotals['engagementRate'] = prevTotals['engagementRate'] / prevRowCount;
        prevTotals['averageSessionDuration'] = prevTotals['averageSessionDuration'] / prevRowCount;
        prevConversionRate = prevTotals['totalUsers'] > 0
            ? (prevTotals['ecommercePurchases'] / prevTotals['totalUsers']) * 100 : 0;
    }

    // Helper to build KPI with compare data
    const buildKPI = (label, currentVal, prevVal, type, icon) => {
        const change = compareMode !== 'none' ? calculateChange(currentVal, prevVal) : null;
        let formattedValue, formattedPrev;

        if (type === 'percentage') {
            formattedValue = `${(currentVal * 100).toFixed(1)}%`;
            formattedPrev = `${(prevVal * 100).toFixed(1)}%`;
        } else if (type === 'percentRaw') {
            formattedValue = `${currentVal.toFixed(2)}%`;
            formattedPrev = `${prevVal.toFixed(2)}%`;
        } else if (type === 'currency') {
            formattedValue = formatNumber(currentVal, 'currency');
            formattedPrev = formatNumber(prevVal, 'currency');
        } else if (type === 'duration') {
            formattedValue = formatNumber(currentVal, 'duration');
            formattedPrev = formatNumber(prevVal, 'duration');
        } else {
            formattedValue = formatNumber(currentVal, 'number');
            formattedPrev = formatNumber(prevVal, 'number');
        }

        return {
            label,
            value: formattedValue,
            icon,
            change,
            previousValue: compareMode !== 'none' ? formattedPrev : null
        };
    };

    // Build KPI array with all 9 metrics including compare data
    const kpis = [
        buildKPI(getMetricLabel('totalUsers') || '總人數', totals['totalUsers'], prevTotals['totalUsers'] || 0, 'number', '👥'),
        buildKPI(getMetricLabel('sessions') || '工作階段', totals['sessions'], prevTotals['sessions'] || 0, 'number', '📊'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.engagedSessions[language === 'zh' ? 'zh' : 'en'], totals['engagedSessions'], prevTotals['engagedSessions'] || 0, 'number', '✨'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.engagementRate[language === 'zh' ? 'zh' : 'en'], totals['engagementRate'], prevTotals['engagementRate'] || 0, 'percentage', '📈'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.averageSessionDuration[language === 'zh' ? 'zh' : 'en'], totals['averageSessionDuration'], prevTotals['averageSessionDuration'] || 0, 'duration', '⏱️'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.addToCarts[language === 'zh' ? 'zh' : 'en'], totals['addToCarts'], prevTotals['addToCarts'] || 0, 'number', '🛒'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.ecommercePurchases[language === 'zh' ? 'zh' : 'en'], totals['ecommercePurchases'], prevTotals['ecommercePurchases'] || 0, 'number', '💰'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.purchaseRevenue[language === 'zh' ? 'zh' : 'en'], totals['purchaseRevenue'], prevTotals['purchaseRevenue'] || 0, 'currency', '💵'),
        buildKPI(TRAFFIC_COLUMN_HEADERS.conversionRate[language === 'zh' ? 'zh' : 'en'], conversionRate, prevConversionRate, 'percentRaw', '🎯')
    ];

    return kpis;
};

// Get Behavior Tab KPI data with dimension filter
export const getBehaviorKPIData = ({ analyticsData, compareData, compareMode, behaviorFilter, behaviorDimension, language }) => {
    if (!analyticsData || !analyticsData.rows) return [];

    // Filter rows by selected filter value
    let filteredRows = analyticsData.rows;
    if (behaviorFilter !== 'all') {
        filteredRows = analyticsData.rows.filter(row => {
            const dimValue = row[behaviorDimension] || row.dimension || '';
            return dimValue === behaviorFilter;
        });
    }

    // Calculate totals from filtered rows
    const totals = {};
    BEHAVIOR_METRICS.forEach(metric => {
        totals[metric] = 0;
    });

    filteredRows.forEach(row => {
        BEHAVIOR_METRICS.forEach(metric => {
            totals[metric] += parseFloat(row[metric]) || 0;
        });
    });

    // Average for rate metrics
    const rowCount = filteredRows.length || 1;
    totals['engagementRate'] = totals['engagementRate'] / rowCount;
    totals['averageSessionDuration'] = totals['averageSessionDuration'] / rowCount;

    // Calculate conversion rate
    const conversionRate = totals['totalUsers'] > 0
        ? (totals['ecommercePurchases'] / totals['totalUsers']) * 100 : 0;

    // Calculate compare period totals if compare mode is active
    let prevTotals = {};
    let prevConversionRate = 0;

    if (compareMode !== 'none' && compareData && compareData.rows) {
        // Apply same filter to compare data
        let filteredCompareRows = compareData.rows;
        if (behaviorFilter !== 'all') {
            filteredCompareRows = compareData.rows.filter(row => {
                const dimValue = row[behaviorDimension] || row.dimension || '';
                return dimValue === behaviorFilter;
            });
        }

        BEHAVIOR_METRICS.forEach(metric => {
            prevTotals[metric] = 0;
        });
        filteredCompareRows.forEach(row => {
            BEHAVIOR_METRICS.forEach(metric => {
                prevTotals[metric] += parseFloat(row[metric]) || 0;
            });
        });

        const prevRowCount = filteredCompareRows.length || 1;
        prevTotals['engagementRate'] = prevTotals['engagementRate'] / prevRowCount;
        prevTotals['averageSessionDuration'] = prevTotals['averageSessionDuration'] / prevRowCount;
        prevConversionRate = prevTotals['totalUsers'] > 0
            ? (prevTotals['ecommercePurchases'] / prevTotals['totalUsers']) * 100 : 0;
    }

    // Helper to build KPI with compare data
    const buildKPI = (label, currentVal, prevVal, type, icon) => {
        const change = compareMode !== 'none' ? calculateChange(currentVal, prevVal) : null;
        let formattedValue, formattedPrev;

        if (type === 'percentage') {
            formattedValue = `${(currentVal * 100).toFixed(1)}%`;
            formattedPrev = `${(prevVal * 100).toFixed(1)}%`;
        } else if (type === 'percentRaw') {
            formattedValue = `${currentVal.toFixed(2)}%`;
            formattedPrev = `${prevVal.toFixed(2)}%`;
        } else if (type === 'currency') {
            formattedValue = formatNumber(currentVal, 'currency');
            formattedPrev = formatNumber(prevVal, 'currency');
        } else if (type === 'duration') {
            formattedValue = formatNumber(currentVal, 'duration');
            formattedPrev = formatNumber(prevVal, 'duration');
        } else {
            formattedValue = formatNumber(currentVal, 'number');
            formattedPrev = formatNumber(prevVal, 'number');
        }

        return {
            label,
            value: formattedValue,
            icon,
            change,
            previousValue: compareMode !== 'none' ? formattedPrev : null
        };
    };

    // Build KPI array with all 9 metrics including compare data
    const kpis = [
        buildKPI(BEHAVIOR_COLUMN_HEADERS.totalUsers[language === 'zh' ? 'zh' : 'en'], totals['totalUsers'], prevTotals['totalUsers'] || 0, 'number', '👥'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.engagedSessions[language === 'zh' ? 'zh' : 'en'], totals['engagedSessions'], prevTotals['engagedSessions'] || 0, 'number', '✨'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.screenPageViews[language === 'zh' ? 'zh' : 'en'], totals['screenPageViews'], prevTotals['screenPageViews'] || 0, 'number', '👁️'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.engagementRate[language === 'zh' ? 'zh' : 'en'], totals['engagementRate'], prevTotals['engagementRate'] || 0, 'percentage', '📈'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.averageSessionDuration[language === 'zh' ? 'zh' : 'en'], totals['averageSessionDuration'], prevTotals['averageSessionDuration'] || 0, 'duration', '⏱️'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.addToCarts[language === 'zh' ? 'zh' : 'en'], totals['addToCarts'], prevTotals['addToCarts'] || 0, 'number', '🛒'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.ecommercePurchases[language === 'zh' ? 'zh' : 'en'], totals['ecommercePurchases'], prevTotals['ecommercePurchases'] || 0, 'number', '💰'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.purchaseRevenue[language === 'zh' ? 'zh' : 'en'], totals['purchaseRevenue'], prevTotals['purchaseRevenue'] || 0, 'currency', '💵'),
        buildKPI(BEHAVIOR_COLUMN_HEADERS.conversionRate[language === 'zh' ? 'zh' : 'en'], conversionRate, prevConversionRate, 'percentRaw', '🎯')
    ];

    return kpis;
};

// Get Ecommerce Tab KPI data with product and traffic filters
export const getEcommerceKPIData = ({ analyticsData, compareData, compareMode, ecommerceFilter, ecommerceDimension, ecommerceSecondaryFilter, ecommerceSecondaryDimension, sourceGroups, language }) => {
    if (!analyticsData || !analyticsData.rows) return [];

    // Filter rows by selected product filter and secondary filter
    let filteredRows = analyticsData.rows;

    // Apply product dimension filter
    if (ecommerceFilter !== 'all') {
        filteredRows = filteredRows.filter(row => {
            const dimValue = row[ecommerceDimension] || '';
            return dimValue === ecommerceFilter;
        });
    }

    // Apply secondary traffic dimension filter (if selected)
    if (ecommerceSecondaryDimension !== 'none' && ecommerceSecondaryFilter !== 'all') {
        // Check if it's a source group filter
        if (ecommerceSecondaryFilter.startsWith('group_') || ecommerceSecondaryFilter.startsWith('custom_')) {
            const group = sourceGroups.find(g => g.key === ecommerceSecondaryFilter);
            if (group && group.patterns) {
                filteredRows = filteredRows.filter(row => {
                    const dimValue = (row[ecommerceSecondaryDimension] || '').toLowerCase();
                    return group.patterns.some(pattern => dimValue.includes(pattern.toLowerCase()));
                });
            }
        } else {
            // Direct value filter
            filteredRows = filteredRows.filter(row => {
                const dimValue = row[ecommerceSecondaryDimension] || '';
                return dimValue === ecommerceSecondaryFilter;
            });
        }
    }

    // Calculate totals from filtered rows
    const totals = {};
    ECOMMERCE_METRICS.forEach(metric => {
        totals[metric] = 0;
    });

    filteredRows.forEach(row => {
        ECOMMERCE_METRICS.forEach(metric => {
            totals[metric] += parseFloat(row[metric]) || 0;
        });
    });

    // Calculate all 3 computed rates
    const addToCartRate = totals['itemsViewed'] > 0
        ? (totals['itemsAddedToCart'] / totals['itemsViewed']) * 100 : 0;
    const checkoutConversionRate = totals['itemsAddedToCart'] > 0
        ? (totals['itemsPurchased'] / totals['itemsAddedToCart']) * 100 : 0;
    const conversionRate = totals['itemsViewed'] > 0
        ? (totals['itemsPurchased'] / totals['itemsViewed']) * 100 : 0;

    // Calculate compare period totals if compare mode is active
    let prevTotals = {};
    let prevAddToCartRate = 0;
    let prevCheckoutConversionRate = 0;
    let prevConversionRate = 0;

    if (compareMode !== 'none' && compareData && compareData.rows) {
        // Apply same filters to compare data
        let filteredCompareRows = compareData.rows;

        if (ecommerceFilter !== 'all') {
            filteredCompareRows = filteredCompareRows.filter(row => {
                const dimValue = row[ecommerceDimension] || '';
                return dimValue === ecommerceFilter;
            });
        }

        if (ecommerceSecondaryDimension !== 'none' && ecommerceSecondaryFilter !== 'all') {
            // Check if it's a source group filter
            if (ecommerceSecondaryFilter.startsWith('group_') || ecommerceSecondaryFilter.startsWith('custom_')) {
                const group = sourceGroups.find(g => g.key === ecommerceSecondaryFilter);
                if (group && group.patterns) {
                    filteredCompareRows = filteredCompareRows.filter(row => {
                        const dimValue = (row[ecommerceSecondaryDimension] || '').toLowerCase();
                        return group.patterns.some(pattern => dimValue.includes(pattern.toLowerCase()));
                    });
                }
            } else {
                // Direct value filter
                filteredCompareRows = filteredCompareRows.filter(row => {
                    const dimValue = row[ecommerceSecondaryDimension] || '';
                    return dimValue === ecommerceSecondaryFilter;
                });
            }
        }

        ECOMMERCE_METRICS.forEach(metric => {
            prevTotals[metric] = 0;
        });
        filteredCompareRows.forEach(row => {
            ECOMMERCE_METRICS.forEach(metric => {
                prevTotals[metric] += parseFloat(row[metric]) || 0;
            });
        });

        prevAddToCartRate = prevTotals['itemsViewed'] > 0
            ? (prevTotals['itemsAddedToCart'] / prevTotals['itemsViewed']) * 100 : 0;
        prevCheckoutConversionRate = prevTotals['itemsAddedToCart'] > 0
            ? (prevTotals['itemsPurchased'] / prevTotals['itemsAddedToCart']) * 100 : 0;
        prevConversionRate = prevTotals['itemsViewed'] > 0
            ? (prevTotals['itemsPurchased'] / prevTotals['itemsViewed']) * 100 : 0;
    }

    // Helper to build KPI with compare data
    const buildKPI = (label, currentVal, prevVal, type, icon) => {
        const change = compareMode !== 'none' ? calculateChange(currentVal, prevVal) : null;
        let formattedValue, formattedPrev;

        if (type === 'percentRaw') {
            formattedValue = `${currentVal.toFixed(2)}%`;
            formattedPrev = `${prevVal.toFixed(2)}%`;
        } else if (type === 'currency') {
            formattedValue = formatNumber(currentVal, 'currency');
            formattedPrev = formatNumber(prevVal, 'currency');
        } else {
            formattedValue = formatNumber(currentVal, 'number');
            formattedPrev = formatNumber(prevVal, 'number');
        }

        return {
            label,
            value: formattedValue,
            icon,
            change,
            previousValue: compareMode !== 'none' ? formattedPrev : null
        };
    };

    // Build KPI array with all 9 metrics including compare data
    const kpis = [
        buildKPI(ECOMMERCE_COLUMN_HEADERS.totalUsers[language === 'zh' ? 'zh' : 'en'], totals['totalUsers'], prevTotals['totalUsers'] || 0, 'number', '👥'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.itemsViewed[language === 'zh' ? 'zh' : 'en'], totals['itemsViewed'], prevTotals['itemsViewed'] || 0, 'number', '👁️'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.itemsAddedToCart[language === 'zh' ? 'zh' : 'en'], totals['itemsAddedToCart'], prevTotals['itemsAddedToCart'] || 0, 'number', '🛒'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.addToCartRate[language === 'zh' ? 'zh' : 'en'], addToCartRate, prevAddToCartRate, 'percentRaw', '📊'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.itemsPurchased[language === 'zh' ? 'zh' : 'en'], totals['itemsPurchased'], prevTotals['itemsPurchased'] || 0, 'number', '🛍️'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.totalPurchasers[language === 'zh' ? 'zh' : 'en'], totals['totalPurchasers'], prevTotals['totalPurchasers'] || 0, 'number', '👤'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.itemRevenue[language === 'zh' ? 'zh' : 'en'], totals['itemRevenue'], prevTotals['itemRevenue'] || 0, 'currency', '💵'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.checkoutConversionRate[language === 'zh' ? 'zh' : 'en'], checkoutConversionRate, prevCheckoutConversionRate, 'percentRaw', '✅'),
        buildKPI(ECOMMERCE_COLUMN_HEADERS.conversionRate[language === 'zh' ? 'zh' : 'en'], conversionRate, prevConversionRate, 'percentRaw', '🎯')
    ];

    return kpis;
};

// Get Content Analysis Tab KPI data with content type filter
export const getContentKPIData = ({ analyticsData, compareData, compareMode, contentTypeFilter, contentGroups, contentDimension, language }) => {
    if (!analyticsData || !analyticsData.rows) return [];

    // Filter rows by content group if a specific group is selected
    let filteredRows = analyticsData.rows;
    if (contentTypeFilter !== 'all') {
        const group = contentGroups.find(g => g.key === contentTypeFilter);
        if (group) {
            filteredRows = filterByContentGroup(filteredRows, group, contentDimension);
        }
    }

    // Calculate totals from filtered rows
    const totals = {};
    CONTENT_METRICS.forEach(metric => {
        totals[metric] = 0;
    });

    filteredRows.forEach(row => {
        CONTENT_METRICS.forEach(metric => {
            totals[metric] += parseFloat(row[metric]) || 0;
        });
    });

    // Average for rate metrics
    const rowCount = filteredRows.length || 1;
    totals['averageSessionDuration'] = totals['averageSessionDuration'] / rowCount;
    totals['bounceRate'] = totals['bounceRate'] / rowCount;

    // Calculate compare period totals if compare mode is active
    let prevTotals = {};

    if (compareMode !== 'none' && compareData && compareData.rows) {
        // Apply same filters to compare data
        let filteredCompareRows = compareData.rows;
        if (contentTypeFilter !== 'all') {
            const group = contentGroups.find(g => g.key === contentTypeFilter);
            if (group) {
                filteredCompareRows = filterByContentGroup(filteredCompareRows, group, contentDimension);
            }
        }

        CONTENT_METRICS.forEach(metric => {
            prevTotals[metric] = 0;
        });
        filteredCompareRows.forEach(row => {
            CONTENT_METRICS.forEach(metric => {
                prevTotals[metric] += parseFloat(row[metric]) || 0;
            });
        });

        const prevRowCount = filteredCompareRows.length || 1;
        prevTotals['averageSessionDuration'] = prevTotals['averageSessionDuration'] / prevRowCount;
        prevTotals['bounceRate'] = prevTotals['bounceRate'] / prevRowCount;
    }

    // Helper to build KPI with compare data
    const buildKPI = (label, currentVal, prevVal, type, icon) => {
        const change = compareMode !== 'none' ? calculateChange(currentVal, prevVal) : null;
        let formattedValue, formattedPrev;

        if (type === 'percentage') {
            formattedValue = `${(currentVal * 100).toFixed(1)}%`;
            formattedPrev = `${(prevVal * 100).toFixed(1)}%`;
        } else if (type === 'duration') {
            formattedValue = formatNumber(currentVal, 'duration');
            formattedPrev = formatNumber(prevVal, 'duration');
        } else {
            formattedValue = formatNumber(currentVal, 'number');
            formattedPrev = formatNumber(prevVal, 'number');
        }

        return {
            label,
            value: formattedValue,
            icon,
            change,
            previousValue: compareMode !== 'none' ? formattedPrev : null
        };
    };

    // Build KPI array with all 6 metrics including compare data
    const kpis = [
        buildKPI(CONTENT_COLUMN_HEADERS.totalUsers[language === 'zh' ? 'zh' : 'en'], totals['totalUsers'], prevTotals['totalUsers'] || 0, 'number', '👥'),
        buildKPI(CONTENT_COLUMN_HEADERS.activeUsers[language === 'zh' ? 'zh' : 'en'], totals['activeUsers'], prevTotals['activeUsers'] || 0, 'number', '👤'),
        buildKPI(CONTENT_COLUMN_HEADERS.screenPageViews[language === 'zh' ? 'zh' : 'en'], totals['screenPageViews'], prevTotals['screenPageViews'] || 0, 'number', '👁️'),
        buildKPI(CONTENT_COLUMN_HEADERS.sessions[language === 'zh' ? 'zh' : 'en'], totals['sessions'], prevTotals['sessions'] || 0, 'number', '🔄'),
        buildKPI(CONTENT_COLUMN_HEADERS.averageSessionDuration[language === 'zh' ? 'zh' : 'en'], totals['averageSessionDuration'], prevTotals['averageSessionDuration'] || 0, 'duration', '⏱️'),
        buildKPI(CONTENT_COLUMN_HEADERS.bounceRate[language === 'zh' ? 'zh' : 'en'], totals['bounceRate'], prevTotals['bounceRate'] || 0, 'percentage', '📈')
    ];

    return kpis;
};
