import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import {
    AIInsightNote,
    DaySelector,
    ATTRIBUTION_MODEL_LABELS,
    CHANNEL_DIMENSION_OPTIONS,
    badgeStyle,
    baseCardStyle,
    channelClosingLabel,
    channelDimensionLabel,
    emptyState,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';
// docs/64：表格主體與警示橫幅跟分享頁共用同一份實作。
import { ChannelsTable, PayloadWarnings } from './GA4InsightsTables';

const ChannelsTab = ({
    language,
    t,
    propertyId,
    channelsDimension,
    setChannelsDimension,
    channelsDays,
    setChannelsDays,
    loadChannels,
    channelsError,
    channelsSnapshot,
    channelsLoading,
}) => (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Assist vs. close channels', '渠道助攻/主攻對照')}</div>
                                    {ATTRIBUTION_MODEL_LABELS[channelsSnapshot?.payload?.attribution_model] && (
                                        <span
                                            style={badgeStyle(channelsSnapshot.payload.attribution_model)}
                                            title={tr(
                                                language,
                                                ATTRIBUTION_MODEL_LABELS[channelsSnapshot.payload.attribution_model].tooltip.en,
                                                ATTRIBUTION_MODEL_LABELS[channelsSnapshot.payload.attribution_model].tooltip.zh
                                            )}
                                        >
                                            {tr(
                                                language,
                                                ATTRIBUTION_MODEL_LABELS[channelsSnapshot.payload.attribution_model].en,
                                                ATTRIBUTION_MODEL_LABELS[channelsSnapshot.payload.attribution_model].zh
                                            )}
                                        </span>
                                    )}
                                </div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                    {t(
                                        'First-touch vs. last-touch conversions by channel. For deeper incremental contribution, see the Contribution Analysis page.',
                                        '首次接觸 vs 最後接觸轉換的渠道對照。想看更深入的增量貢獻，請至貢獻分析頁。'
                                    )}
                                </div>
                                {ATTRIBUTION_MODEL_LABELS[channelsSnapshot?.payload?.attribution_model] && (
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>
                                        {t(
                                            '"Assisting" is always a hard first-touch count. "Closing" reflects this property\'s reporting attribution model — hover the badge above for details.',
                                            '「開發」永遠是硬計數(使用者第一次造訪的管道)；「收單」的意義依帳戶的報表歸因模式而定，詳見上方 badge 提示。'
                                        )}
                                    </div>
                                )}
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>
                                    {t(
                                        'The tag reflects this channel\'s internal assist/close role — not how much it matters to total orders. Check the share (%) column for that.',
                                        '標籤講的是這個渠道「開發 vs 收單」的內部角色，不是它在全站訂單裡的重要性——量級請看佔比欄位。'
                                    )}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                                <select
                                    value={channelsDimension}
                                    onChange={(event) => {
                                        const nextDimension = event.target.value;
                                        setChannelsDimension(nextDimension);
                                        loadChannels(propertyId, channelsDays, nextDimension);
                                    }}
                                    style={{ ...inputStyle, width: 'auto', padding: '8px 10px' }}
                                >
                                    {CHANNEL_DIMENSION_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                    ))}
                                </select>
                                <DaySelector language={language} value={channelsDays} onChange={(d) => { setChannelsDays(d); loadChannels(propertyId, d, channelsDimension); }} />
                            </div>
                        </div>
                        {channelsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{channelsError}</div>}
                        <PayloadWarnings t={t} payload={channelsSnapshot?.payload} kind="daily_channel" />
                        {channelsLoading && !channelsSnapshot ? (
                            emptyState(t('Loading channels…', '載入渠道資料中…'))
                        ) : channelsSnapshot?.payload?.channels?.length ? (
                            <>
                                <div className="ga4-insights-chart-root">
                                    <ResponsiveContainer width="100%" height={Math.max(220, channelsSnapshot.payload.channels.length * 40)}>
                                        <BarChart data={channelsSnapshot.payload.channels} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                                            <CartesianGrid stroke="var(--viz-grid)" horizontal={false} />
                                            <XAxis type="number" tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={{ stroke: 'var(--viz-axis)' }} tickLine={false} />
                                            <YAxis type="category" dataKey="channel" width={140} tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <Tooltip contentStyle={{ background: 'var(--viz-tooltip-bg)', border: '1px solid var(--viz-tooltip-border)', borderRadius: 8, fontSize: '0.8rem' }} />
                                            <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'var(--viz-text)' }} />
                                            <Bar dataKey="assisting_conversions" name={t('Assisting (first-touch)', '開發（首次接觸）')} fill="var(--viz-series-1)" radius={[0, 4, 4, 0]} />
                                            <Bar dataKey="closing_conversions" name={channelClosingLabel(channelsSnapshot?.payload?.attribution_model, language)} fill="var(--viz-series-2)" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                                <div style={{ marginTop: '12px' }}>
                                    <ChannelsTable
                                        language={language}
                                        t={t}
                                        payload={channelsSnapshot.payload}
                                        rows={channelsSnapshot.payload.channels}
                                    />
                                </div>
                            </>
                        ) : (
                            emptyState(t('No channel data.', '暫無渠道資料。'))
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={channelsSnapshot}
                        kind="daily_channel"
                        contextLabel={t(
                            `Property ${propertyId}; dimension ${channelDimensionLabel(channelsSnapshot?.payload?.dimension || channelsDimension, 'en')}; period ${channelsSnapshot?.payload?.start_date || ''} ~ ${channelsSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；維度 ${channelDimensionLabel(channelsSnapshot?.payload?.dimension || channelsDimension, 'zh')}；期間 ${channelsSnapshot?.payload?.start_date || ''} ~ ${channelsSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({
                            dimension: channelsSnapshot?.payload?.dimension,
                            channels: channelsSnapshot?.payload?.channels || [],
                            attribution_model: channelsSnapshot?.payload?.attribution_model,
                        })}
                    />
    </>
);

export default ChannelsTab;
