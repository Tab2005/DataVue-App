/**
 * useTokenRefresh Hook
 * 自動監控 Token 有效期並在過期前或過期時觸發回調。
 */

import { useEffect, useCallback } from 'react';
import { getTokenRemainingTime, clearAuthToken } from '../utils/auth';

/** 到期前幾毫秒觸發警告（5 分鐘） */
const REFRESH_THRESHOLD = 5 * 60 * 1000;

/** 每分鐘檢查一次 */
const CHECK_INTERVAL = 60 * 1000;

/**
 * 自動監控 Token 有效期並在過期前觸發重新登入
 *
 * @param {function} onExpired - Token 過期時的回調（通常導向登入頁）
 */
export function useTokenRefresh(onExpired) {
    const handleExpired = useCallback(() => {
        clearAuthToken();
        onExpired?.();
    }, [onExpired]);

    useEffect(() => {
        const checkInterval = setInterval(() => {
            const remaining = getTokenRemainingTime();

            // remaining === -1 表示找不到過期時間（無法確認），暫時跳過
            if (remaining === -1) return;

            if (remaining <= 0) {
                console.warn('[TokenRefresh] Token 已過期');
                handleExpired();
                clearInterval(checkInterval);
                return;
            }

            if (remaining <= REFRESH_THRESHOLD) {
                console.info(
                    `[TokenRefresh] Token 將在 ${Math.round(remaining / 1000)} 秒後過期，請準備重新登入`
                );
                // TODO: 若後端支援 implicit flow 靜默刷新，可在此觸發
            }
        }, CHECK_INTERVAL);

        return () => clearInterval(checkInterval);
    }, [handleExpired]);
}

export default useTokenRefresh;
