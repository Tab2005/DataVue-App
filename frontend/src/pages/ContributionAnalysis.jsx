import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';

import { useModuleAccess } from '../hooks/usePermission';
import {
    createAnalysis,
    fetchDataCoverage,
    getAnalysis,
    getGroups,
    listAnalyses,
    listCampaignSummaries,
    refreshContributionData,
    resetGroups,
    updateGroups,
} from '../services/contributionService';
import {
    AccountAndPeriod,
    AnalysisView,
    ErrorPanel,
    GroupEditor,
    HistoryList,
    InfoPanel,
    Section,
    VIZ_TOKENS,
    computePeriod,
    t,
} from '../components/Contribution/ContributionAnalysisComponents';

const DEFAULT_PERIOD_DAYS = 180;
const POLL_INTERVAL_MS = 2000;
// docs/27 任務 4.5：全量 180 天背景抓取遠不止 1.5 秒，改為輪詢快取活動數
// 直到穩定或逾時，取代固定等待後假裝抓完的舊行為。
const REFRESH_POLL_INTERVAL_MS = 3000;
const REFRESH_POLL_TIMEOUT_MS = 60000;

// 純函數：依「本次活動數 / 刷新前基準值 / 上次輪詢的活動數 / 已過時間」決定
// 這次輪詢是否該停止，及停止原因。抽成獨立函式以便脫離 setInterval/計時器
// 直接單元測試（docs/27 任務 4.5）。
// reason: 'increased'（活動數比基準值高，代表已有新資料）
//       | 'stabilized'（連續兩次不變且 > 0，視為已抓完並穩定）
//       | 'timeout'（逾時仍未穩定，提示使用者稍後手動重新整理）
//       | null（尚未達停止條件，continue polling）
// eslint-disable-next-line react-refresh/only-export-components
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

