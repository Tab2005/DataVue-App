import React, { useMemo } from 'react';

import AiInsightsCard from './ContributionAiInsights';
import { ContributionChart, ContributionTable, MarginalChart } from './ContributionCharts';
import DiagnosticsPanel from './ContributionDiagnostics';
import { Section, t } from './ContributionShared';

const AnalysisView = ({ language, isMobile, snapshot, groups, reportedByGroup, marginalCurrency, accountName, onAiSummarySaved }) => {
    const results = snapshot?.results || null;
    const diagnostics = snapshot?.diagnostics || null;

    // docs/27 任務 4.1：歷史快照應以「分析當時的分組」渲染，不是頁面目前的
    // groups state——使用者改組後點開舊快照，用當前 groups 對不上會顯示 0
    // 或缺組。snapshot.config.group_snapshot 是 create_analysis 當下寫入的
    // 分組快照（service._group_to_dict，形狀與 groups state 相同：
    // group_key/group_name/campaign_ids/source）；理論上自任務 1.4 起每筆
    // snapshot 都會有此欄位，缺欄位時仍安全退回目前 groups。
    const effectiveGroups = snapshot?.config?.group_snapshot ?? groups;

    const rows = useMemo(() => {
        if (!results || !effectiveGroups.length) return [];
        const warnings = diagnostics?.collinearity_warnings || [];
        const correlatedPairs = new Set();
        warnings.forEach((w) => {
            correlatedPairs.add(w.group_a);
            correlatedPairs.add(w.group_b);
        });
        const groupsData = results.groups || {};
        return effectiveGroups.map((g) => {
            const data = groupsData[g.group_key] || {};
            const median = data.contribution_share?.median ?? 0;
            const doubtful = median <= 0.005 && correlatedPairs.has(g.group_key);
            return {
                groupKey: g.group_key,
                label: `${g.group_key} · ${g.group_name}`,
                spendShare: data.spend_share,
                reportedShare: reportedByGroup[g.group_key] || 0,
                contributionShare: data.contribution_share,
                marginalPerStep: data.marginal?.per_step,
                // docs/27 任務 4.3：邊際步長是各組依自己日均花費各自計算的
                // （engine.resolve_marginal_step），不是全帳戶統一的單一值。
                // 每列需帶自己的 step 才能正確標示「+N 元」。
                marginalStepValue: data.marginal?.step ?? null,
                doubtful,
            };
        });
    }, [results, effectiveGroups, diagnostics, reportedByGroup]);

    if (snapshot?.status !== 'completed' || !results) {
        return null;
    }

    return (
        <div style={{ display: 'grid', gap: '16px' }}>
            <Section
                title={t(language, 'Contribution Comparison', '貢獻對比')}
                subtitle={t(
                    language,
                    'Spend share vs. platform-reported share vs. MMM contribution. Doubtful groups are grayed out.',
                    '花費占比 vs 自報占比 vs MMM 貢獻。標「存疑」的組別以灰階呈現。'
                )}
            >
                <ContributionChart language={language} rows={rows} isMobile={isMobile} />
                <ContributionTable
                    language={language}
                    rows={rows}
                    marginalCurrency={marginalCurrency}
                />
            </Section>

            <Section
                title={t(language, 'Marginal ROI Ranking', '邊際報酬排序')}
                subtitle={t(
                    language,
                    'Higher = more incremental conversions per +100 spend at the current spend level (normalized across groups).',
                    '數值越高代表在目前花費水位附近，每 +100 元帶來的增量轉換越多（已跨組正規化）。'
                )}
            >
                <MarginalChart
                    language={language}
                    rows={rows}
                    marginalCurrency={marginalCurrency}
                    isMobile={isMobile}
                />
            </Section>

            <DiagnosticsPanel
                language={language}
                diagnostics={diagnostics}
                r2={results.r2}
                baseShare={results.base_share}
                dataSummary={diagnostics?.data_summary}
            />

            <AiInsightsCard
                language={language}
                snapshot={snapshot}
                groups={effectiveGroups}
                reportedByGroup={reportedByGroup}
                accountName={accountName}
                onAiSummarySaved={onAiSummarySaved}
            />
        </div>
    );
};

export default AnalysisView;
