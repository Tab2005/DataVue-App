import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    DaySelector,
    CHANNEL_DIMENSION_OPTIONS,
    CHANNEL_GROUP_MATCH_TYPE_OPTIONS,
    LANDING_MATCH_TYPE_OPTIONS,
    TablePager,
    badgeStyle,
    baseCardStyle,
    buttonStyle,
    channelDimensionLabel,
    emptyState,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';
// docs/64：表格主體與警示橫幅跟分享頁共用同一份實作。可排序表頭是本頁專屬的
// 互動，用 renderHeader 傳進去，欄位定義本身仍然只有共用元件那一份。
import { ItemsTable, PayloadWarnings } from './GA4InsightsTables';

const ITEMS_PAGE_SIZE = 25;

// docs/55：跟上一期比較開啟時，讓使用者依「單一指標」的漲跌篩選表格列。
const ITEMS_GROWTH_METRIC_OPTIONS = [
    { value: 'views', field: 'views_compare_growth_rate', labelEn: 'Views', labelZh: '瀏覽數' },
    { value: 'cart_to_view_rate', field: 'cart_to_view_rate_delta_pp', labelEn: 'Add-to-cart rate', labelZh: '加購率' },
    { value: 'purchase_to_view_rate', field: 'purchase_to_view_rate_delta_pp', labelEn: 'Purchase rate', labelZh: '購買率' },
    { value: 'revenue', field: 'revenue_growth_rate', labelEn: 'Revenue', labelZh: '營收' },
];

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

// docs/53：分類篩選（下拉選單）是純前端二次篩選，本來完全不會反映在 AI
// 解讀的 contextLabel 裡，容易讓 AI 誤以為在分析全部分類的商品。商品分類
// 是依 GA4 實際分類/自訂規則動態產生的清單，不像到達頁有固定 4 種，直接
// 顯示原始分類字串即可，(not set) 顯示成「未分類」跟表格既有慣例一致。
const categoryScopeLabel = (categoryFilter, t) => {
    if (!categoryFilter || categoryFilter === 'all') return null;
    const label = categoryFilter === '(not set)' ? t('Uncategorized', '未分類') : categoryFilter;
    return t(`category filter: ${label}`, `分類篩選：${label}`);
};

// docs/54：跟上一期比較開啟時，告訴 AI 現在看到的數字已經有比較資訊可以提。
const compareScopeLabel = (payload, t) => {
    if (!payload?.compare_enabled) return null;
    if (payload.compare_query_error) return null;
    return t(
        `compared to prior period (${payload.compare_start_date} ~ ${payload.compare_end_date})`,
        `已啟用上一期比較（${payload.compare_start_date} ~ ${payload.compare_end_date}）`
    );
};

