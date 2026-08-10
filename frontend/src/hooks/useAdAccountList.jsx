// frontend/src/hooks/useAdAccountList.jsx (docs/33 第 7 波：ContributionAnalysis.jsx 組合層瘦身)
//
// 原本內嵌在 ContributionAnalysis.jsx 頂部，邏輯本身已完全自足，單純搬出。
import { useEffect, useState } from 'react';

export const useAdAccountList = (teamId) => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            setLoading(true);
            try {
                const mod = await import('../services/teamService');
                const res = await mod.TeamService.getAllAdAccounts(teamId);
                if (cancelled) return;
                setAccounts(res || []);
            } catch (err) {
                if (cancelled) return;
                setError(err.message || '載入帳戶失敗');
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => {
            cancelled = true;
        };
    }, [teamId]);
    return { accounts, loading, error };
};

export default useAdAccountList;
