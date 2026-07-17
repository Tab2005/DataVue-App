// Date Range Presets Configuration (aligned with GA4)
export const DATE_PRESETS = [
    { key: 'today', label_zh: '今日', label_en: 'Today', days: 0, isToday: true },
    { key: 'yesterday', label_zh: '昨天', label_en: 'Yesterday', days: 1, isYesterday: true },
    { key: 'this_week', label_zh: '本週', label_en: 'This Week', days: null, isThisWeek: true },
    { key: 'last_week', label_zh: '上週', label_en: 'Last Week', days: null, isLastWeek: true },
    { key: 'this_month', label_zh: '本月', label_en: 'This Month', days: null, isThisMonth: true },
    { key: 'last_month', label_zh: '上月', label_en: 'Last Month', days: null, isLastMonth: true },
    { key: 'last_7d', label_zh: '過去 7 天', label_en: 'Past 7 Days', days: 7 },
    { key: 'last_14d', label_zh: '過去 14 天', label_en: 'Past 14 Days', days: 14 },
    { key: 'last_28d', label_zh: '過去 28 天', label_en: 'Past 28 Days', days: 28 },
    { key: 'custom', label_zh: '自訂', label_en: 'Custom', days: null }
];

// Compare Mode Options (aligned with GA4)
export const COMPARE_OPTIONS = [
    { key: 'none', label_zh: '不比較', label_en: 'No Comparison' },
    { key: 'previous_period', label_zh: '前一時段', label_en: 'Previous Period' },
    { key: 'previous_year', label_zh: '去年同期', label_en: 'Previous Year' }
];


// Tab Configuration

export const TABS = [
    { key: 'daily', label_zh: '📈 每日成效', label_en: '📈 Daily Performance', dimension: 'date' },
    { key: 'query', label_zh: '🔍 關鍵字分析', label_en: '🔍 Keyword Analysis', dimension: 'query' },
    { key: 'page', label_zh: '📄 頁面分析', label_en: '📄 Page Analysis', dimension: 'page' },
    { key: 'trend', label_zh: '📊 頁面趨勢', label_en: '📊 Page Trends', dimension: 'page' },
    { key: 'country', label_zh: '🌍 地區分佈', label_en: '🌍 Country', dimension: 'country' },
    { key: 'device', label_zh: '📱 裝置分佈', label_en: '📱 Device', dimension: 'device' },
    { key: 'gap', label_zh: '🎯 內容缺口', label_en: '🎯 Keyword Gap', dimension: 'page' },
    { key: 'searchAppearance', label_zh: '🎨 搜尋外觀', label_en: '🎨 Search Appearance', dimension: 'searchAppearance' }
];

// Trend Sub-tabs
export const TREND_SUBTABS = [
    { key: 'top', label_zh: '頂層', label_en: 'Top' },
    { key: 'up', label_zh: '走勢向上', label_en: 'Trending Up' },
    { key: 'down', label_zh: '走勢向下', label_en: 'Trending Down' }
];

