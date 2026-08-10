/**
 * 統一 API Client
 * 提供集中的 fetch 封裝，統一處理認證、錯誤、重試與逾時邏輯。
 */

import { getAuthToken, clearAuthToken, isTokenExpired } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * 全局 API 請求統計（可用於監控）
 */
let requestCount = 0;
let errorCount = 0;

/**
 * 重試設定
 */
const RETRY_CONFIG = {
    maxRetries: 2,
    retryDelay: 1000,         // 毫秒
    retryableStatuses: [502, 503, 504],
};

/**
 * 延遲輔助函式
 */
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface ApiRequestOptions {
    body?: unknown;
    headers?: Record<string, string>;
    skipAuth?: boolean;
    timeout?: number;
    /** 內部重試計數，呼叫端不需自行提供 */
    _retryCount?: number;
}

/**
 * 自訂 API 錯誤類別
 */
export class ApiError extends Error {
    statusCode: number;
    path: string;
    code?: string | null;

    constructor(message: string, statusCode: number, path: string) {
        super(message);
        this.name = 'ApiError';
        this.statusCode = statusCode;
        this.path = path;
    }
}

/**
 * 重導向至登入頁
 */
function redirectToLogin(reason: string): void {
    console.warn(`[ApiClient] 重導向至登入頁：${reason}`);
    const currentPath = window.location.pathname + window.location.search;
    if (currentPath !== '/login' && currentPath !== '/') {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
    }
    window.location.href = '/login';
}

/**
 * 統一 API 請求函式
 *
 * @param method - HTTP 方法（GET, POST, PUT, PATCH, DELETE）
 * @param path - API 路徑（如 /api/users/me）
 * @param options - 額外選項
 * @returns 解析後的 JSON 回應
 */
async function request<T = unknown>(
    method: HttpMethod,
    path: string,
    options: ApiRequestOptions = {}
): Promise<T> {
    const {
        body,
        headers: extraHeaders = {},
        skipAuth = false,
        timeout = 30000,
        _retryCount = 0,
    } = options;

    // Token 過期檢查（在發送請求前）
    if (!skipAuth) {
        const token = getAuthToken();
        if (!token) {
            redirectToLogin('無認證 Token');
            throw new ApiError('未登入', 401, path);
        }
        if (isTokenExpired(token)) {
            clearAuthToken();
            redirectToLogin('Token 已過期');
            throw new ApiError('登入已過期，請重新登入', 401, path);
        }
    }

    // 取得 Team ID（維持與 getAuthHeaders 一致的行為）
    const teamId = localStorage.getItem('selected_team_id');

    // 建構 headers
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(!skipAuth && {
            Authorization: `Bearer ${getAuthToken()}`,
            ...(teamId && { 'X-Team-ID': teamId }),
        }),
        ...extraHeaders,
    };

    // 逾時處理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // 建構請求設定
    const fetchOptions: RequestInit = {
        method,
        headers,
        signal: controller.signal,
        ...(body !== undefined && { body: JSON.stringify(body) }),
    };

    requestCount++;

    try {
        const response = await fetch(`${API_URL}${path}`, fetchOptions);
        clearTimeout(timeoutId);

        // 401：Token 無效或已在伺服器端失效
        if (response.status === 401) {
            clearAuthToken();
            redirectToLogin('伺服器拒絕認證');
            throw new ApiError('登入已失效，請重新登入', 401, path);
        }

        // 需要重試的狀態碼（伺服器暫時不可用）
        if (
            RETRY_CONFIG.retryableStatuses.includes(response.status) &&
            _retryCount < RETRY_CONFIG.maxRetries
        ) {
            console.warn(`[ApiClient] ${response.status} 觸發重試 (${_retryCount + 1}/${RETRY_CONFIG.maxRetries}): ${path}`);
            await sleep(RETRY_CONFIG.retryDelay * (_retryCount + 1));
            return request<T>(method, path, { ...options, _retryCount: _retryCount + 1 });
        }

        // 其他錯誤回應
        if (!response.ok) {
            errorCount++;
            let errorMessage = `HTTP ${response.status}`;
            let errorCode: string | null = null;
            try {
                const errorData = await response.json();
                const detail = errorData.detail || errorData.error || errorData.message;
                // FastAPI 的 HTTPException(detail={"code": ..., "message": ...}) 這種結構化錯誤
                // detail 會是物件，直接塞進 Error 會被 String() 轉成 "[object Object]"，要先拆開
                if (detail && typeof detail === 'object') {
                    errorMessage = detail.message || JSON.stringify(detail);
                    errorCode = detail.code || null;
                } else if (detail) {
                    errorMessage = detail;
                }
            } catch {
                // 無法解析 JSON 錯誤回應，使用預設訊息
            }
            const apiError = new ApiError(errorMessage, response.status, path);
            apiError.code = errorCode;
            throw apiError;
        }

        // 204 No Content
        if (response.status === 204) {
            return null as T;
        }

        return (await response.json()) as T;
    } catch (error) {
        clearTimeout(timeoutId);

        if (error instanceof Error && error.name === 'AbortError') {
            errorCount++;
            throw new ApiError(`請求逾時（>${timeout}ms）`, 0, path);
        }

        throw error;
    }
}

/**
 * 統一 API Client 物件
 */
const apiClient = {
    get: <T = unknown>(path: string, options?: ApiRequestOptions) =>
        request<T>('GET', path, options),
    post: <T = unknown>(path: string, body?: unknown, options?: ApiRequestOptions) =>
        request<T>('POST', path, { body, ...options }),
    put: <T = unknown>(path: string, body?: unknown, options?: ApiRequestOptions) =>
        request<T>('PUT', path, { body, ...options }),
    patch: <T = unknown>(path: string, body?: unknown, options?: ApiRequestOptions) =>
        request<T>('PATCH', path, { body, ...options }),
    delete: <T = unknown>(path: string, options?: ApiRequestOptions) =>
        request<T>('DELETE', path, options),

    /** 取得請求統計 */
    getStats: () => ({ requestCount, errorCount }),
};

export default apiClient;
