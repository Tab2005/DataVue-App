import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';

import { useModuleAccess } from '../hooks/usePermission';
import {
    fetchDataCoverage,
    listCampaignSummaries,
} from '../services/contributionService';
import useAdAccountList from '../hooks/useAdAccountList';
import useContributionDataRefresh, { evaluateRefreshPoll } from '../hooks/useContributionDataRefresh';
import useContributionGroups from '../hooks/useContributionGroups';
import useContributionHistory from '../hooks/useContributionHistory';
import useContributionAnalysisSnapshot from '../hooks/useContributionAnalysisSnapshot';
import {
    AccountAndPeriod,
    AnalysisView,
    ErrorPanel,
    GroupEditor,
    HistoryList,
    InfoPanel,
    Section,
    VIZ_TOKENS,
    t,
} from '../components/Contribution/ContributionAnalysisComponents';

// docs/27 任務 4.5 的輪詢停止條件判斷（evaluateRefreshPoll）已搬到
// useContributionDataRefresh.jsx；這裡重新 export 是為了讓既有測試
// （import { evaluateRefreshPoll } from '../ContributionAnalysis'）不用改路徑。
// eslint-disable-next-line react-refresh/only-export-components
export { evaluateRefreshPoll };

const DEFAULT_PERIOD_DAYS = 180;

const ContributionAnalysis = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('contribution', selectedTeamId);
    const { accounts, loading: loadingAccounts } = useAdAccountList(selectedTeamId);

    const [accountId, setAccountId] = useState('');
    const [periodDays, setPeriodDays] = useState(DEFAULT_PERIOD_DAYS);
    const [campaigns, setCampaigns] = useState([]);
    const [dataCoverage, setDataCoverage] = useState(null);

    // docs/33 第 7 波：帳戶/週期以外的每個關注點（分組編輯、歷史列表、分析
    // 快照+自報占比、抓取資料輪詢）各自抽成獨立 hook（原本全部內嵌在本檔）。
    const groupsHook = useContributionGroups({ accountId, language });
    const { groups, loadGroups } = groupsHook;
    const historyHook = useContributionHistory();
    const { loadHistory } = historyHook;

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

    const analysisHook = useContributionAnalysisSnapshot({
        accountId, periodDays, groups,
        onCompleted: () => loadHistory(accountId),
    });
    const {
        submitting, submitError, activeSnapshot, polling, pageError: analysisError,
        reportedByGroup, handleSubmitAnalysis, handleSelectSnapshot, handleAiSummarySaved,
    } = analysisHook;

    const dataRefreshHook = useContributionDataRefresh({
        accountId, campaigns, setCampaigns, loadDataCoverage, language,
    });
    const { refreshing, refreshingError, refreshNotice, handleRefreshData } = dataRefreshHook;

    // 預設選單一帳戶
    useEffect(() => {
        if (!accountId && accounts.length === 1) {
            setAccountId(accounts[0].id);
        }
    }, [accounts, accountId]);

    useEffect(() => {
        dataRefreshHook.resetOnAccountChange();

        if (!accountId) {
            analysisHook.resetOnAccountChange();
            return;
        }
        loadCampaigns(accountId);
        loadGroups(accountId);
        loadHistory(accountId);
        loadDataCoverage(accountId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountId]);

    // 由目前選擇的 accountId 找對應帳戶名稱（傳入 AI 解讀卡當 context 開頭）
    const accountName = useMemo(() => {
        if (!accountId) return null;
        const match = accounts.find((a) => a.id === accountId);
        return match?.name || null;
    }, [accountId, accounts]);

    // docs/27 任務 4.3：舊版在此取「第一組」的 step 當全域顯示值——但每組
    // step 依各自日均花費各自計算，用第一組代表全部在花費量級差異大的帳戶
    // 上會顯示錯誤數字。步長改為在 AnalysisView 內逐列使用該組自己的
    // marginal.step（見 rows 的 marginalStepValue），此處不再需要單一值。
    const marginalCurrency = ''; // 未來可由帳戶 metadata 取得

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

    const canSubmit = Boolean(accountId) && (groups.length > 0 || groupsHook.editingGroups);

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

            {analysisError && <ErrorPanel message={analysisError} />}
            {submitError && <ErrorPanel message={submitError} />}

            <div style={{ display: 'grid', gap: '16px' }}>
                <AccountAndPeriod
                    language={language}
                    isMobile={isMobile}
                    accountId={accountId}
                    onAccountChange={(v) => {
                        analysisHook.resetOnAccountChange();
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
                        editing={groupsHook.editingGroups}
                        onEdit={groupsHook.handleEditGroups}
                        onCancel={groupsHook.handleCancelEdit}
                        onSave={groupsHook.handleSaveGroups}
                        saving={groupsHook.savingGroups}
                        saveError={groupsHook.groupSaveError}
                        onReset={groupsHook.handleResetGroups}
                        resetting={groupsHook.resettingGroups}
                        resetError={groupsHook.groupResetError}
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
                            onAiSummarySaved={(saved) => handleAiSummarySaved(saved, historyHook.markHasAiSummary)}
                        />
                    </Section>
                )}

                {accountId && (
                    <HistoryList
                        language={language}
                        history={historyHook.history}
                        loading={historyHook.loadingHistory}
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
