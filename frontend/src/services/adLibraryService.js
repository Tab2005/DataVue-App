/**
 * 廣告文案庫 API 服務層（docs/73、docs/74）
 *
 * 包裝 backend/modules/ad_library/ 的端點：
 *   GET  /api/ad-library/accounts
 *   POST /api/ad-library/refresh
 *   GET  /api/ad-library/refresh/{job_id}
 *   GET  /api/ad-library/ads
 *   GET  /api/ad-library/ads/export   （CSV，blob 下載）
 *   GET  /api/ad-library/media/{id}    （圖片，blob URL）
 *   GET  /api/ad-library/tree           （行銷活動 → 廣告組合 → 廣告，docs/74）
 *   GET  /api/ad-library/campaigns/{id}
 *   GET  /api/ad-library/adsets/{id}
 *   GET  /api/ad-library/comparisons    （素材測試／文案測試／重複投放，docs/74）
 *   GET  /api/ad-library/contents       （內容元件）
 *   GET  /api/ad-library/ads/{id}/asset-insights（動態素材元件成效，docs/74 第 3 階段）
 *   GET  /api/ad-library/ai-analysis   （最近一次 AI 分析，docs/75）
 *   POST /api/ad-library/ai-analysis   （串流產生 AI 分析，回傳純文字 Markdown）
 *
 * 圖片與 CSV 需帶 Authorization header，<img src> / <a href> 無法直接帶，
 * 因此用 fetch 取回 blob 後轉成 object URL。
 */
import apiClient from './apiClient';
import { getAuthToken } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BASE = '/api/ad-library';

const buildQuery = (params) => {
    const search = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') return;
        search.append(key, String(value));
    });
    const qs = search.toString();
    return qs ? `?${qs}` : '';
};

const authHeaders = () => {
    const teamId = localStorage.getItem('selected_team_id');
    return {
        Authorization: `Bearer ${getAuthToken()}`,
        ...(teamId && { 'X-Team-ID': teamId }),
    };
};

export const listAccounts = () => apiClient.get(`${BASE}/accounts`);

export const startRefresh = (accountId) =>
    apiClient.post(`${BASE}/refresh`, { account_id: accountId });

export const getRefreshJob = (jobId) => apiClient.get(`${BASE}/refresh/${encodeURIComponent(jobId)}`);

export const listAds = ({ accountId, status, mediaType, q, sort, order, page, pageSize, copyKey, mediaKey }) =>
    apiClient.get(
        `${BASE}/ads${buildQuery({
            account_id: accountId,
            status,
            media_type: mediaType,
            q,
            sort,
            order,
            page,
            page_size: pageSize,
            copy_key: copyKey,
            media_key: mediaKey,
        })}`
    );

export const getTree = ({ accountId, status }) =>
    apiClient.get(`${BASE}/tree${buildQuery({ account_id: accountId, status })}`);

export const getCampaign = (id) => apiClient.get(`${BASE}/campaigns/${encodeURIComponent(id)}`);

export const getAdset = (id) => apiClient.get(`${BASE}/adsets/${encodeURIComponent(id)}`);

export const getComparisons = ({ accountId, scope, relation }) =>
    apiClient.get(`${BASE}/comparisons${buildQuery({ account_id: accountId, scope, relation })}`);

export const listContents = ({ accountId, kind, q, sort, page, pageSize }) =>
    apiClient.get(`${BASE}/contents${buildQuery({ account_id: accountId, kind, q, sort, page, page_size: pageSize })}`);

export const getAdAssetInsights = (itemId) =>
    apiClient.get(`${BASE}/ads/${encodeURIComponent(itemId)}/asset-insights`);

export const getAiAnalysis = ({ accountId, campaignId }) =>
    apiClient.get(`${BASE}/ai-analysis${buildQuery({ account_id: accountId, campaign_id: campaignId })}`);

/**
 * 串流產生 AI 分析；每收到一段文字呼叫 onChunk(累積全文)。
 * 失敗時拋出帶後端 detail 的 Error（例如未設定 AI API Key）。
 */
export const streamAiAnalysis = async ({ accountId, campaignId, model, onChunk, signal }) => {
    const resp = await fetch(`${API_URL}${BASE}/ai-analysis`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: accountId, campaign_id: campaignId, ...(model && { model }) }),
        signal,
    });
    if (!resp.ok) {
        let detail = `AI 分析失敗（${resp.status}）`;
        try {
            const body = await resp.json();
            if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : detail;
        } catch {
            // 非 JSON 錯誤回應時沿用預設訊息
        }
        throw new Error(detail);
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let text = '';
    for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
        onChunk?.(text);
    }
    text += decoder.decode();
    onChunk?.(text);
    return text;
};

export const getContent = (id) => apiClient.get(`${BASE}/contents/${encodeURIComponent(id)}`);

export const downloadCsv = async ({ accountId, status, mediaType, q, sort, order, copyKey, mediaKey }) => {
    const qs = buildQuery({
        account_id: accountId, status, media_type: mediaType, q, sort, order, copy_key: copyKey, media_key: mediaKey,
    });
    const resp = await fetch(`${API_URL}${BASE}/ads/export${qs}`, { headers: authHeaders() });
    if (!resp.ok) throw new Error(`匯出失敗（${resp.status}）`);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ad_library_${accountId}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
};

export const fetchMediaBlobUrl = async (assetId, signal) => {
    const resp = await fetch(`${API_URL}${BASE}/media/${encodeURIComponent(assetId)}`, {
        headers: authHeaders(),
        signal,
    });
    if (!resp.ok) throw new Error(`media ${resp.status}`);
    return URL.createObjectURL(await resp.blob());
};
