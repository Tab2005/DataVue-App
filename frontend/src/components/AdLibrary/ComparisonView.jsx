/**
 * 廣告文案庫「比對」分頁（docs/74 第二節）
 *
 * 在同一廣告組合（或行銷活動）內，把廣告依文案／素材指紋分組：
 *   - 素材測試：文案固定，比較不同素材
 *   - 文案測試：素材固定，比較不同文案
 *   - 重複投放：文案與素材都相同的多則廣告
 * 成效為廣告層級數字，只是固定一個變因後的比較，頁面上一併顯示此前提。
 */
import React, { useEffect, useState } from 'react';
import { FiCpu } from 'react-icons/fi';

import { getComparisons } from '../../services/adLibraryService';
import { MEDIA_TYPE_LABELS, formatMoney, formatNumber, t } from './labels';
import { Metrics } from './StructureView';
import Thumb from './Thumb';

const GROUPS_PER_PAGE = 20;
// 曝光太少的變體不標「CTR 最高」，避免小樣本誤導
export const MIN_IMPRESSIONS_FOR_BEST = 1000;

const RELATION_LABELS = {
    media_test: ['Media test', '素材測試'],
    copy_test: ['Copy test', '文案測試'],
    duplicate: ['Duplicates', '重複投放'],
};

const RELATION_HINTS = {
    media_test: ['Same copy, different media', '文案相同，比較不同素材'],
    copy_test: ['Same media, different copy', '素材相同，比較不同文案'],
    duplicate: ['Same copy and media', '文案與素材都相同'],
};

const STYLES = `
.adlib-cmp-group { background: var(--bg-secondary); border: 1px solid var(--glass-border); border-radius: var(--radius-lg, 12px);
  padding: 14px; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.adlib-cmp-variants { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
@media (max-width: 640px) { .adlib-cmp-variants { grid-template-columns: 1fr; } }
.adlib-cmp-variant { border: 1px solid var(--glass-border); border-radius: var(--radius-md, 8px); background: var(--bg-primary);
  padding: 10px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.adlib-cmp-best { border-color: #16a34a; }
.adlib-cmp-text { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 0.85rem; color: var(--text-primary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.adlib-cmp-fixed { display: flex; gap: 10px; align-items: flex-start; padding: 10px; border-radius: var(--radius-md, 8px);
  background: var(--bg-primary); border: 1px dashed var(--glass-border); min-width: 0; }
`;

const CopyPreview = ({ preview, language }) => {
    const text = preview?.primary_texts?.[0];
    const headline = preview?.headlines?.[0];
    const extra = Math.max((preview?.primary_texts?.length || 0) - 1, 0);
    return (
        <div style={{ minWidth: 0 }}>
            {headline && <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: 2 }}>{headline}</div>}
            {text
                ? <div className="adlib-cmp-text">{text}</div>
                : <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{t(language, 'No primary text', '無主要文字')}</div>}
            {extra > 0 && (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 2 }}>
                    {t(language, `+${extra} more variants`, `另有 ${extra} 段文案`)}
                </div>
            )}
        </div>
    );
};

const MediaPreview = ({ preview, language, size = 96 }) => {
    const mediaType = MEDIA_TYPE_LABELS[preview?.media_type];
    return (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Thumb thumbnail={preview?.thumbnail} size={size} />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {mediaType ? t(language, mediaType[0], mediaType[1]) : preview?.media_type}
                {preview?.media_count > 1 && <div>{t(language, `${preview.media_count} items`, `${preview.media_count} 個素材`)}</div>}
            </div>
        </div>
    );
};

const AdList = ({ ads, showAdset, language }) => (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {ads.map((ad) => (
            <li key={ad.id} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', overflowWrap: 'anywhere' }}>
                {ad.name || ad.ad_id}
                {showAdset && ad.adset_name && <span style={{ color: 'var(--text-muted)' }}> · {ad.adset_name}</span>}
                <span style={{ color: 'var(--text-muted)' }}>
                    {' '}· {t(language, 'spend', '花費')} {formatMoney(ad.metrics?.spend)} · {formatNumber(ad.metrics?.impressions)} {t(language, 'impr.', '曝光')}
                </span>
            </li>
        ))}
    </ul>
);