const useAdAccountList = (teamId) => {
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

const ContributionAnalysis = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('contribution', selectedTeamId);
    const { accounts, loading: loadingAccounts } = useAdAccountList(selectedTeamId);

    const [accountId, setAccountId] = useState('');
    const [periodDays, setPeriodDays] = useState(DEFAULT_PERIOD_DAYS);
    const [campaigns, setCampaigns] = useState([]);
    const [groups, setGroups] = useState([]);
    const [editingGroups, setEditingGroups] = useState(null);
    const [savingGroups, setSavingGroups] = useState(false);
    const [groupSaveError, setGroupSaveError] = useState(null);
    const [resettingGroups, setResettingGroups] = useState(false);
    const [groupResetError, setGroupResetError] = useState(null);
    const [dataCoverage, setDataCoverage] = useState(null);
    const [refreshing, setRefreshing] = useState(false);
    const [refreshingError, setRefreshingError] = useState(null);
    const [refreshNotice, setRefreshNotice] = useState(null);
    const refreshPollRef = useRef(null);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    const [activeSnapshot, setActiveSnapshot] = useState(null);
    const [polling, setPolling] = useState(false);
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [pageError, setPageError] = useState(null);
    const pollRef = useRef(null);

    // 預設選單一帳戶
    useEffect(() => {
        if (!accountId && accounts.length === 1) {
            setAccountId(accounts[0].id);
        }
    }, [accounts, accountId]);

    const loadCampaigns = useCallback(async (acct) => {
        if (!acct) {
            setCampaigns([]);
            return;
        }
        try {
            const res = await listCampaignSummaries({ accountId: acct });
            setCampaigns(res.campaigns || []);
        } catch (err) {
            console.error('listCampaignSummaries failed', err);
            setCampaigns([]);
        }
    }, []);

    const loadGroups = useCallback(async (acct) => {
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
    }, []);

    const loadDataCoverage = useCallback(async (acct) => {
        if (!acct) {
            setDataCoverage(null);
            return;
        }
        try {
            const res = await fetchDataCoverage({ accountId: acct });
            setDataCoverage(res);
        } catch (err) {
            console.error('fetchDataCoverage failed', err);
            setDataCoverage(null);
        }
    }, []);

    const loadHistory = useCallback(async (acct) => {
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
    }, []);

    useEffect(() => {
        // docs/27 任務 4.5：切換帳戶時清掉尚在進行的「抓取資料」輪詢，避免
        // 舊帳戶的輪詢殘留繼續跑並把結果寫進新帳戶的畫面狀態。
        if (refreshPollRef.current) {
            clearInterval(refreshPollRef.current);
            refreshPollRef.current = null;
        }
        setRefreshing(false);
        setRefreshingError(null);
        setRefreshNotice(null);

        if (!accountId) {
            setActiveSnapshot(null);
            return;
        }
        loadCampaigns(accountId);
        loadGroups(accountId);
        loadHistory(accountId);
        loadDataCoverage(accountId);
    }, [accountId, loadCampaigns, loadGroups, loadHistory, loadDataCoverage]);

    // 輪詢 active snapshot
    useEffect(() => {
        if (!activeSnapshot || activeSnapshot.status === 'completed' || activeSnapshot.status === 'failed') {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
            setPolling(false);
            return;
        }
        setPolling(true);
        pollRef.current = setInterval(async () => {
            try {
                const next = await getAnalysis(activeSnapshot.snapshot_id);
                setActiveSnapshot(next);
                if (next.status === 'completed' || next.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setPolling(false);
                    if (next.status === 'completed') {
                        loadHistory(accountId);
                    }
                }
            } catch (err) {
                console.error('poll getAnalysis failed', err);
            }
        }, POLL_INTERVAL_MS);
        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        };
    }, [activeSnapshot, accountId, loadHistory]);

    useEffect(() => () => {
        if (pollRef.current) clearInterval(pollRef.current);
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

        // docs/27 任務 4.5：全量 180 天背景抓取遠不止 1.5 秒；固定等待後就
        // 假裝抓完會讓首次使用者看到仍是 0 筆而困惑。改為輪詢快取活動數，
        // 直到「活動數增加」或「連續兩次不變且 > 0」（視為已抓完並穩定）
        // 才停止；60 秒逾時仍未穩定則提示使用者稍後手動重新整理，按鈕在
        // 整個輪詢期間維持「抓取中…」。
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
            await loadHistory(accountId);
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

    // docs/27 任務 4.2：自報占比改用快照區間，而非 campaigns 的全歷史彙總。
    // MMM 貢獻只涵蓋 activeSnapshot 的分析區間，若自報占比用全歷史彙總，
    // 90 天分析配 180 天自報占比時兩者對照本身失真（且會餵進 AI payload
    // 誤導「高估/低估」判斷）。`campaigns`（全歷史）仍保留給分組編輯器與
    // 「快取活動數」提示使用（職責不同，見 loadCampaigns）。
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
        // eslint-disable-next-line react-hooks/exhaustive-deps
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

    // docs/27 任務 4.3：舊版在此取「第一組」的 step 當全域顯示值——但每組
    // step 依各自日均花費各自計算，用第一組代表全部在花費量級差異大的帳戶
    // 上會顯示錯誤數字。步長改為在 AnalysisView 內逐列使用該組自己的
    // marginal.step（見 rows 的 marginalStepValue），此處不再需要單一值。
    const marginalCurrency = ''; // 未來可由帳戶 metadata 取得

    // 由目前選擇的 accountId 找對應帳戶名稱（傳入 AI 解讀卡當 context 開頭）
    const accountName = useMemo(() => {
        if (!accountId) return null;
        const match = accounts.find((a) => a.id === accountId);
        return match?.name || null;
    }, [accountId, accounts]);

    // AI 解讀卡持久化完成 → 更新 activeSnapshot，使再次進入頁面時仍可見解讀
    const handleAiSummarySaved = useCallback((saved) => {
        setActiveSnapshot((prev) => {
            if (!prev || prev.snapshot_id !== saved.snapshot_id) return prev;
            return {
                ...prev,
                ai_summary: saved.ai_summary,
                ai_summary_generated_at: saved.ai_summary_generated_at,
            };
        });
        // 同步歷史列表的 has_ai_summary 狀態
        setHistory((prev) =>
            prev.map((row) =>
                row.snapshot_id === saved.snapshot_id
                    ? { ...row, has_ai_summary: true }
                    : row
            )
        );
    }, []);

    if (accessLoading) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <Section title={t(language, 'Contribution Analysis', '貢獻分析')}>
                    <InfoPanel message={t(language, 'Checking workspace access…', '正在確認工作區模組權限…')} />
                </Section>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <Section title={t(language, 'Contribution Analysis', '貢獻分析')}>
                    <InfoPanel
                        message={t(
                            language,
                            'You do not have access to Contribution Analysis in this workspace.',
                            '此工作區無「貢獻分析」模組存取權限，請聯絡管理員開通。'
                        )}
                        tone="info"
                    />
                </Section>
            </div>
        );
    }

    const canSubmit = Boolean(accountId) && (groups.length > 0 || editingGroups);

    return (
        <>
            <style>{VIZ_TOKENS}</style>
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div
                style={{
                    marginBottom: '20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: isMobile ? 'flex-start' : 'center',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '12px',
                }}
            >
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        {t(language, 'Contribution Analysis', '貢獻分析')}
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t(language, 'MMM Contribution Explorer', 'MMM 活動貢獻分析')}
                    </h1>
                </div>
            </div>

            {pageError && <ErrorPanel message={pageError} />}
            {submitError && <ErrorPanel message={submitError} />}

            <div style={{ display: 'grid', gap: '16px' }}>
                <AccountAndPeriod
                    language={language}
                    isMobile={isMobile}
                    accountId={accountId}
                    onAccountChange={(v) => {
                        setActiveSnapshot(null);
                        setAccountId(v);
                    }}
                    onRefreshCampaigns={handleRefreshData}
                    refreshing={refreshing}
                    campaignsCount={campaigns.length}
                    periodDays={periodDays}
                    onPeriodChange={setPeriodDays}
                    onSubmit={handleSubmitAnalysis}
                    submitting={submitting || polling}
                    canSubmit={canSubmit}
                    accountList={accounts}
                    loadingAccounts={loadingAccounts}
                    dataCoverage={dataCoverage}
                />

                {refreshingError && <ErrorPanel message={refreshingError} />}
                {refreshNotice && (
                    <InfoPanel message={refreshNotice.message} tone={refreshNotice.tone} />
                )}

                {!accountId && (
                    <InfoPanel
                        message={t(
                            language,
                            'Select an ad account to start.',
                            '請選擇一個廣告帳戶開始使用。'
                        )}
                    />
                )}

                {accountId && campaigns.length === 0 && (
                    <InfoPanel
                        message={t(
                            language,
                            'No cached campaigns for this account. Click "Refresh Data" to fetch from Meta.',
                            '此帳戶快取中尚無活動資料，請按「抓取資料」從 Meta 拉取。'
                        )}
                    />
                )}

                {accountId && (
                    <GroupEditor
                        language={language}
                        campaigns={campaigns}
                        groups={groups}
                        editing={editingGroups}
                        onEdit={handleEditGroups}
                        onCancel={handleCancelEdit}
                        onSave={handleSaveGroups}
                        saving={savingGroups}
                        saveError={groupSaveError}
                        onReset={handleResetGroups}
                        resetting={resettingGroups}
                        resetError={groupResetError}
                    />
                )}

                {activeSnapshot && (
                    <Section
                        title={t(language, 'Latest Analysis', '最新分析')}
                        subtitle={
                            activeSnapshot.status === 'completed'
                                ? t(language, `Period: ${activeSnapshot.date_start} ~ ${activeSnapshot.date_end}`, `區間：${activeSnapshot.date_start} ~ ${activeSnapshot.date_end}`)
                                : t(language, `Snapshot ${activeSnapshot.snapshot_id} · ${activeSnapshot.status}`, `快照 ${activeSnapshot.snapshot_id} · ${activeSnapshot.status}`)
                        }
                    >
                        {activeSnapshot.status === 'failed' && (
                            <ErrorPanel message={activeSnapshot.error_message || '分析失敗'} />
                        )}
                        {(activeSnapshot.status === 'queued' || activeSnapshot.status === 'processing') && (
                            <InfoPanel message={t(language, 'Analysis is running, please wait…', '分析執行中，請稍候…')} />
                        )}
                        <AnalysisView
                            language={language}
                            isMobile={isMobile}
                            snapshot={activeSnapshot}
                            groups={groups}
                            reportedByGroup={reportedByGroup}
                            marginalCurrency={marginalCurrency}
                            accountName={accountName}
                            onAiSummarySaved={handleAiSummarySaved}
                        />
                    </Section>
                )}

                {accountId && (
                    <HistoryList
                        language={language}
                        history={history}
                        loading={loadingHistory}
                        onSelect={handleSelectSnapshot}
                        onRefresh={() => loadHistory(accountId)}
                        selectedId={activeSnapshot?.snapshot_id}
                        isMobile={isMobile}
                    />
                )}
            </div>
        </div>
        </>
    );
};

export default ContributionAnalysis;
