const TOKEN_KEY = 'google_token';
const TOKEN_EXPIRY_KEY = 'google_token_expiry';

/**
 * 解析 JWT Payload（不需要驗證簽名，僅讀取宣告）
 * @param {string} token - JWT token 字串
 * @returns {object|null} - 解析後的 payload 或 null
 */
export function parseJwtPayload(token) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const payload = parts[1];
        // 補齊 base64 padding
        const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4);
        const decoded = atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
        return JSON.parse(decoded);
    } catch {
        return null;
    }
}

/**
 * 儲存認證 Token 並同時儲存過期時間
 * @param {string} token - Google ID Token
 */
export function saveAuthToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
    // 從 JWT payload 讀取過期時間
    const payload = parseJwtPayload(token);
    if (payload?.exp) {
        localStorage.setItem(TOKEN_EXPIRY_KEY, String(payload.exp * 1000)); // 轉為毫秒
    }
}

/**
 * 取得儲存的認證 Token
 * @returns {string|null}
 */
export const getAuthToken = () => {
    return localStorage.getItem(TOKEN_KEY);
};

/**
 * 檢查 Token 是否已過期
 * @param {string} [token] - 若未提供則使用 localStorage 中的 Token
 * @returns {boolean} - true 表示已過期或無法確認
 */
export function isTokenExpired(token) {
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (!expiryStr) {
        // 無過期時間記錄，嘗試從 Token 解析
        const targetToken = token || getAuthToken();
        if (!targetToken) return true;
        const payload = parseJwtPayload(targetToken);
        if (!payload?.exp) return false; // 無法確認，視為未過期
        return Date.now() > payload.exp * 1000;
    }

    return Date.now() > parseInt(expiryStr, 10);
}

/**
 * 取得 Token 剩餘有效時間（毫秒）
 * @returns {number} - 剩餘毫秒數，<=0 表示已過期，-1 表示無法確認
 */
export function getTokenRemainingTime() {
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryStr) return -1;
    return parseInt(expiryStr, 10) - Date.now();
}

export const getAuthHeaders = () => {
    const token = getAuthToken();
    const teamId = localStorage.getItem('selected_team_id');

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    if (teamId) {
        headers['X-Team-ID'] = teamId;
    }

    return headers;
};

/**
 * 清除認證 Token（登出時使用）
 */
export const clearAuthToken = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    sessionStorage.removeItem('redirectAfterLogin');
};
