import React from 'react';
import { CONTENT_DIMENSIONS } from './constants';
import GA4StatsShared from './GA4StatsShared';

export const ContentControls = ({
    contentDimension,
    contentGroups,
    contentTypeFilter,
    isMobile,
    language,
    setContentDimension,
    setContentTypeFilter,
    setEditingContentGroup,
    setShowContentGroupModal,
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
                    📄 {t('內容維度', 'Content Dimension')}
                </label>
                <select
                    value={contentDimension}
                    onChange={(e) => setContentDimension(e.target.value)}
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
                    {CONTENT_DIMENSIONS.map(dim => (
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
                    🏷️ {t('內容類型', 'Content Type')}
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <select
                        value={contentTypeFilter}
                        onChange={(e) => {
                            if (e.target.value === 'add_new') {
                                setEditingContentGroup(null);
                                setShowContentGroupModal(true);
                            } else {
                                setContentTypeFilter(e.target.value);
                            }
                        }}
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
                            {t('全部頁面', 'All Pages')}
                        </option>

                        {contentGroups.filter(g => g.isDefault).length > 0 && (
                            <option disabled style={{ color: '#666' }}>── {t('預設分組', 'Default Groups')} ──</option>
                        )}
                        {contentGroups.filter(g => g.isDefault).map(group => (
                            <option key={group.key} value={group.key} style={{ color: 'black' }}>
                                {language === 'zh' ? group.label_zh : group.label_en}
                            </option>
                        ))}

                        {contentGroups.filter(g => !g.isDefault).length > 0 && (
                            <option disabled style={{ color: '#666' }}>── {t('自訂分組', 'Custom Groups')} ──</option>
                        )}
                        {contentGroups.filter(g => !g.isDefault).map(group => (
                            <option key={group.key} value={group.key} style={{ color: 'black' }}>
                                {language === 'zh' ? group.label_zh : group.label_en}
                            </option>
                        ))}

                        <option disabled style={{ color: '#666' }}>──────────────</option>
                        <option value="add_new" style={{ color: 'black' }}>
                            ➕ {t('新增分組...', 'Add Group...')}
                        </option>
                    </select>

                    {contentTypeFilter !== 'all' && contentTypeFilter !== 'add_new' && (
                        <button
                            onClick={() => {
                                const group = contentGroups.find(g => g.key === contentTypeFilter);
                                if (group) {
                                    setEditingContentGroup(group);
                                    setShowContentGroupModal(true);
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
        </div>
    </div>
);

const ContentSection = ({
    analyticsData,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getContentColumnLabel,
    getContentColumnOrder,
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
        activeTab="content"
        analyticsData={analyticsData}
        columns={getContentColumnOrder()}
        currentPage={currentPage}
        ga4HasMore={ga4HasMore}
        ga4LoadingMore={ga4LoadingMore}
        getColumnLabel={getContentColumnLabel}
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

export default ContentSection;
