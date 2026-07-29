import React, { useEffect, useMemo, useState } from 'react';

import {
    AIInsightNote,
    CHANNEL_DIMENSION_OPTIONS,
    CHANNEL_GROUP_MATCH_TYPE_OPTIONS,
    LANDING_CATEGORY_LABELS,
    LANDING_CATEGORY_ORDER,
    LANDING_MATCH_TYPE_OPTIONS,
    TablePager,
    badgeStyle,
    baseCardStyle,
    buttonStyle,
    channelDimensionLabel,
    dayButtonStyle,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';

const LANDING_PAGE_SIZE = 25;

// docs/46：把目前的渠道篩選狀態轉成一句話，塞進 AI 解讀的 contextLabel，
// 讓 AI 知道這份 payload 已經是篩選過某個渠道的子集，不是全站/全渠道的
// 到達頁表現（否則模型容易誤用「整體」語氣下結論）。沒篩選時回傳 null，
// 不影響原本的全域解讀文字。
const channelScopeLabel = (payload, language, t) => {
    if (!payload?.channel_dimension) return null;
    const dimLabel = channelDimensionLabel(payload.channel_dimension, language);
    if (payload.channel_group) {
        return t(`channel filter: ${dimLabel} = custom group "${payload.channel_group}"`, `渠道篩選：${dimLabel} = 自訂分組「${payload.channel_group}」`);
    }
    if (payload.channel_value) {
        return t(`channel filter: ${dimLabel} = "${payload.channel_value}"`, `渠道篩選：${dimLabel} = 「${payload.channel_value}」`);
    }
    return null;
};

// docs/53：分類篩選（商品/文章/功能/其他按鈕）是純前端二次篩選，本來完全
// 不會反映在 AI 解讀的 contextLabel 裡，容易讓 AI 誤以為在分析全部分類。
const categoryScopeLabel = (categoryFilter, language, t) => {
    if (!categoryFilter || categoryFilter === 'all') return null;
    const label = LANDING_CATEGORY_LABELS[categoryFilter]
        ? tr(language, LANDING_CATEGORY_LABELS[categoryFilter].en, LANDING_CATEGORY_LABELS[categoryFilter].zh)
        : categoryFilter;
    return t(`category filter: ${label}`, `分類篩選：${label}`);
};

// docs/54：跟上一期比較開啟時，告訴 AI 現在看到的數字已經有比較資訊可以提，
// 避免 AI 白話解讀完全沒提到「相較上一期」的變化。
const compareScopeLabel = (payload, t) => {
    if (!payload?.compare_enabled) return null;
    if (payload.compare_query_error) return null;
    return t(
        `compared to prior period (${payload.compare_start_date} ~ ${payload.compare_end_date})`,
        `已啟用上一期比較（${payload.compare_start_date} ~ ${payload.compare_end_date}）`
    );
};

// docs/54：次數類指標（工作階段/轉換次數）用相對成長率；比率類指標（轉換率/
// 跳出率）改用百分點差異，避免「5%→6%」被講成「成長20%」造成誤解。pp 是
// percentage point（百分點）的縮寫，不是每個使用者都認得，加 title 滑鼠提示
// 說明清楚，跟畫面上其他 ⓘ 提示同一套「用 cursor: help 提示可以看說明」慣例。
const GrowthBadge = ({ value, isPercentagePoint = false, t }) => {
    if (value == null) return null;
    const arrow = value > 0 ? '▲' : value < 0 ? '▼' : '';
    const color = value > 0 ? '#34d399' : value < 0 ? '#f87171' : 'var(--text-tertiary)';
    const magnitude = Math.abs(value);
    const text = isPercentagePoint ? `${magnitude.toFixed(1)}pp` : `${(magnitude * 100).toFixed(0)}%`;
    const title = isPercentagePoint
        ? t(
            'pp = percentage point, the absolute gap vs. the prior period (e.g. a rate going from 5% to 6% is +1.0pp, not a 20% increase).',
            'pp＝百分點，是跟上一期的絕對差距（例如比率從 5% 變 6% 是 +1.0pp，不是成長 20%）。'
        )
        : undefined;
    return (
        <span style={{ fontSize: '0.72rem', marginLeft: '4px', color, whiteSpace: 'nowrap', cursor: isPercentagePoint ? 'help' : 'default' }} title={title}>
            {arrow}{text}
        </span>
    );
};

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
    landingCompareEnabled,
    setLandingCompareEnabled,
    landingChannelDimension,
    setLandingChannelDimension,
    landingChannelValue,
    setLandingChannelValue,
    landingChannelValues,
    landingChannelValuesLoading,
    loadLandingChannelValues,
    landingChannelGroup,
    setLandingChannelGroup,
    landingChannelGroups,
    landingChannelGroupsLoading,
    loadLandingChannelGroups,
    landingChannelGroupRulesOpen,
    setLandingChannelGroupRulesOpen,
    landingChannelGroupRules,
    landingChannelGroupRulesLoading,
    landingChannelGroupRulesError,
    loadLandingChannelGroupRules,
    handleCreateChannelGroupRule,
    handleDeleteChannelGroupRule,
    landingChannelGroupRuleForm,
    setLandingChannelGroupRuleForm,
    landingChannelGroupRuleSaving,
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
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                {/* docs/54：跟上一期比較開關，預設關閉；開啟時重新請求資料（往前推
                                    同樣天數的前一段期間，沿用目前的渠道/關鍵事件篩選）。 */}
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={landingCompareEnabled}
                                        onChange={(event) => {
                                            const next = event.target.checked;
                                            setLandingCompareEnabled(next);
                                            loadLandingPages(propertyId, landingDays, landingKeyEvent, landingChannelDimension, landingChannelValue, landingChannelGroup, next);
                                        }}
                                    />
                                    {t('Compare to prior period', '比較上一期')}
                                </label>
                                <DaySelector value={landingDays} onChange={(d) => {
                                    setLandingDays(d);
                                    loadLandingPages(propertyId, d);
                                    if (landingChannelDimension) loadLandingChannelValues(propertyId, d, landingChannelDimension);
                                }} />
                            </div>
                        </div>
                        {landingError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{landingError}</div>}
                        {landingSnapshot?.payload?.compare_enabled && landingSnapshot?.payload?.compare_query_error && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    'Could not fetch the prior period for comparison (temporary); showing this period only.',
                                    '暫時無法取得上一期資料做比較，以下僅顯示本期數字。'
                                )}
                            </div>
                        )}
                        {landingLoading && !landingSnapshot ? (
                            emptyState(t('Loading landing pages…', '載入到達頁資料中…'))
                        ) : landingSnapshot?.payload?.landing_pages?.length ? (
                            <>
                                {/* 篩選列：關鍵事件／渠道維度／渠道值下拉統一放最左邊，分類篩選按鈕
                                    接在後面，全部擠在同一行（畫面窄時自然換行，同既有 flexWrap 慣例）。
                                    docs/42：渠道維度選單複用渠道對照分頁既有的 CHANNEL_DIMENSION_OPTIONS，
                                    渠道值選單選了維度後才顯示，選項來自 loadLandingChannelValues 抓到的清單。 */}
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px', alignItems: 'center' }}>
                                    <select
                                        value={landingKeyEvent}
                                        onChange={(event) => {
                                            const next = event.target.value;
                                            setLandingKeyEvent(next);
                                            loadLandingPages(propertyId, landingDays, next);
                                        }}
                                        title={t('Only events marked as "key events" in GA4 are counted.', '僅統計已在 GA4 標為關鍵事件的事件。')}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    >
                                        <option value="">{t('All key events', '全部關鍵事件')}</option>
                                        {(landingSnapshot.payload.available_key_events || []).map((event) => (
                                            <option key={event} value={event}>{event}</option>
                                        ))}
                                    </select>
                                    <select
                                        value={landingChannelDimension}
                                        onChange={(event) => {
                                            const nextDimension = event.target.value;
                                            setLandingChannelDimension(nextDimension);
                                            setLandingChannelValue('');
                                            setLandingChannelGroup('');
                                            loadLandingChannelValues(propertyId, landingDays, nextDimension);
                                            loadLandingChannelGroups(propertyId, nextDimension);
                                            if (landingChannelGroupRulesOpen) loadLandingChannelGroupRules(propertyId, nextDimension);
                                            loadLandingPages(propertyId, landingDays, landingKeyEvent, nextDimension, '', '');
                                        }}
                                        style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                    >
                                        <option value="">{t('No channel filter', '不篩選渠道')}</option>
                                        {CHANNEL_DIMENSION_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                        ))}
                                    </select>
                                    {landingChannelDimension && (
                                        <select
                                            value={landingChannelValue}
                                            onChange={(event) => {
                                                const nextValue = event.target.value;
                                                setLandingChannelValue(nextValue);
                                                setLandingChannelGroup('');
                                                loadLandingPages(propertyId, landingDays, landingKeyEvent, landingChannelDimension, nextValue, '');
                                            }}
                                            disabled={landingChannelValuesLoading}
                                            style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: landingChannelValuesLoading ? 0.6 : 1 }}
                                        >
                                            <option value="">{t('All channel values', '全部渠道')}</option>
                                            {landingChannelValues.map((value) => (
                                                <option key={value} value={value}>{value}</option>
                                            ))}
                                        </select>
                                    )}
                                    {landingChannelDimension && (
                                        // docs/44：自訂分組——跟「渠道值」互斥，選了分組要清空渠道值，反之亦然。
                                        <select
                                            value={landingChannelGroup}
                                            onChange={(event) => {
                                                const nextGroup = event.target.value;
                                                setLandingChannelGroup(nextGroup);
                                                setLandingChannelValue('');
                                                loadLandingPages(propertyId, landingDays, landingKeyEvent, landingChannelDimension, '', nextGroup);
                                            }}
                                            disabled={landingChannelGroupsLoading}
                                            style={{ ...inputStyle, width: 'auto', padding: '8px 10px', opacity: landingChannelGroupsLoading ? 0.6 : 1 }}
                                        >
                                            <option value="">{t('No custom group', '不用自訂分組')}</option>
                                            {landingChannelGroups.map((group) => (
                                                <option key={group.group_label} value={group.group_label}>
                                                    {group.group_label} ({group.rule_count})
                                                </option>
                                            ))}
                                        </select>
                                    )}
                                    {(landingChannelValuesLoading || landingChannelGroupsLoading) && (
                                        <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('Loading channels…', '載入渠道清單中…')}</span>
                                    )}
                                    <span style={{ width: '1px', alignSelf: 'stretch', background: 'var(--glass-border)', margin: '0 2px' }} />
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
                                                .map((row) => {
                                                    const showCompare = landingSnapshot.payload.compare_enabled && !landingSnapshot.payload.compare_query_error;
                                                    const showGrowth = showCompare && !row.is_new;
                                                    return (
                                                    <tr key={row.landingPage} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                        <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                                            {row.landingPage}
                                                        </td>
                                                        <td style={{ padding: '6px' }}>
                                                            <span style={badgeStyle(row.category)}>
                                                                {tr(language, LANDING_CATEGORY_LABELS[row.category]?.en, LANDING_CATEGORY_LABELS[row.category]?.zh) || row.category}
                                                            </span>
                                                        </td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                            {fmtNumber(row.sessions)}
                                                            {showGrowth && <GrowthBadge value={row.sessions_growth_rate} />}
                                                        </td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                            {fmtNumber(row.conversions)}
                                                            {showGrowth && <GrowthBadge value={row.conversions_growth_rate} />}
                                                        </td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                            {fmtPct(row.session_key_event_rate)}
                                                            {showGrowth && <GrowthBadge value={row.session_key_event_rate_delta_pp} isPercentagePoint t={t} />}
                                                        </td>
                                                        <td style={{ padding: '6px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                            {fmtPct(row.bounceRate)}
                                                            {showGrowth && <GrowthBadge value={row.bounce_rate_delta_pp} isPercentagePoint t={t} />}
                                                        </td>
                                                        <td style={{ padding: '6px' }}>
                                                            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                                                {row.is_high_traffic_low_conversion && (
                                                                    <span style={badgeStyle('flagged')}>{t('High traffic, low conversion', '高流量低轉換')}</span>
                                                                )}
                                                                {showCompare && row.is_new && (
                                                                    <span style={badgeStyle('flagged')} title={t('No data in the prior period', '上一期沒有這個頁面的資料')}>
                                                                        🆕 {t('New', '新')}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </td>
                                                    </tr>
                                                    );
                                                })}
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

                    {/* docs/44：渠道值自訂分組規則管理——規則綁定單一維度，直接沿用
                        上方篩選列已選的「維度」，未選維度時提示先選維度再管理規則。 */}
                    <section style={baseCardStyle}>
                        <button
                            type="button"
                            onClick={() => {
                                const next = !landingChannelGroupRulesOpen;
                                setLandingChannelGroupRulesOpen(next);
                                if (next && landingChannelDimension) {
                                    loadLandingChannelGroupRules(propertyId, landingChannelDimension);
                                }
                            }}
                            style={{ ...secondaryButtonStyle, width: '100%', textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
                        >
                            <span>{t('Channel group rules', '渠道分組規則')}</span>
                            <span>{landingChannelGroupRulesOpen ? '▲' : '▼'}</span>
                        </button>
                        {landingChannelGroupRulesOpen && (
                            <div style={{ marginTop: '14px', display: 'grid', gap: '14px' }}>
                                {!landingChannelDimension ? (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                        {t('Select a channel dimension above first to manage its group rules.', '請先在上方篩選列選擇一個渠道維度，才能管理該維度的分組規則。')}
                                    </div>
                                ) : (
                                    <>
                                        {landingChannelGroupRulesError && <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>{landingChannelGroupRulesError}</div>}
                                        {landingChannelGroupRulesLoading && !landingChannelGroupRules ? (
                                            emptyState(t('Loading rules…', '載入規則中…'))
                                        ) : landingChannelGroupRules && landingChannelGroupRules.length === 0 ? (
                                            <div style={{ color: 'var(--text-tertiary)', fontSize: '0.82rem' }}>
                                                {t('No custom group rules yet for this dimension.', '這個維度目前沒有自訂分組規則。')}
                                            </div>
                                        ) : (
                                            <div style={{ display: 'grid', gap: '8px' }}>
                                                {(landingChannelGroupRules || []).map((rule) => (
                                                    <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '10px 12px', gap: '8px', flexWrap: 'wrap' }}>
                                                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                                                            <span style={badgeStyle('product')}>{rule.group_label}</span>
                                                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                                                {tr(language, CHANNEL_GROUP_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.en, CHANNEL_GROUP_MATCH_TYPE_OPTIONS.find((m) => m.value === rule.match_type)?.zh)}
                                                            </span>
                                                            <code style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{rule.pattern}</code>
                                                            <span style={{ color: 'var(--text-tertiary)', fontSize: '0.76rem' }}>{t('priority', '優先序')} {rule.priority}</span>
                                                        </div>
                                                        {canManageGa4InsightsRules && (
                                                            <button type="button" style={{ ...secondaryButtonStyle, padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => handleDeleteChannelGroupRule(rule.id)}>
                                                                {t('Delete', '刪除')}
                                                            </button>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {canManageGa4InsightsRules ? (
                                            <form onSubmit={handleCreateChannelGroupRule} style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(5, minmax(0, 1fr))' }}>
                                                <input
                                                    type="text"
                                                    value={landingChannelGroupRuleForm.group_label}
                                                    onChange={(event) => setLandingChannelGroupRuleForm((prev) => ({ ...prev, group_label: event.target.value }))}
                                                    placeholder={t('Group name (e.g. Facebook Ads)', '分組名稱（例：Facebook 付費廣告）')}
                                                    style={inputStyle}
                                                />
                                                <select value={landingChannelGroupRuleForm.match_type} onChange={(event) => setLandingChannelGroupRuleForm((prev) => ({ ...prev, match_type: event.target.value }))} style={inputStyle}>
                                                    {CHANNEL_GROUP_MATCH_TYPE_OPTIONS.map((option) => (
                                                        <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                                    ))}
                                                </select>
                                                <input
                                                    type="text"
                                                    value={landingChannelGroupRuleForm.pattern}
                                                    onChange={(event) => setLandingChannelGroupRuleForm((prev) => ({ ...prev, pattern: event.target.value }))}
                                                    placeholder={t('Pattern (e.g. facebook / cpc)', '比對字串（例：facebook / cpc）')}
                                                    style={inputStyle}
                                                />
                                                <input
                                                    type="number"
                                                    min="0"
                                                    value={landingChannelGroupRuleForm.priority}
                                                    onChange={(event) => setLandingChannelGroupRuleForm((prev) => ({ ...prev, priority: event.target.value }))}
                                                    placeholder={t('Priority', '優先序')}
                                                    style={inputStyle}
                                                />
                                                <button type="submit" style={buttonStyle} disabled={landingChannelGroupRuleSaving || !landingChannelGroupRuleForm.group_label.trim() || !landingChannelGroupRuleForm.pattern.trim()}>
                                                    {landingChannelGroupRuleSaving ? t('Saving…', '儲存中…') : t('Add rule', '新增規則')}
                                                </button>
                                            </form>
                                        ) : (
                                            <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                                {t('You do not have permission to manage classification rules.', '您沒有管理分類規則的權限。')}
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={landingSnapshot}
                        kind="landing_page"
                        contextLabel={[
                            t(
                                `Property ${propertyId}; key event ${landingSnapshot?.payload?.key_event || 'all'}; period ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`,
                                `屬性 ${propertyId}；關鍵事件 ${landingSnapshot?.payload?.key_event || '全部'}；期間 ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`
                            ),
                            channelScopeLabel(landingSnapshot?.payload, language, t),
                            categoryScopeLabel(landingCategoryFilter, language, t),
                            compareScopeLabel(landingSnapshot?.payload, t),
                        ].filter(Boolean).join('；')}
                        shareUrlParams={landingCategoryFilter !== 'all' ? { category: landingCategoryFilter } : {}}
                        buildPayload={() => ({
                            key_event: landingSnapshot?.payload?.key_event || null,
                            channel_dimension: landingSnapshot?.payload?.channel_dimension || null,
                            channel_value: landingSnapshot?.payload?.channel_value || null,
                            channel_group: landingSnapshot?.payload?.channel_group || null,
                            // docs/53：改用畫面上已經套用分類篩選後的清單，AI 分析的內容才會
                            // 跟目前選的分類（全部/商品/文章/功能/其他）一致；category_counts
                            // 仍傳完整版，讓 AI 知道這個屬性整體的分類分布。
                            landing_pages: filteredSortedLandingPages,
                            category_counts: landingSnapshot?.payload?.category_counts || {},
                            // docs/54：跟上一期比較——每列已經帶有 *_growth_rate/*_delta_pp/is_new
                            // 欄位，這裡額外補上比較期間，AI 才知道「上一期」具體是哪段日期。
                            compare_enabled: landingSnapshot?.payload?.compare_enabled || false,
                            compare_start_date: landingSnapshot?.payload?.compare_start_date || null,
                            compare_end_date: landingSnapshot?.payload?.compare_end_date || null,
                        })}
                    />
    </>
    );
};

export default LandingPagesTab;
