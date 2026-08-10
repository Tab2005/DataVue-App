// frontend/src/hooks/useContributionGroups.jsx (docs/33 第 7 波：ContributionAnalysis.jsx 組合層瘦身)
import { useState } from 'react';

import { getGroups, resetGroups, updateGroups } from '../services/contributionService';
import { t } from '../components/Contribution/ContributionAnalysisComponents';

export const useContributionGroups = ({ accountId, language }) => {
    const [groups, setGroups] = useState([]);
    const [editingGroups, setEditingGroups] = useState(null);
    const [savingGroups, setSavingGroups] = useState(false);
    const [groupSaveError, setGroupSaveError] = useState(null);
    const [resettingGroups, setResettingGroups] = useState(false);
    const [groupResetError, setGroupResetError] = useState(null);

    const loadGroups = async (acct) => {
        if (!acct) {
            setGroups([]);
            return;
        }
        try {
            const res = await getGroups({ accountId: acct });
            setGroups(res.groups || []);
        } catch (err) {
            console.error('getGroups failed', err);
            setGroups([]);
        }
    };

    const handleEditGroups = (next) => {
        setGroupSaveError(null);
        setEditingGroups(next);
    };

    const handleCancelEdit = () => {
        setEditingGroups(null);
        setGroupSaveError(null);
    };

    const handleSaveGroups = async () => {
        if (!editingGroups || !accountId) return;
        setSavingGroups(true);
        setGroupSaveError(null);
        try {
            // docs/27 任務 4.4：把某組活動全搬走後，該組會變成空的
            // campaign_ids；後端 validate_manual_groups 對空組回 422
            // 「campaign_ids 不可為空」，但編輯器本身沒有刪組功能，使用者
            // 會卡在無法儲存也無法移除的狀態。送出前直接過濾掉空組——
            // 完整性檢查（活動不遺失）仍由後端 validate_manual_groups 把關。
            const nonEmptyGroups = editingGroups.filter(
                (g) => (g.campaign_ids || []).length > 0
            );
            await updateGroups({ accountId, groups: nonEmptyGroups });
            await loadGroups(accountId);
            setEditingGroups(null);
        } catch (err) {
            setGroupSaveError(err.message);
        } finally {
            setSavingGroups(false);
        }
    };

    // 直接掛在 <button onClick={onReset}>（見 GroupEditor.jsx），不吃函式參數
    // （沿用原本 ContributionAnalysis.jsx 的寫法）。
    const handleResetGroups = async () => {
        if (!accountId) return;
        const confirmed = window.confirm(
            t(
                language,
                'This clears the current groups (including any manual edits) and regenerates them with the latest auto-grouping rules. Continue?',
                '此操作將清除目前分組（含任何手動編輯），並以最新的自動分組規則重新產生，確定要繼續嗎？'
            )
        );
        if (!confirmed) return;
        setResettingGroups(true);
        setGroupResetError(null);
        try {
            const res = await resetGroups({ accountId });
            setGroups(res.groups || []);
            setEditingGroups(null);
        } catch (err) {
            setGroupResetError(err.message);
        } finally {
            setResettingGroups(false);
        }
    };

    return {
        groups, editingGroups, savingGroups, groupSaveError,
        resettingGroups, groupResetError,
        loadGroups,
        handleEditGroups,
        handleCancelEdit,
        handleSaveGroups,
        handleResetGroups,
    };
};

export default useContributionGroups;
