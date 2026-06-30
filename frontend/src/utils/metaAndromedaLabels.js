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
