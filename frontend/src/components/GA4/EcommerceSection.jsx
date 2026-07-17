import React from 'react';
import { ECOMMERCE_DIMENSIONS, TRAFFIC_SECONDARY_DIMENSIONS } from './constants';
import GA4StatsShared from './GA4StatsShared';

export const EcommerceControls = ({
    analyticsData,
    ecommerceDimension,
    ecommerceFilter,
    ecommerceSecondaryDimension,
    ecommerceSecondaryFilter,
    isMobile,
    language,
    setEcommerceDimension,
    setEcommerceFilter,
    setEcommerceSecondaryDimension,
    setEcommerceSecondaryFilter,
    setEditingGroup,
    setShowGroupModal,
    sourceGroups,
    t
}) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        marginBottom: '20px',
        padding: '16px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)'
    }}>
        <div style={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            gap: '16px'
        }}>
            <div style={{ flex: 1 }}>
                <label style={{
                    display: 'block',
                    marginBottom: '8px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-secondary)'
                }}>
                    📦 {t('商品維度', 'Product Dimension')}
                </label>
                <select
                    value={ecommerceDimension}
                    onChange={(e) => setEcommerceDimension(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '10px 12px',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'var(--text-primary)',
                        fontSize: '14px'
                    }}
                >
                    {ECOMMERCE_DIMENSIONS.map(dim => (
                        <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                            {language === 'zh' ? dim.label_zh : dim.label_en}
                        </option>
                    ))}
                </select>
            </div>

            <div style={{ flex: 1 }}>
                <label style={{
                    display: 'block',
                    marginBottom: '8px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-secondary)'
                }}>
                    🌐 {t('流量維度（選填）', 'Traffic Dimension (Optional)')}
                </label>
                <select
                    value={ecommerceSecondaryDimension}
                    onChange={(e) => setEcommerceSecondaryDimension(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '10px 12px',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'var(--text-primary)',
                        fontSize: '14px'
                    }}
                >
                    {TRAFFIC_SECONDARY_DIMENSIONS.map(dim => (
                        <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                            {language === 'zh' ? dim.label_zh : dim.label_en}
                        </option>
                    ))}
                </select>
            </div>
        </div>

        <div style={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            gap: '16px'
        }}>
            <div style={{ flex: 1 }}>
                <label style={{
                    display: 'block',
                    marginBottom: '8px',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-secondary)'
                }}>
                    🎯 {t('商品篩選', 'Product Filter')}
                </label>
                <select
                    value={ecommerceFilter}
                    onChange={(e) => setEcommerceFilter(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '10px 12px',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'var(--text-primary)',
                        fontSize: '14px'
                    }}
                >
                    <option value="all" style={{ color: 'black' }}>
                        {t('全部商品', 'All Products')}
                    </option>
                    {analyticsData && analyticsData.rows &&
                        [...new Set(analyticsData.rows.map(row =>
                            row[ecommerceDimension]
                        ).filter(Boolean))].sort().map(value => (
                            <option key={value} value={value} style={{ color: 'black' }}>
                                {value.length > 40 ? `${value.substring(0, 40)}...` : value}
                            </option>
                        ))
                    }
                </select>
            </div>

            {ecommerceSecondaryDimension !== 'none' && (
                <div style={{ flex: 1 }}>
                    <label style={{
                        display: 'flex',
                        marginBottom: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <span>🌐 {t('來源篩選', 'Traffic Filter')}</span>
                        <button
                            onClick={() => {
                                setEditingGroup(null);
                                setShowGroupModal(true);
                            }}
                            style={{
                                background: 'rgba(99, 102, 241, 0.2)',
                                border: '1px solid rgba(99, 102, 241, 0.4)',
                                borderRadius: '4px',
                                color: '#818cf8',
                                fontSize: '11px',
                                padding: '2px 8px',
                                cursor: 'pointer'
                            }}
                        >
                            + {t('新增分組', 'Add Group')}
                        </button>
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <select
                            value={ecommerceSecondaryFilter}
                            onChange={(e) => setEcommerceSecondaryFilter(e.target.value)}
                            style={{
                                flex: 1,
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            <option value="all" style={{ color: 'black' }}>
                                {t('全部來源', 'All Sources')}
                            </option>
                            {analyticsData && analyticsData.rows && sourceGroups.filter(group => {
                                const sources = analyticsData.rows.map(row =>
                                    (row[ecommerceSecondaryDimension] || '').toLowerCase()
                                );
                                return group.patterns.some(pattern =>
                                    sources.some(source => source.includes(pattern.toLowerCase()))
                                );
                            }).map(group => (
                                <option key={group.key} value={group.key} style={{ color: 'black', fontWeight: 'bold' }}>
                                    {language === 'zh' ? group.label_zh : group.label_en}
                                </option>
                            ))}
                            <option disabled style={{ color: '#666' }}>──────────────</option>
                            {analyticsData && analyticsData.rows &&
                                [...new Set(analyticsData.rows.map(row =>
                                    row[ecommerceSecondaryDimension]
                                ).filter(Boolean))].sort().map(value => (
                                    <option key={value} value={value} style={{ color: 'black' }}>
                                        {value}
                                    </option>
                                ))
                            }
                        </select>

                        {(ecommerceSecondaryFilter.startsWith('group_') || ecommerceSecondaryFilter.startsWith('custom_')) && ecommerceSecondaryFilter !== 'all' && (
                            <button
                                onClick={() => {
                                    const group = sourceGroups.find(g => g.key === ecommerceSecondaryFilter);
                                    if (group) {
                                        setEditingGroup(group);
                                        setShowGroupModal(true);
                                    }
                                }}
                                style={{
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    color: 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '14px'
                                }}
                                title={t('編輯分組', 'Edit Group')}
                            >
                                ✏️
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    </div>
);

const EcommerceSection = ({
    analyticsData,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getEcommerceColumnLabel,
    getEcommerceColumnOrder,
    isMobile,
    itemsPerPage,
    loadMoreGa4Data,
    setCurrentPage,
    setItemsPerPage,
    setSortConfig,
    sortConfig,
    t
}) => (
    <GA4StatsShared
        activeTab="ecommerce"
        analyticsData={analyticsData}
        columns={getEcommerceColumnOrder()}
        currentPage={currentPage}
        ga4HasMore={ga4HasMore}
        ga4LoadingMore={ga4LoadingMore}
        getColumnLabel={getEcommerceColumnLabel}
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

export default EcommerceSection;
