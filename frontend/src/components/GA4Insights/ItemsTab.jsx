import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    CHANNEL_DIMENSION_OPTIONS,
    CHANNEL_GROUP_MATCH_TYPE_OPTIONS,
    ITEM_CATEGORY_SOURCE_LABELS,
    LANDING_MATCH_TYPE_OPTIONS,
    TablePager,
    badgeStyle,
    baseCardStyle,
    buttonStyle,
    channelDimensionLabel,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';

const ITEMS_PAGE_SIZE = 25;

// docs/46：同到達頁分頁，把目前的渠道篩選狀態轉成一句話塞進 AI 解讀的
// contextLabel，避免 AI 把篩選後的商品表現誤當成全店表現來描述。
const channelScopeLabel = (payload, language, t) => {
    if (!payload?.channel_dimension) return null;
    const dimLabel = channelDimensionLabel(payload.channel_dimension, language);
    if (payload.channel_group) {
        return t(`channel filter: ${dimLabel} = custom group "${payload.channel_group}"`, `渠道篩選：${dimLabel} = 自訂分組「${payload.channel_group}」`);
    }
    if (payload.channel_value) {
        return t(`channel filter: ${dimLabel} = "${payload.channel_value}"`, `渠道篩選：${dimLabel} = 「${payload.channel_value}」`);
    }
    return null;
};

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
    itemsChannelDimension,
    setItemsChannelDimension,
    itemsChannelValue,
    setItemsChannelValue,
    itemsChannelValues,
    itemsChannelValuesLoading,
    loadItemsChannelValues,
    itemsChannelGroup,
    setItemsChannelGroup,
    itemsChannelGroups,
    itemsChannelGroupsLoading,
    loadItemsChannelGroups,
    itemsChannelGroupRulesOpen,
    setItemsChannelGroupRulesOpen,
    itemsChannelGroupRules,
    itemsChannelGroupRulesLoading,
    itemsChannelGroupRulesError,
    loadItemsChannelGroupRules,
    handleCreateItemsChannelGroupRule,
    handleDeleteItemsChannelGroupRule,
    itemsChannelGroupRuleForm,
    setItemsChannelGroupRuleForm,
    itemsChannelGroupRuleSaving,
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
}) => {
    const [itemsPage, setItemsPage] = useState(1);

    const filteredSortedItems = useMemo(() => (
        sortedItemsRows(
            (itemsSnapshot?.payload?.items || [])
                .filter((row) => itemsCategoryFilter === 'all' || row.item_category === itemsCategoryFilter)
                .filter((row) => !itemsSearchQuery.trim() || row.itemName?.toLowerCase().includes(itemsSearchQuery.trim().toLowerCase()))
        )
    ), [itemsSnapshot, itemsCategoryFilter, itemsSearchQuery, sortedItemsRows]);

    const itemsTotalPages = Math.max(1, Math.ceil(filteredSortedItems.length / ITEMS_PAGE_SIZE));
    const itemsPageClamped = Math.min(itemsPage, itemsTotalPages);
    const pagedItems = filteredSortedItems.slice(
        (itemsPageClamped - 1) * ITEMS_PAGE_SIZE,
        itemsPageClamped * ITEMS_PAGE_SIZE
    );

    // 篩選/搜尋條件或資料快照變動時重置回第一頁，避免停在一個已經不存在的頁碼。
    useEffect(() => {
        setItemsPage(1);
    }, [itemsCategoryFilter, itemsSearchQuery, itemsSnapshot?.snapshot_id]);

    return (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Items', '商品分析')}</div>
                                <div
                                    style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', cursor: 'help' }}
                                    title={t(
                                        'Always compares the last 7 days vs. the prior 7 days, independent of the date range above and of the channel filter below. Items with a small prior base can swing wildly — cross-check the raw counts.',
                                        '固定比較近 7 天 vs 前 7 天，與上方期間選擇及下方渠道篩選皆無關（全渠道成長趨勢）；前期瀏覽極少的商品成長率波動大，請搭配原始次數判讀。'
                                    )}
                                >
                                    {t('View growth compares the last 7 days vs. the prior 7 days (all channels).', '瀏覽成長比較固定用近 7 天 vs 前 7 天（全渠道，不受下方篩選影響）。')} ⓘ
                                </div>
                            </div>
                            <DaySelector value={itemsDays} onChange={(d) => {
                                setItemsDays(d);
                                loadItems(propertyId, d);
                                if (itemsChannelDimension) loadItemsChannelValues(propertyId, d, itemsChannelDimension);
                            }} />
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
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px', alignItems: 'center' }}>
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
                                    <span style={{ width: '1px', alignSelf: 'stretch', background: 'var(--glass-border)', margin: '0 2px' }} />
                                    {/* docs/45：渠道篩選只影響主表格（瀏覽/加購/購買數與比率），不影響
                                        上方瀏覽成長比較與商品分類拆解，已在表頭 ⓘ 提示標注。三個下拉跟
                                        到達頁分頁同一套邏輯：渠道值／自訂分組互斥，選了維度才顯示後兩個。 */}
                                    <select
                                        value={itemsChannelDimension}
                                        onChange={(event) => {
                                            const nextDimension = event.target.value;
                                            setItemsChannelDimension(nextDimension);
                                            setItemsChannelValue('');
                                            setItemsChannelGroup('');
                                            loadItemsChannelValues(propertyId, itemsDays, nextDimension);
                                            loadItemsChannelGroups(propertyId, nextDimension);
                                            if (itemsChannelGroupRulesOpen) loadItemsChannelGroupRules(propertyId, nextDimension);
                                            loadItems(propertyId, itemsDays, nextDimension, '', '');
                                        }}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    >
                                        <option value="">{t('No channel filter', '不篩選渠道')}</option>
                                        {CHANNEL_DIMENSION_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                        ))}
                                    </select>
                                    {itemsChannelDimension && (
                                        <select
                                            value={itemsChannelValue}
                                            onChange={(event) => {
                                                const nextValue = event.target.value;
                                                setItemsChannelValue(nextValue);
                                                setItemsChannelGroup('');
                                                loadItems(propertyId, itemsDays, itemsChannelDimension, nextValue, '');
                                            }}
                                            disabled={itemsChannelValuesLoading}
                                            style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: itemsChannelValuesLoading ? 0.6 : 1 }}
                                        >
                                            <option value="">{t('All channel values', '全部渠道')}</option>
                                            {itemsChannelValues.map((value) => (
                                                <option key={value} value={value}>{value}</option>
                                            ))}
                                        </select>
                                    )}
                                    {itemsChannelDimension && (
                                        <select
                                            value={itemsChannelGroup}
                                            onChange={(event) => {
                                                const nextGroup = event.target.value;
                                                setItemsChannelGroup(nextGroup);
                                                setItemsChannelValue('');
                                                loadItems(propertyId, itemsDays, itemsChannelDimension, '', nextGroup);
                                            }}
                                            disabled={itemsChannelGroupsLoading}
                                            style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: itemsChannelGroupsLoading ? 0.6 : 1 }}
                                        >
                                            <option value="">{t('No custom group', '不用自訂分組')}</option>
                                            {itemsChannelGroups.map((group) => (
                                                <option key={group.group_label} value={group.group_label}>
                                                    {group.group_label} ({group.rule_count})
                                                </option>
                                            ))}
                                        </select>
                                    )}
                                    {(itemsChannelValuesLoading || itemsChannelGroupsLoading) && (
                                        <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('Loading channels…', '載入渠道清單中…')}</span>
                                    )}
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
                                            {pagedItems
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
                                <TablePager
                                    page={itemsPageClamped}
                                    totalPages={itemsTotalPages}
                                    onPageChange={setItemsPage}
                                    language={language}
                                />
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

                    {/* docs/45：渠道分組規則管理面板，複用到達頁分頁同一套規則（綁維度
                        不綁分頁），沿用上方篩選列已選的「維度」，未選維度時提示先選維度。 */}
                    <section style={baseCardStyle}>
                        <button
                            type="button"
                            onClick={() => {
                                const next = !itemsChannelGroupRulesOpen;
                                setItemsChannelGroupRulesOpen(next);
                                if (next && itemsChannelDimension) {
                                    loadItemsChannelGroupRules(propertyId, itemsChannelDimension);
                                }
                            }}
                            style={{ ...secondaryButtonStyle, width: '100%', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                        >
                            <span>{t('Channel group rules', '渠道分組規則')}</span>
                            <span>{itemsChannelGroupRulesOpen ? '▲' : '▼'}</span>
                        </button>
                        {itemsChannelGroupRulesOpen && (
                            <div style={{ marginTop: '14px', display: 'grid', gap: '14px' }}>
                                {!itemsChannelDimension ? (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                        {t('Select a channel dimension above first to manage its group rules.', '請先在上方篩選列選擇一個渠道維度，才能管理該維度的分組規則。')}
                                    </div>
                                ) : (
                                    <>
                                        <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                            {t(
                                                'Rules are shared with the Landing pages tab (bound to the dimension, not the tab).',
                                                '規則跟「到達頁分析」分頁共用（綁定維度，不綁分頁）。'
                                            )}
                                        </div>
                                        {itemsChannelGroupRulesError && <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>{itemsChannelGroupRulesError}</div>}
                                        {itemsChannelGroupRulesLoading && !itemsChannelGroupRules ? (
                                            emptyState(t('Loading rules…', '載入規則中…'))
                                        ) : itemsChannelGroupRules && itemsChannelGroupRules.length === 0 ? (
                                            <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                                {t('No custom group rules yet for this dimension.', '這個維度目前沒有自訂分組規則。')}
                                            </div>
                                        ) : (
                                            <div style={{ display: 'grid', gap: '8px' }}>
                                                {(itemsChannelGroupRules || []).map((rule) => (
                                                    <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '10px 12px', gap: '8px', flexWrap: 'wrap' }}>
                                                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                                                            <span style={badgeStyle('product')}>{rule.group_label}</span>
                                                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                                                {tr(language, CHANNEL_GROUP_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.en, CHANNEL_GROUP_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.zh)}
                                                            </span>
                                                            <code style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{rule.pattern}</code>
                                                            <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('priority', '優先序')} {rule.priority}</span>
                                                        </div>
                                                        {canManageGa4InsightsRules && (
                                                            <button type="button" style={{ ...secondaryButtonStyle, padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => handleDeleteItemsChannelGroupRule(rule.id)}>
                                                                {t('Delete', '刪除')}
                                                            </button>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {canManageGa4InsightsRules ? (
                                            <form onSubmit={handleCreateItemsChannelGroupRule} style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(5, minmax(0, 1fr))' }}>
                                                <input
                                                    type="text"
                                                    value={itemsChannelGroupRuleForm.group_label}
                                                    onChange={(event) => setItemsChannelGroupRuleForm((prev) => ({ ...prev, group_label: event.target.value }))}
                                                    placeholder={t('Group name (e.g. Facebook Ads)', '分組名稱（例：Facebook 付費廣告）')}
                                                    style={inputStyle}
                                                />
                                                <select value={itemsChannelGroupRuleForm.match_type} onChange={(event) => setItemsChannelGroupRuleForm((prev) => ({ ...prev, match_type: event.target.value }))} style={inputStyle}>
                                                    {CHANNEL_GROUP_MATCH_TYPE_OPTIONS.map((option) => (
                                                        <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                                    ))}
                                                </select>
                                                <input
                                                    type="text"
                                                    value={itemsChannelGroupRuleForm.pattern}
                                                    onChange={(event) => setItemsChannelGroupRuleForm((prev) => ({ ...prev, pattern: event.target.value }))}
                                                    placeholder={t('Pattern (e.g. facebook / cpc)', '比對字串（例：facebook / cpc）')}
                                                    style={inputStyle}
                                                />
                                                <input
                                                    type="number"
                                                    min="0"
                                                    value={itemsChannelGroupRuleForm.priority}
                                                    onChange={(event) => setItemsChannelGroupRuleForm((prev) => ({ ...prev, priority: event.target.value }))}
                                                    placeholder={t('Priority', '優先序')}
                                                    style={inputStyle}
                                                />
                                                <button type="submit" style={buttonStyle} disabled={itemsChannelGroupRuleSaving || !itemsChannelGroupRuleForm.group_label.trim() || !itemsChannelGroupRuleForm.pattern.trim()}>
                                                    {itemsChannelGroupRuleSaving ? t('Saving…', '儲存中…') : t('Add rule', '新增規則')}
                                                </button>
                                            </form>
                                        ) : (
                                            <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                                {t('You do not have permission to manage classification rules.', '您沒有管理分類規則的權限。')}
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={itemsSnapshot}
                        kind="item"
                        contextLabel={[
                            t(
                                `Property ${propertyId}; period ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`,
                                `屬性 ${propertyId}；期間 ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`
                            ),
                            channelScopeLabel(itemsSnapshot?.payload, language, t),
                        ].filter(Boolean).join('；')}
                        buildPayload={() => ({
                            channel_dimension: itemsSnapshot?.payload?.channel_dimension || null,
                            channel_value: itemsSnapshot?.payload?.channel_value || null,
                            channel_group: itemsSnapshot?.payload?.channel_group || null,
                            items: itemsSnapshot?.payload?.items || [],
                            category_counts: itemsSnapshot?.payload?.category_counts || {},
                        })}
                    />
    </>
    );
};

export default ItemsTab;
