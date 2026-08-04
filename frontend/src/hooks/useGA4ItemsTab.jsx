// frontend/src/hooks/useGA4ItemsTab.js (docs/66)
//
// 商品分頁的全部狀態、載入、排序與規則 CRUD。原本這些散在 GA4Insights.jsx
// 裡，再以 53 個 props 傳進 ItemsTab（docs/59 P2-1）。
//
// 跟 useGA4LandingPagesTab 一樣由父層呼叫——分頁是條件渲染的，狀態放父層
// 才能在切走再切回來時保住快照與篩選條件（理由見該檔開頭）。
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';
import { ITEMS_SORT_COLUMNS } from '../components/GA4Insights/GA4InsightsShared';

const EMPTY_GROUP_RULE_FORM = { group_label: '', match_type: 'contains', pattern: '', priority: 0 };
const EMPTY_CATEGORY_RULE_FORM = { category: '', match_type: 'prefix', pattern: '', priority: 0 };

export const useGA4ItemsTab = ({ propertyId, t }) => {
    const [itemsDays, setItemsDays] = useState(7);
    const [itemsSnapshot, setItemsSnapshot] = useState(null);
    const [itemsLoading, setItemsLoading] = useState(false);
    const [itemsError, setItemsError] = useState('');
    const [itemsCategoryFilter, setItemsCategoryFilter] = useState('all');
    const [itemsSearchQuery, setItemsSearchQuery] = useState('');
    // docs/54：跟上一期比較開關，預設關閉（不多打一次 GA4 查詢）。
    const [itemsCompareEnabled, setItemsCompareEnabled] = useState(false);
    const [itemsSortKey, setItemsSortKey] = useState(null);
    const [itemsSortDirection, setItemsSortDirection] = useState('desc');

    // docs/45：商品渠道篩選，比照到達頁（42+44）同一套維度／渠道值／自訂
    // 分組三個下拉＋規則管理面板；渠道分組規則跨分頁共用（綁維度不綁分頁）。
    const [itemsChannelDimension, setItemsChannelDimension] = useState('');
    const [itemsChannelValue, setItemsChannelValue] = useState('');
    const [itemsChannelValues, setItemsChannelValues] = useState([]);
    const [itemsChannelValuesLoading, setItemsChannelValuesLoading] = useState(false);
    const [itemsChannelGroup, setItemsChannelGroup] = useState('');
    const [itemsChannelGroups, setItemsChannelGroups] = useState([]);
    const [itemsChannelGroupsLoading, setItemsChannelGroupsLoading] = useState(false);
    const [itemsChannelGroupRulesOpen, setItemsChannelGroupRulesOpen] = useState(false);
    const [itemsChannelGroupRules, setItemsChannelGroupRules] = useState(null);
    const [itemsChannelGroupRulesLoading, setItemsChannelGroupRulesLoading] = useState(false);
    const [itemsChannelGroupRulesError, setItemsChannelGroupRulesError] = useState('');
    const [itemsChannelGroupRuleSaving, setItemsChannelGroupRuleSaving] = useState(false);
    const [itemsChannelGroupRuleForm, setItemsChannelGroupRuleForm] = useState(EMPTY_GROUP_RULE_FORM);

    // 第 7 波：商品分類補充規則（GA4 itemCategory 缺值時的補充來源）
    const [itemCategoryRules, setItemCategoryRules] = useState(null);
    const [itemCategoryRulesOpen, setItemCategoryRulesOpen] = useState(false);
    const [itemCategoryRulesLoading, setItemCategoryRulesLoading] = useState(false);
    const [itemCategoryRulesError, setItemCategoryRulesError] = useState('');
    const [itemCategoryRuleSaving, setItemCategoryRuleSaving] = useState(false);
    const [itemCategoryRuleForm, setItemCategoryRuleForm] = useState(EMPTY_CATEGORY_RULE_FORM);

    const loadItems = async (
        pid, days,
        channelDimension = itemsChannelDimension,
        channelValue = itemsChannelValue,
        channelGroup = itemsChannelGroup,
        compare = itemsCompareEnabled,
    ) => {
        if (!pid) return;
        setItemsLoading(true);
        setItemsError('');
        try {
            setItemsSnapshot(
                await ga4InsightsService.getItems(
                    pid, days, channelDimension || null, channelValue || null, channelGroup || null, compare
                )
            );
        } catch (err) {
            setItemsError(err.message || t('Failed to load item insights.', '載入商品分析失敗。'));
        } finally {
            setItemsLoading(false);
        }
    };

    // docs/45：渠道值清單——沿用到達頁既有作法，複用渠道對照端點取實際
    // 存在的渠道值，不用另開新端點。
    const loadItemsChannelValues = async (pid, days, dimension) => {
        if (!pid || !dimension) {
            setItemsChannelValues([]);
            return;
        }
        setItemsChannelValuesLoading(true);
        try {
            const res = await ga4InsightsService.getChannels(pid, days, dimension);
            setItemsChannelValues((res.payload?.channels || []).map((c) => c.channel).filter(Boolean));
        } catch (err) {
            setItemsError(err.message || t('Failed to load channel values.', '載入渠道清單失敗。'));
        } finally {
            setItemsChannelValuesLoading(false);
        }
    };

    // docs/45：自訂分組清單——渠道分組規則綁定維度、不綁分頁，到達頁跟
    // 商品分頁共用同一批規則，這裡只是重新用目前選的維度查一次。
    const loadItemsChannelGroups = async (pid, dimension) => {
        if (!pid || !dimension) {
            setItemsChannelGroups([]);
            return;
        }
        setItemsChannelGroupsLoading(true);
        try {
            const res = await ga4InsightsService.listChannelGroups(pid, dimension);
            setItemsChannelGroups(res.groups || []);
        } catch (err) {
            setItemsError(err.message || t('Failed to load channel groups.', '載入自訂分組失敗。'));
        } finally {
            setItemsChannelGroupsLoading(false);
        }
    };

    const loadItemsChannelGroupRules = async (pid, dimension) => {
        if (!pid || !dimension) {
            setItemsChannelGroupRules([]);
            return;
        }
        setItemsChannelGroupRulesLoading(true);
        setItemsChannelGroupRulesError('');
        try {
            const res = await ga4InsightsService.listChannelGroupRules(pid, dimension);
            setItemsChannelGroupRules(res.rules || []);
        } catch (err) {
            setItemsChannelGroupRulesError(err.message || t('Failed to load channel group rules.', '載入渠道分組規則失敗。'));
        } finally {
            setItemsChannelGroupRulesLoading(false);
        }
    };

    const handleCreateItemsChannelGroupRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !itemsChannelDimension || !itemsChannelGroupRuleForm.group_label.trim() || !itemsChannelGroupRuleForm.pattern.trim()) return;
        setItemsChannelGroupRuleSaving(true);
        setItemsChannelGroupRulesError('');
        try {
            await ga4InsightsService.upsertChannelGroupRule({
                property_id: propertyId,
                channel_dimension: itemsChannelDimension,
                group_label: itemsChannelGroupRuleForm.group_label.trim(),
                match_type: itemsChannelGroupRuleForm.match_type,
                pattern: itemsChannelGroupRuleForm.pattern.trim(),
                priority: Number(itemsChannelGroupRuleForm.priority) || 0,
            });
            setItemsChannelGroupRuleForm((prev) => ({ ...prev, group_label: '', pattern: '' }));
            await loadItemsChannelGroupRules(propertyId, itemsChannelDimension);
            await loadItemsChannelGroups(propertyId, itemsChannelDimension);
        } catch (err) {
            setItemsChannelGroupRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setItemsChannelGroupRuleSaving(false);
        }
    };

    const handleDeleteItemsChannelGroupRule = async (ruleId) => {
        if (!window.confirm(t('Delete this channel group rule?', '要刪除此渠道分組規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteChannelGroupRule(ruleId);
            await loadItemsChannelGroupRules(propertyId, itemsChannelDimension);
            await loadItemsChannelGroups(propertyId, itemsChannelDimension);
        } catch (err) {
            setItemsChannelGroupRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const loadItemCategoryRules = async (pid) => {
        if (!pid) return;
        setItemCategoryRulesLoading(true);
        setItemCategoryRulesError('');
        try {
            const res = await ga4InsightsService.listItemCategoryRules(pid);
            setItemCategoryRules(res.rules || []);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to load item category rules.', '載入商品分類規則失敗。'));
        } finally {
            setItemCategoryRulesLoading(false);
        }
    };

    const handleCreateItemCategoryRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !itemCategoryRuleForm.category.trim() || !itemCategoryRuleForm.pattern.trim()) return;
        setItemCategoryRuleSaving(true);
        setItemCategoryRulesError('');
        try {
            await ga4InsightsService.upsertItemCategoryRule({
                property_id: propertyId,
                category: itemCategoryRuleForm.category.trim(),
                match_type: itemCategoryRuleForm.match_type,
                pattern: itemCategoryRuleForm.pattern.trim(),
                priority: Number(itemCategoryRuleForm.priority) || 0,
            });
            setItemCategoryRuleForm((prev) => ({ ...prev, category: '', pattern: '' }));
            await loadItemCategoryRules(propertyId);
            await loadItems(propertyId, itemsDays);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setItemCategoryRuleSaving(false);
        }
    };

    const handleDeleteItemCategoryRule = async (ruleId) => {
        if (!window.confirm(t('Delete this category rule?', '要刪除此分類規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteItemCategoryRule(ruleId);
            await loadItemCategoryRules(propertyId);
            await loadItems(propertyId, itemsDays);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const handleItemsSort = (key) => {
        if (itemsSortKey === key) {
            setItemsSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
        } else {
            setItemsSortKey(key);
            setItemsSortDirection(ITEMS_SORT_COLUMNS[key].defaultDir);
        }
    };

    // 商品分析表格的可排序表頭（點擊切換欄位/方向）。
    const renderItemsSortHeader = (key, label, tooltip) => {
        const isActive = itemsSortKey === key;
        const arrow = isActive ? (itemsSortDirection === 'asc' ? ' ▲' : ' ▼') : '';
        return (
            <th
                style={{ padding: '6px', cursor: 'pointer', userSelect: 'none', color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}
                title={tooltip}
                onClick={() => handleItemsSort(key)}
            >
                {label}{tooltip ? ' ⓘ' : ''}{arrow}
            </th>
        );
    };

    const sortedItemsRows = (rows) => {
        if (!itemsSortKey) {
            // 預設排序：潛力商品優先（既有行為）
            return [...rows].sort((a, b) => (b.is_potential ? 1 : 0) - (a.is_potential ? 1 : 0));
        }
        const meta = ITEMS_SORT_COLUMNS[itemsSortKey];
        const dir = itemsSortDirection === 'asc' ? 1 : -1;
        return [...rows].sort((a, b) => {
            const av = a[itemsSortKey];
            const bv = b[itemsSortKey];
            if (meta.type === 'string') {
                return dir * String(av || '').localeCompare(String(bv || ''));
            }
            return dir * ((av ?? 0) - (bv ?? 0));
        });
    };

    // 懶載入：只在首次進入商品分頁時抓一次（條件原本在父層 useEffect 裡）。
    const ensureLoaded = (pid) => {
        if (!pid) return;
        if (!itemsSnapshot) loadItems(pid, itemsDays);
        if (!itemCategoryRules) loadItemCategoryRules(pid);
    };

    const reset = () => {
        setItemsSnapshot(null);
        setItemsCategoryFilter('all');
        setItemsSearchQuery('');
        setItemsCompareEnabled(false);
        setItemCategoryRules(null);
    };

    return {
        itemsDays, setItemsDays,
        itemsSnapshot, itemsLoading, itemsError,
        itemsCategoryFilter, setItemsCategoryFilter,
        itemsSearchQuery, setItemsSearchQuery,
        itemsCompareEnabled, setItemsCompareEnabled,
        itemsChannelDimension, setItemsChannelDimension,
        itemsChannelValue, setItemsChannelValue,
        itemsChannelValues, itemsChannelValuesLoading,
        itemsChannelGroup, setItemsChannelGroup,
        itemsChannelGroups, itemsChannelGroupsLoading,
        itemsChannelGroupRulesOpen, setItemsChannelGroupRulesOpen,
        itemsChannelGroupRules, itemsChannelGroupRulesLoading, itemsChannelGroupRulesError,
        itemsChannelGroupRuleForm, setItemsChannelGroupRuleForm,
        itemsChannelGroupRuleSaving,
        itemCategoryRules, itemCategoryRulesOpen, setItemCategoryRulesOpen,
        itemCategoryRulesLoading, itemCategoryRulesError,
        itemCategoryRuleForm, setItemCategoryRuleForm, itemCategoryRuleSaving,
        loadItems,
        loadItemsChannelValues,
        loadItemsChannelGroups,
        loadItemsChannelGroupRules,
        handleCreateItemsChannelGroupRule,
        handleDeleteItemsChannelGroupRule,
        handleCreateItemCategoryRule,
        handleDeleteItemCategoryRule,
        renderItemsSortHeader,
        sortedItemsRows,
        ensureLoaded,
        reset,
    };
};

export default useGA4ItemsTab;
