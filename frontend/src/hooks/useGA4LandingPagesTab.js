// frontend/src/hooks/useGA4LandingPagesTab.js (docs/66)
//
// 到達頁分頁的全部狀態、載入與規則 CRUD。原本這些散在 GA4Insights.jsx 裡，
// 再以 51 個 props 傳進 LandingPagesTab——加一個欄位要在父層 state、傳遞、
// 子層解構三處同步改（docs/59 P2-1）。收進這個 hook 之後只改這一處。
//
// hook 刻意由**父層**呼叫、結果當一個 prop 傳下去，不是由分頁元件自己呼叫：
// 分頁是條件渲染的，切走就 unmount。狀態放在父層，切回來時快照與篩選條件
// 都還在、也不會重打 GA4 查詢；移進分頁元件就會每次切回來都重抓一次。
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';

const EMPTY_RULE_FORM = { category: 'product', match_type: 'prefix', pattern: '', priority: 0 };
const EMPTY_GROUP_RULE_FORM = { group_label: '', match_type: 'contains', pattern: '', priority: 0 };

export const useGA4LandingPagesTab = ({ propertyId, t }) => {
    const [landingDays, setLandingDays] = useState(7);
    const [landingSnapshot, setLandingSnapshot] = useState(null);
    const [landingLoading, setLandingLoading] = useState(false);
    const [landingError, setLandingError] = useState('');
    const [landingCategoryFilter, setLandingCategoryFilter] = useState('all');
    const [landingKeyEvent, setLandingKeyEvent] = useState('');
    // docs/54：跟上一期比較開關，預設關閉（不多打一次 GA4 查詢）。
    const [landingCompareEnabled, setLandingCompareEnabled] = useState(false);
    // docs/42：到達頁渠道篩選——維度＋渠道值兩層下拉，渠道值清單複用
    // getChannels 既有回應，不用另外開一支「列出渠道值」的端點。
    const [landingChannelDimension, setLandingChannelDimension] = useState('');
    const [landingChannelValue, setLandingChannelValue] = useState('');
    const [landingChannelValues, setLandingChannelValues] = useState([]);
    const [landingChannelValuesLoading, setLandingChannelValuesLoading] = useState(false);
    const [landingRules, setLandingRules] = useState(null);
    const [landingRulesOpen, setLandingRulesOpen] = useState(false);
    const [landingRulesLoading, setLandingRulesLoading] = useState(false);
    const [landingRulesError, setLandingRulesError] = useState('');
    const [landingRuleSaving, setLandingRuleSaving] = useState(false);
    const [landingRuleForm, setLandingRuleForm] = useState(EMPTY_RULE_FORM);

    // docs/44：渠道值自訂分組——第三個下拉（跟渠道值互斥），選了維度後才
    // 抓對應的分組清單；規則管理面板另外維護該維度底下的規則列表。
    const [landingChannelGroup, setLandingChannelGroup] = useState('');
    const [landingChannelGroups, setLandingChannelGroups] = useState([]);
    const [landingChannelGroupsLoading, setLandingChannelGroupsLoading] = useState(false);
    const [landingChannelGroupRulesOpen, setLandingChannelGroupRulesOpen] = useState(false);
    const [landingChannelGroupRules, setLandingChannelGroupRules] = useState(null);
    const [landingChannelGroupRulesLoading, setLandingChannelGroupRulesLoading] = useState(false);
    const [landingChannelGroupRulesError, setLandingChannelGroupRulesError] = useState('');
    const [landingChannelGroupRuleSaving, setLandingChannelGroupRuleSaving] = useState(false);
    const [landingChannelGroupRuleForm, setLandingChannelGroupRuleForm] = useState(EMPTY_GROUP_RULE_FORM);

    // 「沒傳就用目前 state」的預設參數語意原樣保留——呼叫端傳位置參數的
    // 寫法（例如只帶前兩個）跟抽 hook 之前完全一致。
    const loadLandingPages = async (
        pid, days,
        keyEvent = landingKeyEvent,
        channelDimension = landingChannelDimension,
        channelValue = landingChannelValue,
        channelGroup = landingChannelGroup,
        compare = landingCompareEnabled,
    ) => {
        if (!pid) return;
        setLandingLoading(true);
        setLandingError('');
        try {
            setLandingSnapshot(
                await ga4InsightsService.getLandingPages(
                    pid, days, keyEvent || null, channelDimension || null, channelValue || null, channelGroup || null, compare
                )
            );
        } catch (err) {
            setLandingError(err.message || t('Failed to load landing pages.', '載入到達頁分析失敗。'));
        } finally {
            setLandingLoading(false);
        }
    };

    // docs/42：渠道值清單——選了「維度」後，用該維度呼叫一次既有的渠道
    // 對照端點，取實際存在的渠道值來組第二層下拉選單，不用另開新端點。
    const loadLandingChannelValues = async (pid, days, dimension) => {
        if (!pid || !dimension) {
            setLandingChannelValues([]);
            return;
        }
        setLandingChannelValuesLoading(true);
        try {
            const res = await ga4InsightsService.getChannels(pid, days, dimension);
            setLandingChannelValues((res.payload?.channels || []).map((c) => c.channel).filter(Boolean));
        } catch (err) {
            setLandingError(err.message || t('Failed to load channel values.', '載入渠道清單失敗。'));
        } finally {
            setLandingChannelValuesLoading(false);
        }
    };

    // docs/44：渠道值自訂分組清單——跟渠道值清單不同，這是直接從資料庫的
    // 規則列表 derive 出來的（不用打 GA4 API），不需要帶 days 參數。
    const loadLandingChannelGroups = async (pid, dimension) => {
        if (!pid || !dimension) {
            setLandingChannelGroups([]);
            return;
        }
        setLandingChannelGroupsLoading(true);
        try {
            const res = await ga4InsightsService.listChannelGroups(pid, dimension);
            setLandingChannelGroups(res.groups || []);
        } catch (err) {
            setLandingError(err.message || t('Failed to load channel groups.', '載入自訂分組失敗。'));
        } finally {
            setLandingChannelGroupsLoading(false);
        }
    };

    const loadLandingChannelGroupRules = async (pid, dimension) => {
        if (!pid || !dimension) {
            setLandingChannelGroupRules([]);
            return;
        }
        setLandingChannelGroupRulesLoading(true);
        setLandingChannelGroupRulesError('');
        try {
            const res = await ga4InsightsService.listChannelGroupRules(pid, dimension);
            setLandingChannelGroupRules(res.rules || []);
        } catch (err) {
            setLandingChannelGroupRulesError(err.message || t('Failed to load channel group rules.', '載入渠道分組規則失敗。'));
        } finally {
            setLandingChannelGroupRulesLoading(false);
        }
    };

    const handleCreateChannelGroupRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !landingChannelDimension || !landingChannelGroupRuleForm.group_label.trim() || !landingChannelGroupRuleForm.pattern.trim()) return;
        setLandingChannelGroupRuleSaving(true);
        setLandingChannelGroupRulesError('');
        try {
            await ga4InsightsService.upsertChannelGroupRule({
                property_id: propertyId,
                channel_dimension: landingChannelDimension,
                group_label: landingChannelGroupRuleForm.group_label.trim(),
                match_type: landingChannelGroupRuleForm.match_type,
                pattern: landingChannelGroupRuleForm.pattern.trim(),
                priority: Number(landingChannelGroupRuleForm.priority) || 0,
            });
            setLandingChannelGroupRuleForm((prev) => ({ ...prev, group_label: '', pattern: '' }));
            await loadLandingChannelGroupRules(propertyId, landingChannelDimension);
            await loadLandingChannelGroups(propertyId, landingChannelDimension);
        } catch (err) {
            setLandingChannelGroupRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setLandingChannelGroupRuleSaving(false);
        }
    };

    const handleDeleteChannelGroupRule = async (ruleId) => {
        if (!window.confirm(t('Delete this channel group rule?', '要刪除此渠道分組規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteChannelGroupRule(ruleId);
            await loadLandingChannelGroupRules(propertyId, landingChannelDimension);
            await loadLandingChannelGroups(propertyId, landingChannelDimension);
        } catch (err) {
            setLandingChannelGroupRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const loadLandingPageRules = async (pid) => {
        if (!pid) return;
        setLandingRulesLoading(true);
        setLandingRulesError('');
        try {
            const res = await ga4InsightsService.listLandingPageRules(pid);
            setLandingRules(res.rules || []);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to load landing page rules.', '載入到達頁分類規則失敗。'));
        } finally {
            setLandingRulesLoading(false);
        }
    };

    const handleCreateLandingPageRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !landingRuleForm.pattern.trim()) return;
        setLandingRuleSaving(true);
        setLandingRulesError('');
        try {
            await ga4InsightsService.upsertLandingPageRule({
                property_id: propertyId,
                category: landingRuleForm.category,
                match_type: landingRuleForm.match_type,
                pattern: landingRuleForm.pattern.trim(),
                priority: Number(landingRuleForm.priority) || 0,
            });
            setLandingRuleForm((prev) => ({ ...prev, pattern: '' }));
            await loadLandingPageRules(propertyId);
            await loadLandingPages(propertyId, landingDays);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setLandingRuleSaving(false);
        }
    };

    const handleDeleteLandingPageRule = async (ruleId) => {
        if (!window.confirm(t('Delete this classification rule?', '要刪除此分類規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteLandingPageRule(ruleId);
            await loadLandingPageRules(propertyId);
            await loadLandingPages(propertyId, landingDays);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    // 懶載入：每個分頁只在首次進入時抓一次。判斷條件（沒有快照/沒有規則）
    // 原本寫在父層的 useEffect 裡，收進來讓父層不需要知道細節。
    const ensureLoaded = (pid) => {
        if (!pid) return;
        if (!landingSnapshot) loadLandingPages(pid, landingDays);
        if (!landingRules) loadLandingPageRules(pid);
    };

    // 切換 GA4 屬性時清掉這個分頁的資料與篩選。刻意做成明確呼叫、不是
    // watch propertyId 自己重設，避免 effect 觸發順序跟父層的 load() 交錯。
    const reset = () => {
        setLandingSnapshot(null);
        setLandingRules(null);
        setLandingCategoryFilter('all');
        setLandingKeyEvent('');
        setLandingCompareEnabled(false);
    };

    return {
        landingDays, setLandingDays,
        landingSnapshot, landingLoading, landingError,
        landingCategoryFilter, setLandingCategoryFilter,
        landingKeyEvent, setLandingKeyEvent,
        landingCompareEnabled, setLandingCompareEnabled,
        landingChannelDimension, setLandingChannelDimension,
        landingChannelValue, setLandingChannelValue,
        landingChannelValues, landingChannelValuesLoading,
        landingChannelGroup, setLandingChannelGroup,
        landingChannelGroups, landingChannelGroupsLoading,
        landingChannelGroupRulesOpen, setLandingChannelGroupRulesOpen,
        landingChannelGroupRules, landingChannelGroupRulesLoading, landingChannelGroupRulesError,
        landingChannelGroupRuleForm, setLandingChannelGroupRuleForm,
        landingChannelGroupRuleSaving,
        landingRules, landingRulesOpen, setLandingRulesOpen,
        landingRulesLoading, landingRulesError,
        landingRuleForm, setLandingRuleForm, landingRuleSaving,
        loadLandingPages,
        loadLandingChannelValues,
        loadLandingChannelGroups,
        loadLandingChannelGroupRules,
        handleCreateChannelGroupRule,
        handleDeleteChannelGroupRule,
        handleCreateLandingPageRule,
        handleDeleteLandingPageRule,
        ensureLoaded,
        reset,
    };
};

export default useGA4LandingPagesTab;
