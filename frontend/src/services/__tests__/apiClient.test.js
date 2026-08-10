import apiClient, { ApiError } from '../apiClient';
import { saveAuthToken } from '../../utils/auth';

// P2-3 補強測試覆蓋：apiClient 的重試（502/503/504）、逾時、401 重導、ApiError 形狀。

function makeJwt(expInSeconds) {
    const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'test-user', exp: expInSeconds }));
    return `${header}.${payload}.signature`;
}

function seedValidToken() {
    const oneHourFromNow = Math.floor(Date.now() / 1000) + 3600;
    saveAuthToken(makeJwt(oneHourFromNow));
}

function jsonResponse(status, body) {
    return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => body,
    };
}

describe('apiClient', () => {
    beforeEach(() => {
        localStorage.clear();
        sessionStorage.clear();
        // jsdom 預設不支援真正的頁面導航，設定成可寫入的物件，避免
        // 「Not implemented: navigation」噪音，也讓測試能斷言導向的結果。
        delete window.location;
        window.location = { href: '', pathname: '/dashboard', search: '' };
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.useRealTimers();
    });

    describe('認證前置檢查', () => {
        it('無 token 時直接拋出 401 ApiError，不呼叫 fetch', async () => {
            global.fetch = vi.fn();

            await expect(apiClient.get('/api/users/me')).rejects.toMatchObject({
                name: 'ApiError',
                statusCode: 401,
            });
            expect(global.fetch).not.toHaveBeenCalled();
            expect(window.location.href).toBe('/login');
        });

        it('token 已過期時清除 token 並拋出 401 ApiError', async () => {
            const oneHourAgo = Math.floor(Date.now() / 1000) - 3600;
            saveAuthToken(makeJwt(oneHourAgo));
            global.fetch = vi.fn();

            await expect(apiClient.get('/api/users/me')).rejects.toMatchObject({
                statusCode: 401,
            });
            expect(global.fetch).not.toHaveBeenCalled();
            expect(localStorage.getItem('google_token')).toBeNull();
        });

        it('skipAuth 時即使無 token 也會呼叫 fetch，且不帶 Authorization header', async () => {
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }));

            const result = await apiClient.get('/api/health', { skipAuth: true });

            expect(result).toEqual({ ok: true });
            const [, options] = global.fetch.mock.calls[0];
            expect(options.headers.Authorization).toBeUndefined();
        });
    });

    describe('成功路徑', () => {
        it('帶有效 token 時附上 Authorization 與（若有）X-Team-ID header', async () => {
            seedValidToken();
            localStorage.setItem('selected_team_id', 'team_123');
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { rows: [] }));

            await apiClient.get('/api/analytics/report');

            const [url, options] = global.fetch.mock.calls[0];
            expect(url).toContain('/api/analytics/report');
            expect(options.headers.Authorization).toMatch(/^Bearer /);
            expect(options.headers['X-Team-ID']).toBe('team_123');
        });

        it('204 No Content 回傳 null', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 204 });

            const result = await apiClient.delete('/api/reports/1');

            expect(result).toBeNull();
        });

        it('post 會把 body 序列化成 JSON', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { id: 1 }));

            await apiClient.post('/api/reports', { name: 'weekly' });

            const [, options] = global.fetch.mock.calls[0];
            expect(options.method).toBe('POST');
            expect(options.body).toBe(JSON.stringify({ name: 'weekly' }));
        });
    });

    describe('401：伺服器拒絕認證', () => {
        it('回應 401 時清除 token、重導至登入頁並拋出 ApiError', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(401, { detail: 'expired' }));

            await expect(apiClient.get('/api/users/me')).rejects.toMatchObject({
                statusCode: 401,
            });
            expect(localStorage.getItem('google_token')).toBeNull();
            expect(window.location.href).toBe('/login');
        });
    });

    describe('重試：502/503/504', () => {
        it('503 觸發重試，第二次成功則回傳結果', async () => {
            vi.useFakeTimers();
            seedValidToken();
            global.fetch = vi
                .fn()
                .mockResolvedValueOnce(jsonResponse(503, {}))
                .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

            const promise = apiClient.get('/api/flaky');
            await vi.advanceTimersByTimeAsync(1000);
            const result = await promise;

            expect(result).toEqual({ ok: true });
            expect(global.fetch).toHaveBeenCalledTimes(2);
        });

        it('連續失敗超過 maxRetries 後，拋出最後一次的錯誤狀態碼', async () => {
            vi.useFakeTimers();
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(503, { detail: 'down' }));

            const promise = apiClient.get('/api/always-down');
            const assertion = expect(promise).rejects.toMatchObject({ statusCode: 503 });
            await vi.advanceTimersByTimeAsync(1000);
            await vi.advanceTimersByTimeAsync(2000);
            await assertion;

            // maxRetries=2 -> 原始請求 + 2 次重試 = 3 次 fetch
            expect(global.fetch).toHaveBeenCalledTimes(3);
        });

        it('非重試狀態碼（如 404）不會觸發重試', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(404, { detail: 'not found' }));

            await expect(apiClient.get('/api/missing')).rejects.toMatchObject({
                statusCode: 404,
            });
            expect(global.fetch).toHaveBeenCalledTimes(1);
        });
    });

    describe('逾時', () => {
        it('超過 timeout 仍未回應時，中止請求並拋出逾時 ApiError', async () => {
            vi.useFakeTimers();
            seedValidToken();
            global.fetch = vi.fn((url, options) => new Promise((resolve, reject) => {
                options.signal.addEventListener('abort', () => {
                    const err = new Error('Aborted');
                    err.name = 'AbortError';
                    reject(err);
                });
            }));

            const promise = apiClient.get('/api/slow', { timeout: 5000 });
            const assertion = expect(promise).rejects.toMatchObject({ statusCode: 0 });
            await vi.advanceTimersByTimeAsync(5000);
            await assertion;
        });
    });

    describe('ApiError 訊息解析', () => {
        it('detail 為結構化物件時，取出 message 與 code', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(
                jsonResponse(400, { detail: { code: 'INVALID_RANGE', message: '日期區間不合法' } })
            );

            try {
                await apiClient.get('/api/reports');
                throw new Error('should have thrown');
            } catch (error) {
                expect(error).toBeInstanceOf(ApiError);
                expect(error.message).toBe('日期區間不合法');
                expect(error.code).toBe('INVALID_RANGE');
                expect(error.statusCode).toBe(400);
            }
        });

        it('detail 為純字串時直接當作訊息', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue(jsonResponse(400, { detail: '欄位缺漏' }));

            await expect(apiClient.get('/api/reports')).rejects.toMatchObject({
                message: '欄位缺漏',
            });
        });

        it('回應無法解析為 JSON 時退回預設訊息', async () => {
            seedValidToken();
            global.fetch = vi.fn().mockResolvedValue({
                ok: false,
                status: 500,
                json: async () => { throw new Error('not json'); },
            });

            await expect(apiClient.get('/api/reports')).rejects.toMatchObject({
                message: 'HTTP 500',
                statusCode: 500,
            });
        });
    });
});
