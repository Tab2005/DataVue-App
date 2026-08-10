// frontend/src/components/Analytics/analyticsAiPayload.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// docs/58：AI 廣告分析卡片的 payload——只送使用者實際勾選的指標
// （activeCols），rows 用 sortedData（跟畫面排序一致，不是 filteredData）
// 取前 20 筆，summary 從既有的 currentSummaryData 篩出勾選的指標。
export const buildAnalyticsAiPayload = ({
    sortedData, activeCols, language, currentSummaryData,
    selectedAccountId, selectedTeamId, level, dateRange,
}) => {
    if (!sortedData || sortedData.length === 0 || activeCols.length === 0) return null;

    const selected_metrics = activeCols.map((col) => ({
        key: col.key,
        label: language === 'zh' ? col.label_zh : col.label_en,
        format: col.format,
    }));

    const summary = {};
    selected_metrics.forEach((m) => {
        if (currentSummaryData && currentSummaryData[m.key] !== undefined) {
            summary[m.key] = currentSummaryData[m.key];
        }
    });

    const rows = sortedData.slice(0, 20).map((row) => {
        const r = { name: row.name };
        selected_metrics.forEach((m) => { r[m.key] = row[m.key]; });
        return r;
    });

    return {
        accountId: selectedAccountId,
        teamId: selectedTeamId,
        level,
        dateSince: dateRange.since,
        dateUntil: dateRange.until,
        payload: {
            selected_metrics,
            summary,
            rows,
            level,
            date_since: dateRange.since,
            date_until: dateRange.until,
        },
    };
};

export default buildAnalyticsAiPayload;