export const bestVariantKey = (variants) => {
    const eligible = variants.filter((v) => (v.metrics?.impressions || 0) >= MIN_IMPRESSIONS_FOR_BEST);
    if (eligible.length < 2) return null;
    return eligible.reduce((best, v) => (v.metrics.ctr > best.metrics.ctr ? v : best)).key;
};

const GroupCard = ({ group, scope, language, onFilterKey, onAnalyzeCampaign }) => {
    const [en, zh] = RELATION_LABELS[group.relation];
    const [hintEn, hintZh] = RELATION_HINTS[group.relation];
    const best = group.relation === 'duplicate' ? null : bestVariantKey(group.variants);
    const showAdset = scope === 'campaign';
    const fixed = group.fixed;
    const campaignId = group.scope.level === 'campaign' ? group.scope.id : group.scope.campaign_id;
    const campaignName = group.scope.level === 'campaign' ? group.scope.name : group.scope.campaign_name;

    return (
        <article className="adlib-cmp-group">
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="adlib-badge" style={{ color: 'var(--accent-primary)', borderColor: 'var(--accent-primary)' }}>
                    {t(language, en, zh)}
                </span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
                    {group.scope.name || group.scope.id}
                </span>
                {group.scope.campaign_name && (
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{group.scope.campaign_name}</span>
                )}
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                    {t(language, 'Total spend', '總花費')} {formatMoney(group.metrics?.spend)}
                </span>
            </div>

            <div className="adlib-cmp-fixed">
                <span className="adlib-chip" style={{ flexShrink: 0 }}>
                    {fixed.kind === 'copy' && t(language, 'Fixed copy', '固定文案')}
                    {fixed.kind === 'media' && t(language, 'Fixed media', '固定素材')}
                    {fixed.kind === 'both' && t(language, hintEn, hintZh)}
                </span>
                {fixed.kind === 'copy' && <CopyPreview preview={fixed.preview} language={language} />}
                {fixed.kind === 'media' && <MediaPreview preview={fixed.preview} language={language} size={64} />}
                {fixed.kind === 'both' && (
                    <div style={{ display: 'flex', gap: 10, minWidth: 0 }}>
                        <MediaPreview preview={fixed.preview} language={language} size={64} />
                        <CopyPreview preview={fixed.preview} language={language} />
                    </div>
                )}
            </div>

            <div className="adlib-cmp-variants">
                {group.variants.map((variant, i) => (
                    <div key={variant.key} className={`adlib-cmp-variant ${variant.key === best ? 'adlib-cmp-best' : ''}`}>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                            {group.relation !== 'duplicate' && (
                                <span className="adlib-badge">{t(language, `Variant ${i + 1}`, `版本 ${i + 1}`)}</span>
                            )}
                            <span className="adlib-badge">{t(language, `${variant.ads.length} ads`, `${variant.ads.length} 則廣告`)}</span>
                            {variant.key === best && (
                                <span className="adlib-badge" style={{ color: '#16a34a', borderColor: '#16a34a' }}>
                                    {t(language, 'Highest CTR', 'CTR 最高')}
                                </span>
                            )}
                        </div>
                        {group.relation === 'media_test' && <MediaPreview preview={variant.preview} language={language} />}
                        {group.relation === 'copy_test' && <CopyPreview preview={variant.preview} language={language} />}
                        <Metrics metrics={variant.metrics} language={language} />
                        <AdList ads={variant.ads} showAdset={showAdset} language={language} />
                    </div>
                ))}
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {fixed.kind !== 'both' && (
                    <button type="button" className="adlib-btn"
                            onClick={() => onFilterKey({ type: fixed.kind === 'copy' ? 'copy' : 'media', key: fixed.key })}>
                        {fixed.kind === 'copy'
                            ? t(language, 'All ads with this copy', '查看所有使用此文案的廣告')
                            : t(language, 'All ads with this media', '查看所有使用此素材的廣告')}
                    </button>
                )}
                {onAnalyzeCampaign && campaignId && (
                    <button type="button" className="adlib-btn"
                            onClick={() => onAnalyzeCampaign({ campaign_id: campaignId, name: campaignName })}>
                        <FiCpu size={14} />
                        {t(language, 'AI analysis of this campaign', 'AI 分析此行銷活動')}
                    </button>
                )}
            </div>
        </article>
    );
};

