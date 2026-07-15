import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    LANDING_CATEGORY_LABELS,
    LANDING_CATEGORY_ORDER,
    LANDING_MATCH_TYPE_OPTIONS,
    TablePager,
    badgeStyle,
    baseCardStyle,
    buttonStyle,
    dayButtonStyle,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';

const LANDING_PAGE_SIZE = 25;

const LandingPagesTab = ({
    language,
    t,
    isMobile,
    propertyId,
    landingDays,
    setLandingDays,
    loadLandingPages,
    landingError,
    landingLoading,
    landingSnapshot,
    landingCategoryFilter,
    setLandingCategoryFilter,
    landingKeyEvent,
    setLandingKeyEvent,
    DaySelector,
    landingRulesOpen,
    setLandingRulesOpen,
    landingRulesError,
    landingRulesLoading,
    landingRules,
    canManageGa4InsightsRules,
    handleDeleteLandingPageRule,
    handleCreateLandingPageRule,
    landingRuleForm,
    setLandingRuleForm,
    landingRuleSaving,
}) => {
    const [landingPage, setLandingPage] = useState(1);

    const filteredSortedLandingPages = useMemo(() => (
        (landingSnapshot?.payload?.landing_pages || [])
            .filter((row) => landingCategoryFilter === 'all' || row.category === landingCategoryFilter)
            .sort((a, b) => (b.sessions || 0) - (a.sessions || 0))
    ), [landingSnapshot, landingCategoryFilter]);

    const landingTotalPages = Math.max(1, Math.ceil(filteredSortedLandingPages.length / LANDING_PAGE_SIZE));
    const landingPageClamped = Math.min(landingPage, landingTotalPages);
    const pagedLandingPages = filteredSortedLandingPages.slice(
        (landingPageClamped - 1) * LANDING_PAGE_SIZE,
        landingPageClamped * LANDING_PAGE_SIZE
    );

    // 篩選條件或資料快照變動時重置回第一頁，避免停在一個已經不存在的頁碼。
    useEffect(() => {
        setLandingPage(1);
    }, [landingCategoryFilter, landingSnapshot?.snapshot_id]);

    return (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Landing pages', '到達頁分析')}</div>
                            <DaySelector value={landingDays} onChange={(d) => { setLandingDays(d); loadLandingPages(propertyId, d); }} />
                        </div>
                        {landingError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{landingError}</div>}
                        {landingLoading && !landingSnapshot ? (
                            emptyState(t('Loading landing pages…', '載入到達頁資料中…'))
                        ) : landingSnapshot?.payload?.landing_pages?.length ? (
                            <>
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px', alignItems: 'center' }}>
                                    {['all', ...LANDING_CATEGORY_ORDER].map((cat) => {
                                        const count = cat === 'all'
                                            ? landingSnapshot.payload.landing_pages.length
                                            : (landingSnapshot.payload.category_counts?.[cat] || 0);
                                        const label = cat === 'all'
                                            ? t('All', '全部')
                                            : tr(language, LANDING_CATEGORY_LABELS[cat].en, LANDING_CATEGORY_LABELS[cat].zh);
                                        return (
                                            <button
                                                key={cat}
                                                type="button"
                                                style={dayButtonStyle(landingCategoryFilter === cat)}
                                                onClick={() => setLandingCategoryFilter(cat)}
                                            >
                                                {label} ({count})
                                            </button>
                                        );
                                    })}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap' }}>
                                    <select
                                        value={landingKeyEvent}
                                        onChange={(event) => {
                                            const next = event.target.value;
                                            setLandingKeyEvent(next);
                                            loadLandingPages(propertyId, landingDays, next);
                                        }}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    >
                                        <option value="">{t('All key events', '全部關鍵事件')}</option>
                                        {(landingSnapshot.payload.available_key_events || []).map((event) => (
                                            <option key={event} value={event}>{event}</option>
                                        ))}
                                    </select>
                                    <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }} title={t('Only events marked as "key events" in GA4 are counted.', '僅統計已在 GA4 標為關鍵事件的事件。')}>
                                        ⓘ {t('Only events marked as key events in GA4', '僅統計已在 GA4 標為關鍵事件的事件')}
                                    </span>
                                </div>
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                                <th style={{ padding: '6px' }}>{t('Page', '頁面')}</th>
                                                <th style={{ padding: '6px' }}>{t('Category', '分類')}</th>
                                                <th style={{ padding: '6px' }}>{t('Sessions', '工作階段')}</th>
                                                <th
                                                    style={{ padding: '6px', cursor: 'help' }}
                                                    title={landingSnapshot.payload.key_events_count_definition || ''}
                                                >
                                                    {t('Key events', '轉換次數')} ⓘ
                                                </th>
                                                <th
                                                    style={{ padding: '6px', cursor: 'help' }}
                                                    title={landingSnapshot.payload.session_key_event_rate_definition || ''}
                                                >
                                                    {t('Conversion rate', '轉換率')} ⓘ
                                                </th>
                                                <th style={{ padding: '6px' }}>{t('Bounce rate', '跳出率')}</th>
                                                <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {pagedLandingPages
                                                .map((row) => (
                                                    <tr key={row.landingPage} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                        <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                                            {row.landingPage}
                                                        </td>
                                                        <td style={{ padding: '6px' }}>
                                                            <span style={badgeStyle(row.category)}>
                                                                {tr(language, LANDING_CATEGORY_LABELS[row.category]?.en, LANDING_CATEGORY_LABELS[row.category]?.zh) || row.category}
                                                            </span>
                                                        </td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.sessions)}</td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.conversions)}</td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.session_key_event_rate)}</td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.bounceRate)}</td>
                                                        <td style={{ padding: '6px' }}>
                                                            {row.is_high_traffic_low_conversion && (
                                                                <span style={badgeStyle('flagged')}>{t('High traffic, low conversion', '高流量低轉換')}</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                        </tbody>
                                    </table>
                                </div>
                                <TablePager
                                    page={landingPageClamped}
                                    totalPages={landingTotalPages}
                                    onPageChange={setLandingPage}
                                    language={language}
                                />
                            </>
                        ) : (
                            emptyState(t('No landing page data.', '暫無到達頁資料。'))
                        )}
                    </section>

                    <section style={baseCardStyle}>
                        <button
                            type="button"
                            onClick={() => setLandingRulesOpen((prev) => !prev)}
                            style={{ ...secondaryButtonStyle, width: '100%', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                        >
                            <span>{t('Classification rules', '分類規則')}</span>
                            <span>{landingRulesOpen ? '▲' : '▼'}</span>
                        </button>
                        {landingRulesOpen && (
                            <div style={{ marginTop: '14px', display: 'grid', gap: '14px' }}>
                                {landingRulesError && <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>{landingRulesError}</div>}
                                {landingRulesLoading && !landingRules ? (
                                    emptyState(t('Loading rules…', '載入規則中…'))
                                ) : landingRules && landingRules.length === 0 ? (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                        {t('No custom rules yet — using built-in default keyword rules.', '目前使用內建預設規則。')}
                                    </div>
                                ) : (
                                    <div style={{ display: 'grid', gap: '8px' }}>
                                        {(landingRules || []).map((rule) => (
                                            <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '10px 12px', gap: '8px', flexWrap: 'wrap' }}>
                                                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                                                    <span style={badgeStyle(rule.category)}>
                                                        {tr(language, LANDING_CATEGORY_LABELS[rule.category]?.en, LANDING_CATEGORY_LABELS[rule.category]?.zh)}
                                                    </span>
                                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                                        {tr(language, LANDING_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.en, LANDING_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.zh)}
                                                    </span>
                                                    <code style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{rule.pattern}</code>
                                                    <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('priority', '優先序')} {rule.priority}</span>
                                                </div>
                                                {canManageGa4InsightsRules && (
                                                    <button type="button" style={{ ...secondaryButtonStyle, padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => handleDeleteLandingPageRule(rule.id)}>
                                                        {t('Delete', '刪除')}
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {canManageGa4InsightsRules ? (
                                    <form onSubmit={handleCreateLandingPageRule} style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(5, minmax(0, 1fr))' }}>
                                        <select value={landingRuleForm.category} onChange={(event) => setLandingRuleForm((prev) => ({ ...prev, category: event.target.value }))} style={inputStyle}>
                                            {LANDING_CATEGORY_ORDER.map((cat) => (
                                                <option key={cat} value={cat}>{tr(language, LANDING_CATEGORY_LABELS[cat].en, LANDING_CATEGORY_LABELS[cat].zh)}</option>
                                            ))}
                                        </select>
                                        <select value={landingRuleForm.match_type} onChange={(event) => setLandingRuleForm((prev) => ({ ...prev, match_type: event.target.value }))} style={inputStyle}>
                                            {LANDING_MATCH_TYPE_OPTIONS.map((option) => (
                                                <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                            ))}
                                        </select>
                                        <input
                                            type="text"
                                            value={landingRuleForm.pattern}
                                            onChange={(event) => setLandingRuleForm((prev) => ({ ...prev, pattern: event.target.value }))}
                                            placeholder={t('Pattern (e.g. /product)', '比對字串（例：/product）')}
                                            style={inputStyle}
                                        />
                                        <input
                                            type="number"
                                            min="0"
                                            value={landingRuleForm.priority}
                                            onChange={(event) => setLandingRuleForm((prev) => ({ ...prev, priority: event.target.value }))}
                                            placeholder={t('Priority', '優先序')}
                                            style={inputStyle}
                                        />
                                        <button type="submit" style={buttonStyle} disabled={landingRuleSaving || !landingRuleForm.pattern.trim()}>
                                            {landingRuleSaving ? t('Saving…', '儲存中…') : t('Add rule', '新增規則')}
                                        </button>
                                    </form>
                                ) : (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                        {t('You do not have permission to manage classification rules.', '您沒有管理分類規則的權限。')}
                                    </div>
                                )}
                            </div>
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={landingSnapshot}
                        kind="landing_page"
                        contextLabel={t(
                            `Property ${propertyId}; key event ${landingSnapshot?.payload?.key_event || 'all'}; period ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；關鍵事件 ${landingSnapshot?.payload?.key_event || '全部'}；期間 ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({
                            key_event: landingSnapshot?.payload?.key_event || null,
                            landing_pages: landingSnapshot?.payload?.landing_pages || [],
                            category_counts: landingSnapshot?.payload?.category_counts || {},
                        })}
                    />
    </>
    );
};

export default LandingPagesTab;