// Country code to name mapping (expanded list)
export const COUNTRY_NAMES = {
    // East Asia
    twn: { zh: '台灣', en: 'Taiwan' },
    jpn: { zh: '日本', en: 'Japan' },
    kor: { zh: '韓國', en: 'South Korea' },
    chn: { zh: '中國', en: 'China' },
    hkg: { zh: '香港', en: 'Hong Kong' },
    mac: { zh: '澳門', en: 'Macau' },
    // Southeast Asia
    sgp: { zh: '新加坡', en: 'Singapore' },
    mys: { zh: '馬來西亞', en: 'Malaysia' },
    tha: { zh: '泰國', en: 'Thailand' },
    vnm: { zh: '越南', en: 'Vietnam' },
    phl: { zh: '菲律賓', en: 'Philippines' },
    idn: { zh: '印尼', en: 'Indonesia' },
    mmr: { zh: '緬甸', en: 'Myanmar' },
    khm: { zh: '柬埔寨', en: 'Cambodia' },
    lao: { zh: '寮國', en: 'Laos' },
    brn: { zh: '汶萊', en: 'Brunei' },
    // North America
    usa: { zh: '美國', en: 'USA' },
    can: { zh: '加拿大', en: 'Canada' },
    mex: { zh: '墨西哥', en: 'Mexico' },
    // Europe
    gbr: { zh: '英國', en: 'UK' },
    deu: { zh: '德國', en: 'Germany' },
    fra: { zh: '法國', en: 'France' },
    ita: { zh: '義大利', en: 'Italy' },
    esp: { zh: '西班牙', en: 'Spain' },
    nld: { zh: '荷蘭', en: 'Netherlands' },
    bel: { zh: '比利時', en: 'Belgium' },
    che: { zh: '瑞士', en: 'Switzerland' },
    aut: { zh: '奧地利', en: 'Austria' },
    pol: { zh: '波蘭', en: 'Poland' },
    swe: { zh: '瑞典', en: 'Sweden' },
    nor: { zh: '挪威', en: 'Norway' },
    dnk: { zh: '丹麥', en: 'Denmark' },
    fin: { zh: '芬蘭', en: 'Finland' },
    irl: { zh: '愛爾蘭', en: 'Ireland' },
    prt: { zh: '葡萄牙', en: 'Portugal' },
    rus: { zh: '俄羅斯', en: 'Russia' },
    ukr: { zh: '烏克蘭', en: 'Ukraine' },
    tur: { zh: '土耳其', en: 'Turkey' },
    grc: { zh: '希臘', en: 'Greece' },
    // Oceania
    aus: { zh: '澳洲', en: 'Australia' },
    nzl: { zh: '紐西蘭', en: 'New Zealand' },
    // South America
    bra: { zh: '巴西', en: 'Brazil' },
    arg: { zh: '阿根廷', en: 'Argentina' },
    chl: { zh: '智利', en: 'Chile' },
    col: { zh: '哥倫比亞', en: 'Colombia' },
    per: { zh: '秘魯', en: 'Peru' },
    // Middle East
    are: { zh: '阿聯酋', en: 'UAE' },
    sau: { zh: '沙烏地阿拉伯', en: 'Saudi Arabia' },
    isr: { zh: '以色列', en: 'Israel' },
    // South Asia
    ind: { zh: '印度', en: 'India' },
    pak: { zh: '巴基斯坦', en: 'Pakistan' },
    bgd: { zh: '孟加拉', en: 'Bangladesh' },
    lka: { zh: '斯里蘭卡', en: 'Sri Lanka' },
    // Africa
    zaf: { zh: '南非', en: 'South Africa' },
    egy: { zh: '埃及', en: 'Egypt' },
    nga: { zh: '奈及利亞', en: 'Nigeria' },
    ken: { zh: '肯亞', en: 'Kenya' },
    // Central Asia
    kaz: { zh: '哈薩克', en: 'Kazakhstan' },
    // Eastern Europe
    alb: { zh: '阿爾巴尼亞', en: 'Albania' },
    // Caribbean / Central America
    pry: { zh: '巴拉圭', en: 'Paraguay' },
    bhs: { zh: '巴哈馬', en: 'Bahamas' },
    blz: { zh: '貝里斯', en: 'Belize' },
    cuw: { zh: '庫拉索', en: 'Curaçao' },
    // Pacific
    fji: { zh: '斐濟', en: 'Fiji' },
    gum: { zh: '關島', en: 'Guam' },
    // Additional countries
    ecu: { zh: '厄瓜多', en: 'Ecuador' },
    geo: { zh: '喬治亞', en: 'Georgia' },
    hnd: { zh: '宏都拉斯', en: 'Honduras' },
    jor: { zh: '約旦', en: 'Jordan' },
    ltu: { zh: '立陶宛', en: 'Lithuania' },
    mar: { zh: '摩洛哥', en: 'Morocco' },
    syc: { zh: '塞席爾', en: 'Seychelles' },
    ven: { zh: '委內瑞拉', en: 'Venezuela' }
};

// Device type mapping
export const DEVICE_NAMES = {
    MOBILE: { zh: '📱 手機', en: '📱 Mobile', color: '#10B981' },
    DESKTOP: { zh: '💻 桌機', en: '💻 Desktop', color: '#3B82F6' },
    TABLET: { zh: '📟 平板', en: '📟 Tablet', color: '#F59E0B' }
};

// searchAppearance 維度的官方類型對照（依 Google Search Console 官方文件整理，2026-07-17 查證）
// https://support.google.com/webmasters/answer/17011259
// 未列在此表的值（含未來新增或未公開類型）會直接顯示 API 原始字串，不會顯示為空白，
// 避免因為硬編碼清單而漏掉新類型。
export const SEARCH_APPEARANCE_NAMES = {
    AMP_TOP_STORIES: { zh: 'AMP 頭條新聞', en: 'AMP Top Stories' },
    AMP_BLUE_LINK: { zh: 'AMP 一般連結', en: 'AMP Blue Link' },
    AMP_IMAGE_RESULT: { zh: 'AMP 圖片結果', en: 'AMP Image Result' },
    FORUMS: { zh: '論壇討論', en: 'Forum Discussions' },
    EDU_Q_AND_A: { zh: '教育問答', en: 'Education Q&A' },
    JOB_DETAILS: { zh: '職缺詳情', en: 'Job Details' },
    JOB_LISTING: { zh: '職缺列表', en: 'Job Listing' },
    MATH_SOLVERS: { zh: '數學解題', en: 'Math Solvers' },
    ACTION: { zh: '媒體互動內容', en: 'Media Actions' },
    MERCHANT_LISTINGS: { zh: '商家資訊', en: 'Merchant Listings' },
    PRACTICE_PROBLEMS: { zh: '練習題', en: 'Practice Problems' },
    PRODUCT_SNIPPETS: { zh: '商品摘要', en: 'Product Snippets' },
    TPF_QA: { zh: '問答摘要', en: 'Q&A Rich Results' },
    RECIPE_FEATURE: { zh: '食譜集錦', en: 'Recipe Gallery' },
    RECIPE_RICH_SNIPPET: { zh: '食譜摘要', en: 'Recipe Rich Result' },
    REVIEW_SNIPPET: { zh: '評論摘要', en: 'Review Snippet' },
    SUBSCRIBED_CONTENT: { zh: '訂閱內容', en: 'Subscribed Content' },
    TRANSLATED_RESULT: { zh: '翻譯結果', en: 'Translated Result' },
    VIDEO: { zh: '影片', en: 'Video' },
    AMP_STORY: { zh: 'AMP 圖文故事', en: 'Web Story' }
};
