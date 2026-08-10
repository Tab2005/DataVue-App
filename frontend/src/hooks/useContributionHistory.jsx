// frontend/src/hooks/useContributionHistory.jsx (docs/33 第 7 波：ContributionAnalysis.jsx 組合層瘦身)
import { useState } from 'react';

import { listAnalyses } from '../services/contributionService';

export const useContributionHistory = () => {
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const loadHistory = async (acct) => {
        if (!acct) {
            setHistory([]);
            return;
        }
        setLoadingHistory(true);
        try {
            const res = await listAnalyses({ accountId: acct, page: 1, pageSize: 20 });
            setHistory(res.analyses || []);
        } catch (err) {
            console.error('listAnalyses failed', err);
            setHistory([]);
        } finally {
            setLoadingHistory(false);
        }
    };

    // AI 解讀卡持久化完成後，同步歷史列表的 has_ai_summary 狀態。
    const markHasAiSummary = (snapshotId) => {
        setHistory((prev) =>
            prev.map((row) =>
                row.snapshot_id === snapshotId
                    ? { ...row, has_ai_summary: true }
                    : row
            )
        );
    };

    return {
        history, loadingHistory,
        loadHistory,
        markHasAiSummary,
    };
};

export default useContributionHistory;
