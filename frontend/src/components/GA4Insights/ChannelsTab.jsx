import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import {
    AIInsightNote,
    ATTRIBUTION_MODEL_LABELS,
    CHANNEL_DIMENSION_OPTIONS,
    CHANNEL_TAG_LABELS,
    badgeStyle,
    baseCardStyle,
    channelClosingLabel,
    channelDimensionLabel,
    emptyState,
    fmtNumber,
    fmtPct,
    inputStyle,
    secondaryButtonStyle,
    tr,
} from './GA4InsightsShared';

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
    DaySelector,
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
                                <DaySelector value={channelsDays} onChange={(d) => { setChannelsDays(d); loadChannels(propertyId, d, channelsDimension); }} />
                            </div>
                        </div>
                        {channelsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{channelsError}</div>}
                        {channelsSnapshot?.payload?.truncated && (
                            <div style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '10px' }}>
                                {t(
                                    `Showing top 20 of ${channelsSnapshot.payload.total_row_count} (ranked by assisting + closing conversions).`,
                                    `顯示前 20 名（依開發+收單轉換數排序），共 ${channelsSnapshot.payload.total_row_count} 個項目。`
                                )}
                            </div>
                        )}
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
                                <div style={{ overflowX: 'auto', marginTop: '12px' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                                <th style={{ padding: '6px' }}>{channelDimensionLabel(channelsSnapshot.payload.dimension, language)}</th>
                                                <th style={{ padding: '6px' }}>{t('Assisting', '開發')}</th>
                                                <th style={{ padding: '6px' }}>{channelClosingLabel(channelsSnapshot?.payload?.attribution_model, language)}</th>
                                                <th style={{ padding: '6px' }}>{t('Ratio', '比例')}</th>
                                                <th style={{ padding: '6px' }}>{t('Tag', '標籤')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {channelsSnapshot.payload.channels.map((row) => (
                                                <tr key={row.channel} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.channel}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.assisting_conversions)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.closing_conversions)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{row.ratio != null ? row.ratio.toFixed(2) : '--'}</td>
                                                    <td style={{ padding: '6px' }}>
                                                        <span style={badgeStyle(row.tag)}>
                                                            {tr(language, CHANNEL_TAG_LABELS[row.tag]?.en, CHANNEL_TAG_LABELS[row.tag]?.zh) || row.tag}
                                                        </span>
                                                        {channelsSnapshot.payload.total_closing_conversions > 0 && (
                                                            <span
                                                                style={{ color: 'var(--text-secondary)', fontSize: '0.74rem', marginLeft: '6px' }}
                                                                title={t(
                                                                    'Share of this channel\'s closing conversions out of all channels\' total.',
                                                                    '這個渠道的收單轉換數，佔全部渠道收單轉換數加總的比例。'
                                                                )}
                                                            >
                                                                ({t('share', '佔收單')} {fmtPct(row.closing_conversions / channelsSnapshot.payload.total_closing_conversions)})
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
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