const ItemsTab = ({
    language,
    t,
    isMobile,
    propertyId,
    canManageGa4InsightsRules,
    // docs/66：這個分頁的整組狀態與行為都在 useGA4ItemsTab 裡，這裡只收一個
    // 物件（原本是 53 個 props）。下面解構出來的名字與原本一致，元件內容不變。
    items,
}) => {
    const {
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
        itemsCompareEnabled,
        setItemsCompareEnabled,
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
        renderItemsSortHeader,
        sortedItemsRows,
        itemCategoryRulesOpen,
        setItemCategoryRulesOpen,
        itemCategoryRulesError,
        itemCategoryRulesLoading,
        itemCategoryRules,
        handleDeleteItemCategoryRule,
        handleCreateItemCategoryRule,
        itemCategoryRuleForm,
        setItemCategoryRuleForm,
        itemCategoryRuleSaving,
    } = items;

    const [itemsPage, setItemsPage] = useState(1);
    // docs/55：指標＋方向兩個下拉，只有 itemsCompareEnabled 時才顯示/生效。
    const [itemsGrowthMetric, setItemsGrowthMetric] = useState('');
    const [itemsGrowthDirection, setItemsGrowthDirection] = useState('all');

    const filteredSortedItems = useMemo(() => {
        const growthField = ITEMS_GROWTH_METRIC_OPTIONS.find((m) => m.value === itemsGrowthMetric)?.field;
        return sortedItemsRows(
            (itemsSnapshot?.payload?.items || [])
                .filter((row) => itemsCategoryFilter === 'all' || row.item_category === itemsCategoryFilter)
                .filter((row) => !itemsSearchQuery.trim() || row.itemName?.toLowerCase().includes(itemsSearchQuery.trim().toLowerCase()))
                .filter((row) => {
                    if (!itemsCompareEnabled || !growthField || itemsGrowthDirection === 'all') return true;
                    // 新商品沒有比較數值，方向篩選（上升/持平/下降）下一律篩掉，選「全部」時不受影響。
                    if (row.is_new || row[growthField] == null) return false;
                    if (itemsGrowthDirection === 'up') return row[growthField] > 0;
                    if (itemsGrowthDirection === 'down') return row[growthField] < 0;
                    return row[growthField] === 0;
                })
        );
    }, [itemsSnapshot, itemsCategoryFilter, itemsSearchQuery, sortedItemsRows, itemsCompareEnabled, itemsGrowthMetric, itemsGrowthDirection]);

    const itemsTotalPages = Math.max(1, Math.ceil(filteredSortedItems.length / ITEMS_PAGE_SIZE));
    const itemsPageClamped = Math.min(itemsPage, itemsTotalPages);
    const pagedItems = filteredSortedItems.slice(
        (itemsPageClamped - 1) * ITEMS_PAGE_SIZE,
        itemsPageClamped * ITEMS_PAGE_SIZE
    );

    // 篩選/搜尋條件或資料快照變動時重置回第一頁，避免停在一個已經不存在的頁碼。
    useEffect(() => {
        setItemsPage(1);
    }, [itemsCategoryFilter, itemsSearchQuery, itemsGrowthMetric, itemsGrowthDirection, itemsSnapshot?.snapshot_id]);

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
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                {/* docs/54：跟上一期比較開關，預設關閉；跟固定的「近7天/前7天瀏覽
                                    成長」是兩件獨立並存的事，這個開關比較的是「跟著上方期間走」的
                                    另一組資料。 */}
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={itemsCompareEnabled}
                                        onChange={(event) => {
                                            const next = event.target.checked;
                                            setItemsCompareEnabled(next);
                                            if (!next) {
                                                // docs/55：關閉比較時重置篩選條件，避免下拉隱藏但殘留舊篩選。
                                                setItemsGrowthMetric('');
                                                setItemsGrowthDirection('all');
                                            }
                                            loadItems(propertyId, itemsDays, itemsChannelDimension, itemsChannelValue, itemsChannelGroup, next);
                                        }}
                                    />
                                    {t('Compare to prior period', '比較上一期')}
                                </label>
                                <DaySelector language={language} value={itemsDays} onChange={(d) => {
                                    setItemsDays(d);
                                    loadItems(propertyId, d);
                                    if (itemsChannelDimension) loadItemsChannelValues(propertyId, d, itemsChannelDimension);
                                }} />
                            </div>
                        </div>
                        {itemsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{itemsError}</div>}
                        <PayloadWarnings t={t} payload={itemsSnapshot?.payload} kind="item" />
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
                                    {/* docs/55：指標＋方向篩選只有比較上一期開啟時才顯示，選了「全部」
                                        以外的方向會篩掉沒有比較數值的新商品。 */}
                                    {itemsCompareEnabled && (
                                        <>
                                            <span style={{ width: '1px', alignSelf: 'stretch', background: 'var(--glass-border)', margin: '0 2px' }} />
                                            <select
                                                value={itemsGrowthMetric}
                                                onChange={(event) => setItemsGrowthMetric(event.target.value)}
                                                style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                            >
                                                <option value="">{t('Growth metric…', '選擇成長指標…')}</option>
                                                {ITEMS_GROWTH_METRIC_OPTIONS.map((option) => (
                                                    <option key={option.value} value={option.value}>{t(option.labelEn, option.labelZh)}</option>
                                                ))}
                                            </select>
                                            <select
                                                value={itemsGrowthDirection}
                                                onChange={(event) => setItemsGrowthDirection(event.target.value)}
                                                disabled={!itemsGrowthMetric}
                                                style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: itemsGrowthMetric ? 1 : 0.6 }}
                                            >
                                                <option value="all">{t('All', '全部')}</option>
                                                <option value="up">{t('Up', '上升')}</option>
                                                <option value="flat">{t('Flat', '持平')}</option>
                                                <option value="down">{t('Down', '下降')}</option>
                                            </select>
                                        </>
                                    )}
                                </div>
                                <ItemsTable
                                    language={language}
                                    t={t}
                                    payload={itemsSnapshot.payload}
                                    rows={pagedItems}
                                    renderHeader={renderItemsSortHeader}
                                />
                                <TablePager
                                    page={itemsPageClamped}
                                    totalPages={itemsTotalPages}
                                    onPageChange={setItemsPage}
                                    language={language}
                                    totalItems={filteredSortedItems.length}
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
                            categoryScopeLabel(itemsCategoryFilter, t),
                            compareScopeLabel(itemsSnapshot?.payload, t),
                        ].filter(Boolean).join('；')}
                        shareUrlParams={itemsCategoryFilter !== 'all' ? { category: itemsCategoryFilter } : {}}
                        buildPayload={() => ({
                            channel_dimension: itemsSnapshot?.payload?.channel_dimension || null,
                            channel_value: itemsSnapshot?.payload?.channel_value || null,
                            channel_group: itemsSnapshot?.payload?.channel_group || null,
                            // docs/53：改用畫面上已經套用分類篩選後的清單，AI 分析的內容才會
                            // 跟目前選的分類一致；category_counts 仍傳完整版，讓 AI 知道這個
                            // 屬性整體的分類分布。
                            items: filteredSortedItems,
                            category_counts: itemsSnapshot?.payload?.category_counts || {},
                            // docs/54：跟上一期比較——每列已經帶有 *_growth_rate/*_delta_pp/is_new
                            // 欄位，這裡額外補上比較期間，AI 才知道「上一期」具體是哪段日期。
                            compare_enabled: itemsSnapshot?.payload?.compare_enabled || false,
                            compare_start_date: itemsSnapshot?.payload?.compare_start_date || null,
                            compare_end_date: itemsSnapshot?.payload?.compare_end_date || null,
                        })}
                    />
    </>
    );
};

export default ItemsTab;
