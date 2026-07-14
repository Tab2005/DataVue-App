import React from 'react';

import {
    AIInsightNote,
    ITEM_CATEGORY_SOURCE_LABELS,
    LANDING_MATCH_TYPE_OPTIONS,
    baseCardStyle,
    buttonStyle,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';

const ItemsTab = ({
    language,
    t,
    isMobile,
    propertyId,
    itemsDays,
    setItemsDays,
    loadItems,
    itemsError,
    itemsLoading,
    itemsSnapshot,
    itemsCategoryFilter,
    setItemsCategoryFilter,
    itemsSearchQuery,
    setItemsSearchQuery,
    DaySelector,
    renderItemsSortHeader,
    sortedItemsRows,
    itemCategoryRulesOpen,
    setItemCategoryRulesOpen,
    itemCategoryRulesError,
    itemCategoryRulesLoading,
    itemCategoryRules,
    canManageGa4InsightsRules,
    handleDeleteItemCategoryRule,
    handleCreateItemCategoryRule,
    itemCategoryRuleForm,
    setItemCategoryRuleForm,
    itemCategoryRuleSaving,
}) => (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Items', '商品分析')}</div>
                                <div
                                    style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', cursor: 'help' }}
                                    title={t(
                                        'Always compares the last 7 days vs. the prior 7 days, independent of the date range above. Items with a small prior base can swing wildly — cross-check the raw counts.',
                                        '固定比較近 7 天 vs 前 7 天，與上方期間選擇無關；前期瀏覽極少的商品成長率波動大，請搭配原始次數判讀。'
                                    )}
                                >
                                    {t('View growth compares the last 7 days vs. the prior 7 days.', '瀏覽成長比較固定用近 7 天 vs 前 7 天。')} ⓘ
                                </div>
                            </div>
                            <DaySelector value={itemsDays} onChange={(d) => { setItemsDays(d); loadItems(propertyId, d); }} />
                        </div>
                        {itemsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{itemsError}</div>}
                        {itemsSnapshot?.payload?.used_fallback_conversion_metrics && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'GA4 could not return the official cart/purchase rate for this property; showing a locally computed rate instead.',
                                    '此屬性無法取得 GA4 官方加購/購買率，改顯示本地計算的比率。'
                                )}
                            </div>
                        )}
                        {itemsSnapshot?.payload?.category_breakdown_error && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'Could not fetch item category data from GA4 (temporary), so every item shows "Uncategorized" below.',
                                    '暫時無法從 GA4 取得商品分類資料，以下商品因此都顯示「未分類」（非您網站真的沒有分類）。'
                                )}
                            </div>
                        )}
                        {itemsLoading && !itemsSnapshot ? (
                            emptyState(t('Loading items…', '載入商品資料中…'))
                        ) : itemsSnapshot?.payload?.items?.length ? (
                            <>
                                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '12px', alignItems: 'center' }}>
                                    <select
                                        value={itemsCategoryFilter}
                                        onChange={(event) => setItemsCategoryFilter(event.target.value)}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    >
                                        <option value="all">{t('All categories', '全部分類')} ({itemsSnapshot.payload.items.length})</option>
                                        {Object.entries(itemsSnapshot.payload.category_counts || {}).map(([cat, count]) => (
                                            <option key={cat} value={cat}>
                                                {cat === '(not set)' ? t('Uncategorized', '未分類') : cat} ({count})
                                            </option>
                                        ))}
                                    </select>
                                    <input
                                        type="text"
                                        value={itemsSearchQuery}
                                        onChange={(event) => setItemsSearchQuery(event.target.value)}
                                        placeholder={t('Search item name…', '搜尋商品名稱…')}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    />
                                </div>
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                                {renderItemsSortHeader('itemName', t('Item', '商品'))}
                                                {renderItemsSortHeader('item_category', t('Category', '分類'))}
                                                {renderItemsSortHeader('itemsViewed', t('Views', '瀏覽'))}
                                                {renderItemsSortHeader('cart_to_view_rate', t('Add-to-cart rate', '瀏覽後加購率'), itemsSnapshot.payload.cart_to_view_rate_definition || '')}
                                                {renderItemsSortHeader('purchase_to_view_rate', t('Purchase rate', '瀏覽後購買率'), itemsSnapshot.payload.purchase_to_view_rate_definition || '')}
                                                {renderItemsSortHeader('views_growth_rate', t('View growth', '瀏覽成長'))}
                                                {renderItemsSortHeader('itemRevenue', t('Revenue', '營收'))}
                                                <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sortedItemsRows(
                                                itemsSnapshot.payload.items
                                                    .filter((row) => itemsCategoryFilter === 'all' || row.item_category === itemsCategoryFilter)
                                                    .filter((row) => !itemsSearchQuery.trim() || row.itemName?.toLowerCase().includes(itemsSearchQuery.trim().toLowerCase()))
                                            )
                                                .map((row) => {
                                                    const isNewEntry = row.views_prior_7d === 0 && row.views_recent_7d > 0;
                                                    return (
                                                        <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                            <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                                                            <td
                                                                style={{ padding: '6px', color: 'var(--text-secondary)', cursor: 'help' }}
                                                                title={tr(language, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.en, ITEM_CATEGORY_SOURCE_LABELS[row.item_category_source]?.zh)}
                                                            >
                                                                {row.item_category === '(not set)' ? t('Uncategorized', '未分類') : row.item_category}
                                                                {row.item_category_source === 'custom_rule' && ' ✎'}
                                                            </td>
                                                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemsViewed)}</td>
                                                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.cart_to_view_rate)}</td>
                                                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.purchase_to_view_rate)}</td>
                                                            <td
                                                                style={{ padding: '6px', color: 'var(--text-secondary)', cursor: 'help' }}
                                                                title={t(
                                                                    `Last 7 days: ${fmtNumber(row.views_recent_7d)} / Prior 7 days: ${fmtNumber(row.views_prior_7d)}`,
                                                                    `近 7 天 ${fmtNumber(row.views_recent_7d)} 次 / 前 7 天 ${fmtNumber(row.views_prior_7d)} 次`
                                                                )}
                                                            >
                                                                {isNewEntry ? (
                                                                    <span style={badgeStyle('new_entry')}>{t('New entry', '新進榜')}</span>
                                                                ) : (
                                                                    fmtPct(row.views_growth_rate)
                                                                )}
                                                            </td>
                                                            <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemRevenue)}</td>
                                                            <td style={{ padding: '6px' }}>
                                                                {row.is_potential && <span style={badgeStyle('potential')}>{t('Potential', '潛力商品')}</span>}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                        </tbody>
                                    </table>
                                </div>
                            </>
                        ) : (
                            emptyState(t('No item data.', '暫無商品資料。'))
                        )}
                    </section>

                    <section style={baseCardStyle}>
                        <button
                            type="button"
                            onClick={() => setItemCategoryRulesOpen((prev) => !prev)}
                            style={{ ...secondaryButtonStyle, width: '100%', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                        >
                            <span>{t('Category rules (fills gaps when GA4 has no category)', '分類規則（補充 GA4 沒有分類的商品）')}</span>
                            <span>{itemCategoryRulesOpen ? '▲' : '▼'}</span>
                        </button>
                        {itemCategoryRulesOpen && (
                            <div style={{ marginTop: '14px', display: 'grid', gap: '14px' }}>
                                <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                    {t(
                                        'GA4\'s own item category always wins when present. These rules only fill in a category for items GA4 reports as uncategorized.',
                                        'GA4 本身回報的商品分類永遠優先；這裡的規則只補充 GA4 顯示「未分類」的商品。'
                                    )}
                                </div>
                                {itemCategoryRulesError && <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>{itemCategoryRulesError}</div>}
                                {itemCategoryRulesLoading && !itemCategoryRules ? (
                                    emptyState(t('Loading rules…', '載入規則中…'))
                                ) : itemCategoryRules && itemCategoryRules.length === 0 ? (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                        {t('No category rules yet.', '目前沒有分類規則。')}
                                    </div>
                                ) : (
                                    <div style={{ display: 'grid', gap: '8px' }}>
                                        {(itemCategoryRules || []).map((rule) => (
                                            <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '10px 12px', gap: '8px', flexWrap: 'wrap' }}>
                                                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                                                    <span style={badgeStyle(rule.category)}>{rule.category}</span>
                                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                                        {tr(language, LANDING_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.en, LANDING_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.zh)}
                                                    </span>
                                                    <code style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{rule.pattern}</code>
                                                    <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('priority', '優先序')} {rule.priority}</span>
                                                </div>
                                                {canManageGa4InsightsRules && (
                                                    <button type="button" style={{ ...secondaryButtonStyle, padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => handleDeleteItemCategoryRule(rule.id)}>
                                                        {t('Delete', '刪除')}
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {canManageGa4InsightsRules ? (
                                    <form onSubmit={handleCreateItemCategoryRule} style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(5, minmax(0, 1fr))' }}>
                                        <input
                                            type="text"
                                            value={itemCategoryRuleForm.category}
                                            onChange={(event) => setItemCategoryRuleForm((prev) => ({ ...prev, category: event.target.value }))}
                                            placeholder={t('Category name (e.g. Pest Control)', '分類名稱（例：驅蟲用品）')}
                                            style={inputStyle}
                                        />
                                        <select value={itemCategoryRuleForm.match_type} onChange={(event) => setItemCategoryRuleForm((prev) => ({ ...prev, match_type: event.target.value }))} style={inputStyle}>
                                            {LANDING_MATCH_TYPE_OPTIONS.map((option) => (
                                                <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                            ))}
                                        </select>
                                        <input
                                            type="text"
                                            value={itemCategoryRuleForm.pattern}
                                            onChange={(event) => setItemCategoryRuleForm((prev) => ({ ...prev, pattern: event.target.value }))}
                                            placeholder={t('Pattern (matches item name)', '比對字串（比對商品名稱）')}
                                            style={inputStyle}
                                        />
                                        <input
                                            type="number"
                                            min="0"
                                            value={itemCategoryRuleForm.priority}
                                            onChange={(event) => setItemCategoryRuleForm((prev) => ({ ...prev, priority: event.target.value }))}
                                            placeholder={t('Priority', '優先序')}
                                            style={inputStyle}
                                        />
                                        <button type="submit" style={buttonStyle} disabled={itemCategoryRuleSaving || !itemCategoryRuleForm.category.trim() || !itemCategoryRuleForm.pattern.trim()}>
                                            {itemCategoryRuleSaving ? t('Saving…', '儲存中…') : t('Add rule', '新增規則')}
                                        </button>
                                    </form>
                                ) : (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                        {t('You do not have permission to manage category rules.', '您沒有管理分類規則的權限。')}
                                    </div>
                                )}
                            </div>
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={itemsSnapshot}
                        kind="item"
                        contextLabel={t(
                            `Property ${propertyId}; period ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；期間 ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({
                            items: itemsSnapshot?.payload?.items || [],
                            category_counts: itemsSnapshot?.payload?.category_counts || {},
                        })}
                    />
    </>
);

export default ItemsTab;
