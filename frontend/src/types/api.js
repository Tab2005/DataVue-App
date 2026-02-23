/**
 * @fileoverview API 回應型別定義
 * 所有後端 API 回應的 JSDoc 型別，供 VS Code IntelliSense 使用。
 * 在 .js 文件頂端加入 // @ts-check 可啟用型別驗證。
 */

// ─── 使用者 ────────────────────────────────────────────────

/**
 * @typedef {Object} User
 * @property {string} id - 使用者 UUID
 * @property {string} email - Google Email
 * @property {string} name - 顯示名稱
 * @property {string|null} picture - 頭像 URL
 * @property {'super_admin'|'admin'|'member'|'viewer'} role - 角色
 * @property {'active'|'disabled'|'pending'} status - 帳號狀態
 * @property {boolean} is_super_admin - 是否為超級管理員
 * @property {string} created_at - ISO 8601 時間字串
 */

// ─── 團隊 ────────────────────────────────────────────────

/**
 * @typedef {Object} Team
 * @property {string} id - 團隊 UUID
 * @property {string} name - 團隊名稱
 * @property {string} owner_id - 擁有者 ID
 * @property {string|null} fb_app_id - Facebook App ID
 * @property {string|null} fb_app_secret - Facebook App Secret（遮蔽）
 * @property {string[]} visible_ad_account_ids - 可見廣告帳號列表
 * @property {string} created_at - 建立時間
 */

/**
 * @typedef {Object} TeamMember
 * @property {string} id - 成員 UUID
 * @property {string} user_id - 使用者 ID
 * @property {string} team_id - 團隊 ID
 * @property {'admin'|'member'|'viewer'} role - 團隊角色
 * @property {string} joined_at - 加入時間
 * @property {User} user - 使用者詳細資料
 */

// ─── Facebook Ads ────────────────────────────────────────────────

/**
 * @typedef {Object} AdAccount
 * @property {string} id - 廣告帳號 ID（格式：act_xxxxxxxx）
 * @property {string} name - 帳號名稱
 * @property {number} account_status - 帳號狀態（1=active, 2=disabled, 3=unsettled）
 * @property {string} currency - 貨幣代碼（如：TWD, USD）
 * @property {string} timezone_name - 時區（如：Asia/Taipei）
 */

/**
 * @typedef {Object} InsightMetric
 * @property {string} date_start - 開始日期
 * @property {string} date_stop - 結束日期
 * @property {string} impressions - 曝光次數
 * @property {string} clicks - 點擊次數
 * @property {string} spend - 花費金額
 * @property {string} reach - 覆蓋人數
 * @property {string|undefined} ctr - 點擊率
 * @property {string|undefined} cpc - 每次點擊成本
 * @property {string|undefined} cpm - 每千次曝光成本
 * @property {string|undefined} roas - 廣告投資報酬率
 * @property {string|undefined} frequency - 平均頻率
 */

// ─── GSC ────────────────────────────────────────────────

/**
 * @typedef {Object} GscKeyword
 * @property {string} query - 搜尋關鍵字
 * @property {number} clicks - 點擊次數
 * @property {number} impressions - 曝光次數
 * @property {number} ctr - 點擊率（0~1）
 * @property {number} position - 平均排名
 */

/**
 * @typedef {Object} GscPage
 * @property {string} page - 頁面 URL
 * @property {number} clicks - 點擊次數
 * @property {number} impressions - 曝光次數
 * @property {number} ctr - 點擊率（0~1）
 * @property {number} position - 平均排名
 */

// ─── GA4 ────────────────────────────────────────────────

/**
 * @typedef {Object} Ga4Metric
 * @property {string} date - 日期（YYYYMMDD）
 * @property {number} sessions - 工作階段數
 * @property {number} users - 使用者數
 * @property {number} newUsers - 新使用者數
 * @property {number} pageviews - 頁面瀏覽數
 * @property {number} bounceRate - 跳出率
 * @property {number} avgSessionDuration - 平均工作階段時長（秒）
 */

// ─── 儲存的視圖 ────────────────────────────────────────────────

/**
 * @typedef {Object} SavedView
 * @property {string} id - 視圖 UUID
 * @property {string} name - 視圖名稱
 * @property {string} tab - 所屬 tab（facebook / gsc / ga4）
 * @property {string[]} metrics - 已選指標列表
 * @property {Object} filters - 篩選條件
 * @property {string} created_at - 建立時間
 * @property {string} updated_at - 更新時間
 */

// ─── 通用 ────────────────────────────────────────────────

/**
 * @typedef {Object} ApiError
 * @property {string} detail - 錯誤詳情
 * @property {number} status_code - HTTP 狀態碼
 */

/**
 * @typedef {Object} PaginatedResponse
 * @template T
 * @property {T[]} items - 資料列表
 * @property {number} total - 總數量
 * @property {number} page - 當前頁碼
 * @property {number} size - 每頁數量
 */

// 為了讓此文件被視為模組，需要匯出空物件
export {};
