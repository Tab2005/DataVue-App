/**
 * @fileoverview Metrics Registry Query Hook
 * 從後端取得廣告指標定義，避免前後端各自維護一份指標清單。
 *
 * 使用方式：
 *   const { data, isLoading } = useMetricsRegistry();
 *   const metric = data?.metrics?.find(m => m.key === 'spend');
 *
 *   // 依分類篩選
 *   const { data } = useMetricsRegistry('conversion');
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';

/**
 * 本地備份指標清單（當後端 API 請求失敗時使用）
 * 僅保留精簡版，詳細定義以後端為準。
 */
const LOCAL_METRICS_FALLBACK = {
  metrics: [
    { key: 'spend',       label: '花費',         label_en: 'Spend',        category: 'cost',        format: 'currency'   },
    { key: 'impressions', label: '曝光次數',      label_en: 'Impressions',  category: 'delivery',    format: 'number'     },
    { key: 'clicks',      label: '點擊次數',      label_en: 'Clicks',       category: 'delivery',    format: 'number'     },
    { key: 'reach',       label: '觸及人數',      label_en: 'Reach',        category: 'delivery',    format: 'number'     },
    { key: 'ctr',         label: '點擊率',        label_en: 'CTR',          category: 'performance', format: 'percentage' },
    { key: 'cpc',         label: '每次點擊成本',  label_en: 'CPC',          category: 'cost',        format: 'currency'   },
    { key: 'cpm',         label: '每千次曝光成本', label_en: 'CPM',         category: 'cost',        format: 'currency'   },
    { key: 'roas',        label: '廣告投資回報率', label_en: 'ROAS',        category: 'conversion',  format: 'multiplier' },
    { key: 'purchases',   label: '購買次數',      label_en: 'Purchases',    category: 'conversion',  format: 'number'     },
    { key: 'purchase_value', label: '購買金額',   label_en: 'Purchase Value', category: 'conversion', format: 'currency' },
  ],
  categories: ['delivery', 'cost', 'performance', 'conversion', 'engagement', 'video', 'messaging'],
  total: 10,
};

/**
 * 取得廣告指標定義清單
 *
 * @param {string|null} category - 可選，篩選特定分類
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useMetricsRegistry(category = null) {
  return useQuery({
    queryKey: ['metrics', 'registry', category],
    queryFn: () =>
      apiClient.get(
        `/api/metrics/registry${category ? `?category=${category}` : ''}`
      ),
    // 指標定義不常變更，快取 1 小時
    staleTime: 60 * 60 * 1000,
    gcTime: 2 * 60 * 60 * 1000,
    // 網路失敗時使用本地備份
    placeholderData: LOCAL_METRICS_FALLBACK,
    retry: 2,
  });
}

/**
 * 取得單一指標的詳細定義
 *
 * @param {string} metricKey - 指標 key（如 'spend', 'roas'）
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useMetricDetail(metricKey) {
  return useQuery({
    queryKey: ['metrics', 'registry', 'detail', metricKey],
    queryFn: () => apiClient.get(`/api/metrics/registry/${metricKey}`),
    staleTime: 60 * 60 * 1000,
    gcTime: 2 * 60 * 60 * 1000,
    enabled: Boolean(metricKey),
  });
}
