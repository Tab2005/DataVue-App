// Diagnostic breakdown key → Traditional Chinese display label
export const DIAGNOSTIC_KEY_LABELS_ZH = {
    // conversion
    visual_appeal:          '視覺吸引力',
    copywriting:            '文案說服力',
    cta_clarity:            'CTA 清晰度',
    relevance:              '圖文一致性',
    // lead
    trust_signals:          '信任感建立',
    value_proposition:      '價值主張',
    audience_fit:           '受眾匹配度',
    // traffic
    thumb_stop:             '停滯力',
    curiosity_hook:         '好奇心誘因',
    landing_relevance:      '落頁相關性',
    // awareness
    brand_recall:           '品牌記憶度',
    message_clarity:        '訊息清晰度',
    visual_distinctiveness: '視覺辨識度',
    emotional_resonance:    '情感共鳴',
    // video
    hook_strength:          '開場吸引力',
    pacing:                 '節奏感',
    message_delivery:       '訊息傳達效率',
    brand_integration:      '品牌融入度',
    // engagement
    shareability:           '分享潛力',
    emotional_hook:         '情感觸發',
    interaction_trigger:    '互動誘因',
    visual_impact:          '視覺衝擊力',
    // heuristic-only
    cta_presence:           'CTA 存在感',
    placement_fit:          '版位適配',
};

export function getDiagnosticLabel(key, lang = 'zh') {
    if (lang !== 'zh') return key;
    return DIAGNOSTIC_KEY_LABELS_ZH[key] ?? key;
}

// Performance snapshot metric key → Traditional Chinese label
// Keys that stay uppercase (ROAS, CPC) keep their English names
export const PERF_METRIC_LABELS_ZH = {
    spend:          '花費',
    impressions:    '曝光次數',
    clicks:         '點擊數',
    purchases:      '購買次數',
    purchase_value: '購買轉換值',
    roas:           'ROAS',
    ctr:            '點擊率',
    cpc:            'CPC',
    reach:          '觸及人數',
    frequency:      '頻率',
    cpp:            'CPP',
    leads:          '潛在客戶數',
    video_views:    '影片觀看數',
    vtr:            'VTR',
    engagements:    '互動數',
    link_clicks:    '連結點擊數',
};

// Format a raw numeric value for display given its metric key
export function formatPerfValue(key, value) {
    if (value === null || value === undefined) return '—';
    const k = String(key).toLowerCase();
    const n = Number(value);
    if (Number.isNaN(n)) return String(value);
    if (k === 'ctr' || k === 'vtr') {
        // stored as ratio (e.g. 2.163 means 2.163%) or as 0.02163 — detect by magnitude
        const pct = n > 1 ? n : n * 100;
        return pct.toFixed(2) + '%';
    }
    if (k === 'roas') return n.toFixed(2);
    if (k === 'cpc' || k === 'cpp') return n.toFixed(2);
    if (k === 'frequency') return n.toFixed(2);
    // integers
    if (Number.isInteger(n)) return n.toLocaleString();
    // large decimal → 2dp
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function getPerfMetricLabel(key, lang = 'zh') {
    if (lang !== 'zh') return key;
    return PERF_METRIC_LABELS_ZH[String(key).toLowerCase()] ?? key;
}
