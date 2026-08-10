// frontend/src/hooks/useContributionAnalysisSnapshot.jsx (docs/33 第 7 波：ContributionAnalysis.jsx 組合層瘦身)
//
// 分析快照的建立/輪詢/選取，以及自報占比（docs/27 任務 4.2）。這兩者綁在
// 同一個 hook 是因為 reportedByGroup 依賴 activeSnapshot 的區間與分組快照
// （group_snapshot），拆開反而要多一層跨 hook 資料傳遞。
import { useEffect, useMemo, useState } from 'react';

import { createAnalysis, getAnalysis, listCampaignSummaries } from '../services/contributionService';
import { computePeriod } from '../components/Contribution/ContributionAnalysisComponents';

const POLL_INTERVAL_MS = 2000;

export const useContributionAnalysisSnapshot = ({ accountId, periodDays, groups, onCompleted }) => {
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    const [activeSnapshot, setActiveSnapshot] = useState(null);
    const [polling, setPolling] = useState(false);
    const [pageError, setPageError] = useState(null);

    // 輪詢 active snapshot
    useEffect(() => {
        if (!activeSnapshot || activeSnapshot.status === 'completed' || activeSnapshot.status === 'failed') {
            setPolling(false);
            return;
        }
        setPolling(true);
        const pollId = setInterval(async () => {
            try {
                const next = await getAnalysis(activeSnapshot.snapshot_id);
                setActiveSnapshot(next);
                if (next.status === 'completed' || next.status === 'failed') {
                    clearInterval(pollId);
                    setPolling(false);
                    if (next.status === 'completed' && onCompleted) {
                        onCompleted();
                    }
                }
            } catch (err) {
                console.error('poll getAnalysis failed', err);
            }
        }, POLL_INTERVAL_MS);
        return () => clearInterval(pollId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeSnapshot]);

    // docs/27 任務 4.2：自報占比改用快照區間，而非 campaigns 的全歷史彙總。
    // MMM 貢獻只涵蓋 activeSnapshot 的分析區間，若自報占比用全歷史彙總，
    // 90 天分析配 180 天自報占比時兩者對照本身失真（且會餵進 AI payload
    // 誤導「高估/低估」判斷）。
    const [snapshotCampaigns, setSnapshotCampaigns] = useState([]);

    useEffect(() => {
        if (!accountId || !activeSnapshot?.date_start || !activeSnapshot?.date_end) {
            setSnapshotCampaigns([]);
            return;
        }
        let cancelled = false;
        listCampaignSummaries({
            accountId,
            dateStart: activeSnapshot.date_start,
            dateEnd: activeSnapshot.date_end,
        })
            .then((res) => {
                if (cancelled) return;
                setSnapshotCampaigns(res.campaigns || []);
            })
            .catch((err) => {
                console.error('listCampaignSummaries (snapshot-scoped) failed', err);
                if (!cancelled) setSnapshotCampaigns([]);
            });
        return () => {
            cancelled = true;
        };
        // activeSnapshot 的其餘欄位（status 等）變動不需重查，只在
        // snapshot_id 或區間本身改變時重打
    }, [accountId, activeSnapshot?.snapshot_id, activeSnapshot?.date_start, activeSnapshot?.date_end]);

    const reportedByGroup = useMemo(() => {
        if (!snapshotCampaigns.length) return {};
        // 與任務 4.1 呼應：cid → group_key 的對應也應用「分析當時的分組」
        // （snapshot.config.group_snapshot），而非頁面目前的 groups state，
        // 否則自報占比的分組口徑會與 MMM 貢獻的分組口徑（已改用
        // group_snapshot）對不上。
        const effectiveGroups = activeSnapshot?.config?.group_snapshot ?? groups;
        const cidToGroup = new Map();
        effectiveGroups.forEach((g) => {
            (g.campaign_ids || []).forEach((cid) => cidToGroup.set(String(cid), g.group_key));
        });
        let totalConversions = 0;
        const groupConversions = {};
        snapshotCampaigns.forEach((c) => {
            const conv = Number(c.conversions || 0);
            const gk = cidToGroup.get(String(c.campaign_id));
            if (!gk) return;
            totalConversions += conv;
            groupConversions[gk] = (groupConversions[gk] || 0) + conv;
        });
        const out = {};
        if (totalConversions > 0) {
            Object.entries(groupConversions).forEach(([gk, conv]) => {
                out[gk] = conv / totalConversions;
            });
        }
        return out;
    }, [snapshotCampaigns, groups, activeSnapshot?.config]);

    const handleSubmitAnalysis = async () => {
        if (!accountId) return;
        setSubmitting(true);
        setSubmitError(null);
        setPageError(null);
        const { dateStart, dateEnd } = computePeriod(periodDays);
        try {
            const res = await createAnalysis({
                accountId,
                dateStart,
                dateEnd,
            });
            setActiveSnapshot({
                snapshot_id: res.snapshot_id,
                status: res.status,
                account_id: res.account_id,
                date_start: dateStart,
                date_end: dateEnd,
            });
            if (onCompleted) await onCompleted();
        } catch (err) {
            if (err.statusCode === 422) {
                setSubmitError(err.message);
            } else {
                setPageError(err.message || '分析啟動失敗');
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleSelectSnapshot = async (snapshotId) => {
        try {
            const next = await getAnalysis(snapshotId);
            setActiveSnapshot(next);
        } catch (err) {
            setPageError(err.message || '載入快照失敗');
        }
    };

    // AI 解讀卡持久化完成 → 更新 activeSnapshot，使再次進入頁面時仍可見解讀
    const handleAiSummarySaved = (saved, onHistorySynced) => {
        setActiveSnapshot((prev) => {
            if (!prev || prev.snapshot_id !== saved.snapshot_id) return prev;
            return {
                ...prev,
                ai_summary: saved.ai_summary,
                ai_summary_generated_at: saved.ai_summary_generated_at,
            };
        });
        if (onHistorySynced) onHistorySynced(saved.snapshot_id);
    };

    const resetOnAccountChange = () => {
        setActiveSnapshot(null);
    };

    return {
        submitting, submitError, activeSnapshot, polling, pageError, setPageError,
        reportedByGroup,
        handleSubmitAnalysis,
        handleSelectSnapshot,
        handleAiSummarySaved,
        resetOnAccountChange,
    };
};

export default useContributionAnalysisSnapshot;
