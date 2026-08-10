// frontend/src/components/Analytics/analyticsTranslations.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 原本內嵌在 Analytics.jsx 頂部的靜態翻譯字典，純資料、無邏輯，直接搬出。
export const ANALYTICS_TRANSLATIONS = {
    zh: {
        title: "深度成效分析",
        subtitle: "自訂報表與漏斗分析",
        mainSettings: "主要設定",
        level: "分析層級",
        dateRange: "日期範圍",
        customStart: "開始",
        customEnd: "結束",
        advanced: "進階選項",
        compareMode: "V.S 比較模式",
        comparePeriod: "比較期間",
        updateReport: "更新報表",
        keyMetrics: "指標總覽",
        customMetrics: "自訂表格指標欄位",
        levels: {
            campaign: "按活動名稱",
            adset: "按廣告組合名稱",
            ad: "按廣告名稱",
            account: "整體總覽",
        },
        presets: {
            today: "今日",
            yesterday: "昨天",
            this_week: "本週",
            last_week: "上週",
            this_month: "本月",
            last_month: "上月",
            last_7d: "過去 7 天",
            last_14d: "過去 14 天",
            last_30d: "過去 30 天",
            lifetime: "累積歷史成效",
            custom: "自訂",
        },
        comparePresets: {
            previous_period: "前一期",
            year_over_year: "去年同期",
            custom: "自訂",
        },
        table: {
            name: "名稱",
            headers: {
                campaign: "活動名稱",
                adset: "廣告組合名稱",
                ad: "廣告名稱",
                account: "名稱"
            },
            spend: "花費",
            roas: "回報率 (ROAS)",
            purchases: "購買數",
            cpa: "CPA",
            clicks: "點擊數",
            cvr: "轉換率",
            atc: "購物車",
            dropoff: "流失率",
        }
    },
    en: {
        title: "Deep Analytics",
        subtitle: "Custom Reports & Funnel Analysis",
        mainSettings: "Main Settings",
        level: "Analysis Level",
        dateRange: "Date Range",
        customStart: "Start",
        customEnd: "End",
        advanced: "Advanced",
        compareMode: "Comparison Mode",
        comparePeriod: "Compare Period",
        updateReport: "Run Report",
        keyMetrics: "Metrics Overview",
        customMetrics: "Custom Report Metrics",
        levels: {
            campaign: "By Campaign",
            adset: "By Ad Set",
            ad: "By Ad",
            account: "Account Overview",
        },
        presets: {
            today: "Today",
            yesterday: "Yesterday",
            this_week: "This Week",
            last_week: "Last Week",
            this_month: "This Month",
            last_month: "Last Month",
            last_7d: "Past 7 Days",
            last_14d: "Past 14 Days",
            last_30d: "Past 30 Days",
            lifetime: "Lifetime",
            custom: "Custom",
        },
        comparePresets: {
            previous_period: "Previous Period",
            year_over_year: "Year Over Year",
            custom: "Custom",
        },
        table: {
            name: "Name",
            headers: {
                campaign: "Campaign Name",
                adset: "Ad Set Name",
                ad: "Ad Name",
                account: "Name"
            },
            spend: "Spend",
            roas: "ROAS",
            purchases: "Purchases",
            cpa: "CPA",
            clicks: "Link Clicks",
            cvr: "CVR",
            atc: "Add to Cart",
            dropoff: "Drop-off",
        }
    }
};

export default ANALYTICS_TRANSLATIONS;
