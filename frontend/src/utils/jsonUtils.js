/**
 * @fileoverview JSON 解析工具函式（3.9 — JSON 欄位型別相容性）
 *
 * 背景：後端原以 String 型別儲存 JSON（JSON.parse 才能讀取），
 * 後改為 SQLAlchemy JSON 型別，直接回傳物件/陣列。
 * 此輔助函式相容兩種格式，確保前端不因後端版本差異而出錯。
 */

/**
 * 安全解析 JSON 欄位值，相容「已是物件/陣列」與「JSON 字串」兩種格式。
 *
 * @template T
 * @param {T|string|null|undefined} value - 待解析的值
 * @param {T} [defaultValue=[]] - 解析失敗時的預設值
 * @returns {T} 解析後的值
 *
 * @example
 * // 後端已回傳陣列（新格式）
 * safeParseJson(['metric1', 'metric2'])  // => ['metric1', 'metric2']
 *
 * // 後端回傳 JSON 字串（舊格式）
 * safeParseJson('["metric1","metric2"]') // => ['metric1', 'metric2']
 *
 * // 解析失敗時使用預設值
 * safeParseJson('invalid json', [])      // => []
 */
export function safeParseJson(value, defaultValue = []) {
  // 已是物件或陣列，直接回傳（後端新格式）
  if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
    return value;
  }
  // 是字串，嘗試解析（後端舊格式或 localStorage 緩存）
  if (typeof value === 'string' && value.trim() !== '') {
    try {
      return JSON.parse(value);
    } catch {
      console.warn('[safeParseJson] 解析失敗，使用預設值:', value);
      return defaultValue;
    }
  }
  // null / undefined / 空字串 => 回傳預設值
  return defaultValue;
}

/**
 * 安全解析 JSON 物件欄位（預設值為 null）
 *
 * @param {Object|string|null|undefined} value - 待解析的值
 * @param {Object|null} [defaultValue=null] - 解析失敗時的預設值
 * @returns {Object|null} 解析後的物件
 */
export function safeParseJsonObject(value, defaultValue = null) {
  return safeParseJson(value, defaultValue);
}
