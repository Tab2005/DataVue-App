// frontend/src/hooks/useContributionDataRefresh.jsx (docs/33 第 7 波：ContributionAnalysis.jsx 組合層瘦身)
//
// 「抓取資料」輪詢（docs/27 任務 4.5）：全量 180 天背景抓取遠不止 1.5 秒，
// 改為輪詢快取活動數直到穩定或逾時，取代固定等待後假裝抓完的舊行為。
import { useEffect, useRef, useState } from 'react';

import { listCampaignSummaries, refreshContributionData } from '../services/contributionService';
import { t } from '../components/Contribution/ContributionAnalysisComponents';

const REFRESH_POLL_INTERVAL_MS = 3000;
const REFRESH_POLL_TIMEOUT_MS = 60000;

// 純函數：依「本次活動數 / 刷新前基準值 / 上次輪詢的活動數 / 已過時間」決定
// 這次輪詢是否該停止，及停止原因。抽成獨立函式以便脫離 setInterval/計時器
// 直接單元測試（docs/27 任務 4.5）。
// reason: 'increased'（活動數比基準值高，代表已有新資料）
//       | 'stabilized'（連續兩次不變且 > 0，視為已抓完並穩定）
//       | 'timeout'（逾時仍未穩定，提示使用者稍後手動重新整理）
//       | null（尚未達停止條件，continue polling）
export const evaluateRefreshPoll = ({ count, baselineCount, lastCount, elapsedMs, timeoutMs }) => {
    if (count > baselineCount) {
        return { stop: true, reason: 'increased' };
    }
    if (lastCount != null && count === lastCount && count > 0) {
        return { stop: true, reason: 'stabilized' };
    }
    if (elapsedMs >= timeoutMs) {
        return { stop: true, reason: 'timeout' };
    }
    return { stop: false, reason: null };
};

export const useContributionDataRefresh = ({ accountId, campaigns, setCampaigns, loadDataCoverage, language }) => {
    const [refreshing, setRefreshing] = useState(false);
    const [refreshingError, setRefreshingError] = useState(null);
    const [refreshNotice, setRefreshNotice] = useState(null);
    const refreshPollRef = useRef(null);

    // docs/27 任務 4.5：切換帳戶時清掉尚在進行的輪詢，避免舊帳戶的輪詢殘留
    // 繼續跑並把結果寫進新帳戶的畫面狀態。頁面層在 accountId 改變時呼叫。
    const resetOnAccountChange = () => {
        if (refreshPollRef.current) {
            clearInterval(refreshPollRef.current);
            refreshPollRef.current = null;
        }
        setRefreshing(false);
        setRefreshingError(null);
        setRefreshNotice(null);
    };

    useEffect(() => () => {
        if (refreshPollRef.current) clearInterval(refreshPollRef.current);
    }, []);

    const handleRefreshData = async () => {
        if (!accountId) return;
        const acct = accountId;
        setRefreshing(true);
        setRefreshingError(null);
        setRefreshNotice(null);
        if (refreshPollRef.current) {
            clearInterval(refreshPollRef.current);
            refreshPollRef.current = null;
        }

        try {
            await refreshContributionData({ accountId: acct });
        } catch (err) {
            setRefreshingError(err.message);
            setRefreshing(false);
            return;
        }

        const baselineCount = campaigns.length;
        let lastCount = null;
        let elapsedMs = 0;

        const stopPolling = () => {
            if (refreshPollRef.current) {
                clearInterval(refreshPollRef.current);
                refreshPollRef.current = null;
            }
            setRefreshing(false);
        };

        refreshPollRef.current = setInterval(async () => {
            elapsedMs += REFRESH_POLL_INTERVAL_MS;
            let count = lastCount ?? baselineCount;
            try {
                const res = await listCampaignSummaries({ accountId: acct });
                setCampaigns(res.campaigns || []);
                count = (res.campaigns || []).length;
            } catch (err) {
                console.error('listCampaignSummaries (refresh poll) failed', err);
            }

            const { stop, reason } = evaluateRefreshPoll({
                count,
                baselineCount,
                lastCount,
                elapsedMs,
                timeoutMs: REFRESH_POLL_TIMEOUT_MS,
            });
            if (stop) {
                stopPolling();
                loadDataCoverage(acct);
                setRefreshNotice(
                    reason === 'timeout'
                        ? {
                            tone: 'info',
                            message: t(
                                language,
                                'Refresh is still running in the background. Please try refreshing again later.',
                                '抓取仍在背景進行，稍後請按重新整理。'
                            ),
                        }
                        : {
                            tone: 'success',
                            message: t(language, 'Data refreshed.', '資料已抓取完成。'),
                        }
                );
                return;
            }
            lastCount = count;
        }, REFRESH_POLL_INTERVAL_MS);
    };

    return {
        refreshing, refreshingError, refreshNotice,
        handleRefreshData,
        resetOnAccountChange,
    };
};

export default useContributionDataRefresh;
