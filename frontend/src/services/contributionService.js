/**
 * 貢獻分析（MMM）API 服務層（docs/21 第 2 波 — 任務 2.1）
 *
 * 包裝 backend/modules/contribution/ 的端點：
 *   GET  /api/contribution/ping
 *   GET  /api/contribution/campaigns
 *   GET  /api/contribution/groups
 *   PUT  /api/contribution/groups
 *   POST /api/contribution/groups/reset
 *   POST /api/contribution/analyses
 *   GET  /api/contribution/analyses
 *   GET  /api/contribution/analyses/{id}
 *   POST /api/contribution/data/refresh
 *   GET  /api/contribution/data/coverage
 *
 * 422 / 503 等語意錯誤由後端拋 `detail = { errors: [...], missing?: [...] }`，
 * 此層將其攤平為 Error.message 內含逐行列點的訊息，避免頁面只能看到
 * `[object Object]` 或完整 JSON 雜訊。
 */
import apiClient, { ApiError } from './apiClient';

const BASE = '/api/contribution';

const buildQuery = (params) => {
    if (!params) return '';
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') return;
        search.append(key, String(value));
    });
    const qs = search.toString();
    return qs ? `?${qs}` : '';
};

const flattenDetail = (detail) => {
    if (detail == null) return null;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map(String).join('；');
    if (typeof detail === 'object') {
        const parts = [];
        if (Array.isArray(detail.errors) && detail.errors.length) {
            parts.push(detail.errors.map(String).join('；'));
        }
        if (Array.isArray(detail.missing) && detail.missing.length) {
            parts.push(`缺少活動：${detail.missing.join('、')}`);
        }
        if (typeof detail.message === 'string') parts.push(detail.message);
        if (!parts.length) {
            try { return JSON.stringify(detail); } catch { return String(detail); }
        }
        return parts.join('\n');
    }
    return String(detail);
};

const ensureStructured = (err, fallbackCode) => {
    if (err instanceof ApiError) {
        const flat = flattenDetail(err.message);
        if (flat && flat !== err.message) {
            const wrapped = new Error(flat);
            wrapped.statusCode = err.statusCode;
            wrapped.code = err.code || fallbackCode;
            wrapped.path = err.path;
            wrapped.original = err;
            return wrapped;
        }
    }
    return err;
};

export const pingContribution = async () => {
    return apiClient.get(`${BASE}/ping`);
};

export const listCampaignSummaries = async ({
    accountId,
    metricKey = 'omni_purchase',
    dateStart,
    dateEnd,
} = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({
        account_id: accountId,
        metric_key: metricKey,
        date_start: dateStart,
        date_end: dateEnd,
    });
    return apiClient.get(`${BASE}/campaigns${qs}`);
};

export const refreshContributionData = async ({ accountId, metricKey = 'omni_purchase' } = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({ account_id: accountId, metric_key: metricKey });
    return apiClient.post(`${BASE}/data/refresh${qs}`, undefined);
};

export const getGroups = async ({ accountId } = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({ account_id: accountId });
    return apiClient.get(`${BASE}/groups${qs}`);
};

export const updateGroups = async ({ accountId, groups }) => {
    if (!accountId) throw new Error('缺少 accountId');
    if (!Array.isArray(groups)) throw new Error('groups 必須為陣列');
    try {
        return await apiClient.put(`${BASE}/groups`, {
            account_id: accountId,
            groups: groups.map((g) => ({
                group_key: g.group_key,
                group_name: g.group_name,
                campaign_ids: Array.isArray(g.campaign_ids) ? g.campaign_ids : [],
                source: 'manual',
            })),
        });
    } catch (err) {
        throw ensureStructured(err, 'group_validation_rejected');
    }
};

export const resetGroups = async ({ accountId } = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({ account_id: accountId });
    try {
        return await apiClient.post(`${BASE}/groups/reset${qs}`, undefined);
    } catch (err) {
        throw ensureStructured(err, 'group_reset_failed');
    }
};

export const fetchDataCoverage = async ({ accountId, metricKey = 'omni_purchase' } = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({ account_id: accountId, metric_key: metricKey });
    return apiClient.get(`${BASE}/data/coverage${qs}`);
};

export const createAnalysis = async ({
    accountId,
    dateStart,
    dateEnd,
    metricKey = 'omni_purchase',
    nRestarts,
    holdoutDays,
    marginalStep,
}) => {
    if (!accountId) throw new Error('缺少 accountId');
    if (!dateStart || !dateEnd) throw new Error('缺少 dateStart 或 dateEnd');
    const body = {
        account_id: accountId,
        date_start: dateStart,
        date_end: dateEnd,
        metric_key: metricKey,
    };
    if (nRestarts != null) body.n_restarts = nRestarts;
    if (holdoutDays != null) body.holdout_days = holdoutDays;
    if (marginalStep != null) body.marginal_step = marginalStep;
    try {
        return await apiClient.post(`${BASE}/analyses`, body);
    } catch (err) {
        throw ensureStructured(err, 'guardrail_rejected');
    }
};

export const listAnalyses = async ({ accountId, page = 1, pageSize = 20 } = {}) => {
    if (!accountId) throw new Error('缺少 accountId');
    const qs = buildQuery({
        account_id: accountId,
        page,
        page_size: pageSize,
    });
    return apiClient.get(`${BASE}/analyses${qs}`);
};

export const getAnalysis = async (snapshotId) => {
    if (!snapshotId) throw new Error('缺少 snapshotId');
    return apiClient.get(`${BASE}/analyses/${snapshotId}`);
};

export const saveAiSummary = async ({ snapshotId, aiSummary }) => {
    if (!snapshotId) throw new Error('缺少 snapshotId');
    if (typeof aiSummary !== 'string' || aiSummary.length === 0) {
        throw new Error('缺少 aiSummary');
    }
    try {
        return await apiClient.put(
            `${BASE}/analyses/${snapshotId}/ai-summary`,
            { ai_summary: aiSummary }
        );
    } catch (err) {
        throw ensureStructured(err, 'ai_summary_save_failed');
    }
};

const contributionService = {
    pingContribution,
    listCampaignSummaries,
    refreshContributionData,
    getGroups,
    updateGroups,
    resetGroups,
    fetchDataCoverage,
    createAnalysis,
    listAnalyses,
    getAnalysis,
    saveAiSummary,
};

export default contributionService;
