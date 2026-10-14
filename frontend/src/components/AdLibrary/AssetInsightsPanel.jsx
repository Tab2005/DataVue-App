/**
 * 動態素材廣告的元件成效（docs/74 第 3 階段）
 *
 * Meta 依元件拆分的成效（/ads/{id}/asset-insights），可直接比較同一則廣告內
 * 各段文案、各張素材的表現。曝光 1,000 以上且至少兩個元件時才標「CTR 最高」。
 */
import React, { useEffect, useState } from 'react';

import { getAdAssetInsights } from '../../services/adLibraryService';
import { MIN_IMPRESSIONS_FOR_BEST } from './ComparisonView';
import { formatMoney, formatNumber, t } from './labels';
import Thumb from './Thumb';

const KIND_LABELS = {
    primary_text: ['Primary text', '主要文字'],
    headline: ['Headline', '標題'],
    description: ['Description', '說明'],
    image: ['Image', '圖片'],
    video: ['Video', '影片'],
};

const TEXT_STYLE = {
    whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.5,
    display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
};

export const bestEntryId = (entries) => {
    const eligible = entries.filter((e) => (e.impressions || 0) >= MIN_IMPRESSIONS_FOR_BEST);
    if (eligible.length < 2) return null;
    return eligible.reduce((best, e) => (e.ctr > best.ctr ? e : best)).content_id;
};

const AssetInsightsPanel = ({ itemId, language }) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        setData(null);
        setError(null);
        getAdAssetInsights(itemId)
            .then((res) => !cancelled && setData(res))
            .catch((err) => !cancelled && setError(err.message));
        return () => { cancelled = true; };
    }, [itemId]);

    if (error) return <div role="alert" style={{ color: 'var(--text-error)', fontSize: '0.82rem' }}>{error}</div>;
    if (!data) return <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{t(language, 'Loading…', '載入中…')}</div>;

    const kinds = Object.keys(data.entries || {});
    if (kinds.length === 0) {
        return (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.5 }}>
                {t(language,
                    'No per-asset results yet. Fetch from Facebook again (only the 100 highest-spend dynamic ads are analyzed).',
                    '尚無元件成效。請重新從 Facebook 抓取（只分析花費最高的 100 則動態素材廣告）。')}
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {kinds.map((kind) => {
                const entries = data.entries[kind];
                const best = bestEntryId(entries);
                const [en, zh] = KIND_LABELS[kind] || [kind, kind];
                return (
                    <section key={kind}>
                        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>
                            {t(language, en, zh)}
                        </div>
                        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {entries.map((e) => (
                                <li key={e.content_id} style={{
                                    display: 'flex', gap: 8, alignItems: 'flex-start', padding: 8, borderRadius: 6,
                                    border: `1px solid ${e.content_id === best ? '#16a34a' : 'var(--glass-border)'}`,
                                    background: 'var(--bg-primary)', minWidth: 0,
                                }}>
                                    {(kind === 'image' || kind === 'video') && (
                                        <Thumb thumbnail={e.asset_id
                                            ? { asset_id: e.asset_id, kind: kind === 'video' ? 'video_thumbnail' : 'image' }
                                            : null} size={44} />
                                    )}
                                    <div style={{ minWidth: 0, flex: 1 }}>
                                        {e.text_value && (
                                            <div style={TEXT_STYLE}>{e.text_value}</div>
                                        )}
                                        {kind === 'video' && !e.text_value && (
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID {e.video_id}</div>
                                        )}
                                        <div className="adlib-metrics">
                                            <span>{t(language, 'Impr.', '曝光')}<strong>{formatNumber(e.impressions)}</strong></span>
                                            <span>CTR<strong>{(e.ctr || 0).toFixed(2)}%</strong></span>
                                            <span>{t(language, 'Spend', '花費')}<strong>{formatMoney(e.spend)}</strong></span>
                                            {e.content_id === best && (
                                                <span style={{ color: '#16a34a', fontWeight: 600 }}>{t(language, 'Highest CTR', 'CTR 最高')}</span>
                                            )}
                                        </div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </section>
                );
            })}
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{data.note}</div>
        </div>
    );
};

export default AssetInsightsPanel;