const ComparisonView = ({ accountId, language, reloadKey, onError, onFilterKey, onAnalyzeCampaign }) => {
    const [scope, setScope] = useState('adset');
    const [relation, setRelation] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [visible, setVisible] = useState(GROUPS_PER_PAGE);

    useEffect(() => {
        if (!accountId) return undefined;
        let cancelled = false;
        setLoading(true);
        getComparisons({ accountId, scope, relation })
            .then((res) => { if (!cancelled) { setData(res); setVisible(GROUPS_PER_PAGE); } })
            .catch((err) => !cancelled && onError?.(err.message))
            .finally(() => !cancelled && setLoading(false));
        return () => { cancelled = true; };
    }, [accountId, scope, relation, reloadKey, onError]);

    const counts = data?.counts || {};
    const groups = data?.groups || [];
    const coverage = data?.coverage;

    return (
        <>
            <style>{STYLES}</style>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                <select className="adlib-input" value={scope} onChange={(e) => setScope(e.target.value)}
                        aria-label={t(language, 'Compare within', '比對範圍')}>
                    <option value="adset">{t(language, 'Within each ad set', '同一廣告組合內')}</option>
                    <option value="campaign">{t(language, 'Within each campaign', '同一行銷活動內')}</option>
                </select>
                {[['', 'All', '全部'], ...Object.entries(RELATION_LABELS).map(([k, [en, zh]]) => [k, en, zh])].map(([key, en, zh]) => (
                    <button key={key || 'all'} type="button" className="adlib-btn" aria-pressed={relation === key}
                            onClick={() => setRelation(key)}
                            style={relation === key ? { borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' } : undefined}>
                        {t(language, en, zh)}
                        {key && data && ` ${counts[key] ?? 0}`}
                    </button>
                ))}
            </div>

            {data?.note && (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>{data.note}</div>
            )}
            {coverage?.without_media_key > 0 && (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                    {t(language,
                        `${coverage.without_media_key} of ${coverage.ads} ads have media that can't be identified (e.g. post-based ads) and are left out of media comparisons.`,
                        `${coverage.ads} 則廣告中有 ${coverage.without_media_key} 則的素材無法識別（例如以既有貼文投放），未納入素材比對。`)}
                </div>
            )}

            {data && !loading && groups.length === 0 && (
                <div role="status" style={{
                    padding: '10px 14px', borderRadius: 8, fontSize: '0.88rem',
                    border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', background: 'var(--bg-secondary)',
                }}>
                    {coverage?.ads
                        ? t(language,
                            'No ads share copy or media within the same scope. Try comparing within each campaign.',
                            '同範圍內沒有共用文案或素材的廣告。可以試試改成「同一行銷活動內」比對。')
                        : t(language, 'No data yet. Click "Fetch from Facebook".', '尚無資料，請按「從 Facebook 重新抓取」。')}
                </div>
            )}

            <div aria-busy={loading} style={{ display: 'flex', flexDirection: 'column', gap: 12, opacity: loading ? 0.6 : 1 }}>
                {groups.slice(0, visible).map((group) => (
                    <GroupCard key={`${group.relation}:${group.scope.id}:${group.fixed.key}`} group={group}
                               scope={data.scope} language={language} onFilterKey={onFilterKey}
                               onAnalyzeCampaign={onAnalyzeCampaign} />
                ))}
            </div>

            {groups.length > visible && (
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16 }}>
                    <button type="button" className="adlib-btn" onClick={() => setVisible((v) => v + GROUPS_PER_PAGE)}>
                        {t(language, `Show more (${groups.length - visible} left)`, `顯示更多（還有 ${groups.length - visible} 組）`)}
                    </button>
                </div>
            )}
        </>
    );
};

export default ComparisonView;
