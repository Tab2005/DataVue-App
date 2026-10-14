/**
 * 廣告文案庫「結構」分頁（docs/74 第一節）
 *
 * 行銷活動 → 廣告組合 → 廣告的可展開樹，資料來自 /api/ad-library/tree。
 * 預設全部收合，展開廣告組合時才載入廣告縮圖，避免大帳號一次打上千張圖。
 */
import React, { useEffect, useMemo, useState } from 'react';
import { FiChevronDown, FiChevronRight, FiImage } from 'react-icons/fi';

import { fetchMediaBlobUrl, getTree } from '../../services/adLibraryService';
import {
    MEDIA_TYPE_LABELS,
    OBJECTIVE_LABELS,
    OPTIMIZATION_GOAL_LABELS,
    STATUS_LABELS,
    formatMoney,
    formatNumber,
    label,
    t,
} from './labels';

const STYLES = `
.adlib-tree { display: flex; flex-direction: column; gap: 10px; }
.adlib-node { background: var(--bg-secondary); border: 1px solid var(--glass-border); border-radius: var(--radius-lg, 12px); min-width: 0; }
.adlib-node-head { display: flex; gap: 10px; align-items: flex-start; padding: 12px 14px; width: 100%; background: none; border: none;
  color: inherit; text-align: left; cursor: pointer; font: inherit; }
.adlib-node-head:hover { background: var(--bg-hover); }
.adlib-node-title { font-weight: 700; color: var(--text-primary); overflow-wrap: anywhere; }
.adlib-node-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; align-items: center; }
.adlib-node-children { padding: 0 14px 12px 34px; display: flex; flex-direction: column; gap: 8px; }
@media (max-width: 640px) { .adlib-node-children { padding-left: 14px; } }
.adlib-metrics { display: flex; gap: 14px; flex-wrap: wrap; font-size: 0.78rem; color: var(--text-muted);
  font-variant-numeric: tabular-nums; margin-top: 6px; }
.adlib-metrics strong { color: var(--text-primary); font-weight: 600; margin-left: 4px; }
.adlib-ad-row { display: flex; gap: 12px; padding: 10px; border: 1px solid var(--glass-border); border-radius: var(--radius-md, 8px);
  background: var(--bg-primary); min-width: 0; }
.adlib-ad-thumb { width: 64px; height: 64px; flex-shrink: 0; border-radius: 6px; overflow: hidden; background: var(--bg-secondary);
  display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
.adlib-ad-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.adlib-chip { font-size: 0.72rem; padding: 2px 8px; border-radius: 6px; background: var(--bg-primary); color: var(--text-secondary);
  border: 1px solid var(--glass-border); }
`;

const StatusBadge = ({ status, language }) => {
    if (!status) return null;
    const entry = STATUS_LABELS[status];
    return (
        <span className="adlib-badge" style={status === 'ACTIVE' ? { color: '#16a34a', borderColor: '#16a34a' } : undefined}>
            {entry ? t(language, entry[0], entry[1]) : status}
        </span>
    );
};

const Metrics = ({ metrics, language }) => (
    <div className="adlib-metrics">
        <span>{t(language, 'Spend', '花費')}<strong>{formatMoney(metrics?.spend)}</strong></span>
        <span>{t(language, 'Impr.', '曝光')}<strong>{formatNumber(metrics?.impressions)}</strong></span>
        <span>{t(language, 'Clicks', '點擊')}<strong>{formatNumber(metrics?.clicks)}</strong></span>
        <span>CTR<strong>{(metrics?.ctr || 0).toFixed(2)}%</strong></span>
    </div>
);

const budgetText = (node, language) => {
    const money = (n) => `${node.currency || ''} ${formatMoney(n)}`.trim();
    if (node.daily_budget != null) return t(language, `${money(node.daily_budget)} / day`, `日預算 ${money(node.daily_budget)}`);
    if (node.lifetime_budget != null) return t(language, `${money(node.lifetime_budget)} lifetime`, `總預算 ${money(node.lifetime_budget)}`);
    return null;
};

const GENDER = { male: ['Men', '男性'], female: ['Women', '女性'] };

export const targetingChips = (summary, language) => {
    if (!summary) return [];
    const chips = [];
    if (summary.age_min || summary.age_max) {
        chips.push(`${summary.age_min || 18}–${summary.age_max || '65+'}${t(language, '', ' 歲')}`);
    }
    if (summary.genders?.length) {
        chips.push(summary.genders.map((g) => (GENDER[g] ? t(language, GENDER[g][0], GENDER[g][1]) : g)).join('、'));
    }
    const places = [...(summary.countries || []), ...(summary.regions || []), ...(summary.cities || [])];
    if (places.length) chips.push(places.slice(0, 4).join('、') + (places.length > 4 ? ` +${places.length - 4}` : ''));
    if (summary.advantage_audience) chips.push(t(language, 'Advantage+ audience', 'Advantage+ 受眾'));
    if (summary.interests?.length) {
        chips.push(`${t(language, 'Interests', '興趣')}：${summary.interests.slice(0, 3).join('、')}${summary.interests.length > 3 ? ` +${summary.interests.length - 3}` : ''}`);
    }
    if (summary.custom_audiences?.length) {
        chips.push(`${t(language, 'Audiences', '自訂受眾')}：${summary.custom_audiences.slice(0, 2).join('、')}${summary.custom_audiences.length > 2 ? ` +${summary.custom_audiences.length - 2}` : ''}`);
    }
    if (summary.excluded_custom_audiences?.length) {
        chips.push(`${t(language, 'Excluded', '排除')}：${summary.excluded_custom_audiences.length}`);
    }
    chips.push(summary.publisher_platforms?.length
        ? summary.publisher_platforms.join('、')
        : t(language, 'Automatic placements', '自動版位'));
    return chips;
};

const Thumb = ({ thumbnail }) => {
    const [src, setSrc] = useState(null);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setSrc(null);
        setFailed(false);
        if (!thumbnail?.asset_id) return undefined;
        const controller = new AbortController();
        let objectUrl = null;
        fetchMediaBlobUrl(thumbnail.asset_id, controller.signal)
            .then((url) => { objectUrl = url; setSrc(url); })
            .catch((err) => { if (err.name !== 'AbortError') setFailed(true); });
        return () => {
            controller.abort();
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [thumbnail?.asset_id]);

    const displaySrc = src || (!thumbnail?.asset_id && thumbnail?.fb_url) || null;
    return (
        <div className="adlib-ad-thumb">
            {displaySrc && !failed ? <img src={displaySrc} alt="" loading="lazy" onError={() => setFailed(true)} /> : <FiImage size={22} />}
        </div>
    );
};

const AdRow = ({ ad, language }) => {
    const mediaType = MEDIA_TYPE_LABELS[ad.media_type];
    return (
        <div className="adlib-ad-row">
            <Thumb thumbnail={ad.thumbnail} />
            <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem', overflowWrap: 'anywhere' }}>
                        {ad.name || ad.ad_id}
                    </span>
                    <StatusBadge status={ad.effective_status} language={language} />
                    {mediaType && <span className="adlib-badge">{t(language, mediaType[0], mediaType[1])}</span>}
                    {ad.variant_count > 1 && (
                        <span className="adlib-badge">{t(language, `${ad.variant_count} variants`, `${ad.variant_count} 組版本`)}</span>
                    )}
                </div>
                {ad.headline && <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 4 }}>{ad.headline}</div>}
                {ad.primary_text && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                        {ad.primary_text}
                    </div>
                )}
                <Metrics metrics={ad.metrics} language={language} />
            </div>
        </div>
    );
};

const MissingSettings = ({ language }) => (
    <span className="adlib-badge" title={t(language, 'Fetch again to load settings', '重新抓取後即可看到設定')}>
        {t(language, 'Settings not fetched', '設定未抓取')}
    </span>
);

const AdsetNode = ({ adset, language, open, onToggle }) => {
    const budget = budgetText(adset, language);
    return (
        <div className="adlib-node" style={{ background: 'var(--bg-primary)' }}>
            <button type="button" className="adlib-node-head" onClick={onToggle} aria-expanded={open}>
                {open ? <FiChevronDown style={{ marginTop: 3, flexShrink: 0 }} /> : <FiChevronRight style={{ marginTop: 3, flexShrink: 0 }} />}
                <div style={{ minWidth: 0, flex: 1 }}>
                    <div className="adlib-node-title" style={{ fontSize: '0.92rem' }}>
                        {adset.name || adset.adset_id || t(language, 'Ads without ad set', '未歸屬廣告組合的廣告')}
                    </div>
                    <div className="adlib-node-meta">
                        {!adset.settings_available && <MissingSettings language={language} />}
                        <StatusBadge status={adset.effective_status} language={language} />
                        {adset.optimization_goal && (
                            <span className="adlib-badge">
                                {t(language, 'Optimize for ', '最佳化：')}{label(OPTIMIZATION_GOAL_LABELS, adset.optimization_goal, language)}
                            </span>
                        )}
                        {budget && <span className="adlib-badge">{budget}</span>}
                        {adset.is_dynamic_creative && <span className="adlib-badge">{t(language, 'Dynamic creative', '動態素材')}</span>}
                        <span className="adlib-badge">{t(language, `${adset.ads.length} ads`, `${adset.ads.length} 則廣告`)}</span>
                    </div>
                    {adset.settings_available && (
                        <div className="adlib-node-meta">
                            {targetingChips(adset.targeting_summary, language).map((chip) => (
                                <span key={chip} className="adlib-chip">{chip}</span>
                            ))}
                        </div>
                    )}
                    <Metrics metrics={adset.metrics} language={language} />
                </div>
            </button>
            {open && (
                <div className="adlib-node-children">
                    {adset.ads.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{t(language, 'No ads fetched.', '沒有抓到廣告。')}</div>
                    )}
                    {adset.ads.map((ad) => <AdRow key={ad.id} ad={ad} language={language} />)}
                </div>
            )}
        </div>
    );
};

const nodeKey = (prefix, node, index) => `${prefix}:${node.id || node.campaign_id || node.adset_id || `i${index}`}`;

const CampaignNode = ({ campaign, index, language, openKeys, toggle }) => {
    const key = nodeKey('c', campaign, index);
    const open = openKeys.has(key);
    const budget = budgetText(campaign, language);
    const adCount = campaign.adsets.reduce((n, s) => n + s.ads.length, 0);
    return (
        <div className="adlib-node">
            <button type="button" className="adlib-node-head" onClick={() => toggle(key)} aria-expanded={open}>
                {open ? <FiChevronDown style={{ marginTop: 3, flexShrink: 0 }} /> : <FiChevronRight style={{ marginTop: 3, flexShrink: 0 }} />}
                <div style={{ minWidth: 0, flex: 1 }}>
                    <div className="adlib-node-title">
                        {campaign.name || campaign.campaign_id || t(language, 'Ads without campaign', '未歸屬行銷活動的廣告')}
                    </div>
                    <div className="adlib-node-meta">
                        {!campaign.settings_available && <MissingSettings language={language} />}
                        <StatusBadge status={campaign.effective_status} language={language} />
                        {campaign.objective && <span className="adlib-badge">{label(OBJECTIVE_LABELS, campaign.objective, language)}</span>}
                        {campaign.settings_available && (
                            <span className="adlib-badge">
                                {campaign.budget_level === 'campaign'
                                    ? t(language, 'Campaign budget', '行銷活動預算')
                                    : t(language, 'Ad set budget', '廣告組合預算')}
                            </span>
                        )}
                        {budget && <span className="adlib-badge">{budget}</span>}
                        <span className="adlib-badge">
                            {t(language, `${campaign.adsets.length} ad sets · ${adCount} ads`, `${campaign.adsets.length} 個廣告組合 · ${adCount} 則廣告`)}
                        </span>
                    </div>
                    <Metrics metrics={campaign.metrics} language={language} />
                </div>
            </button>
            {open && (
                <div className="adlib-node-children">
                    {campaign.adsets.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{t(language, 'No ad sets fetched.', '沒有抓到廣告組合。')}</div>
                    )}
                    {campaign.adsets.map((adset, i) => {
                        const adsetKey = nodeKey(`${key}/s`, adset, i);
                        return (
                            <AdsetNode key={adsetKey} adset={adset} language={language}
                                       open={openKeys.has(adsetKey)} onToggle={() => toggle(adsetKey)} />
                        );
                    })}
                </div>
            )}
        </div>
    );
};

const StructureView = ({ accountId, status, language, reloadKey, onError }) => {
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loaded, setLoaded] = useState(false);
    const [openKeys, setOpenKeys] = useState(() => new Set());

    useEffect(() => {
        if (!accountId) return undefined;
        let cancelled = false;
        setLoading(true);
        getTree({ accountId, status })
            .then((res) => {
                if (cancelled) return;
                setCampaigns(res.campaigns || []);
                setLoaded(true);
            })
            .catch((err) => !cancelled && onError?.(err.message))
            .finally(() => !cancelled && setLoading(false));
        return () => { cancelled = true; };
    }, [accountId, status, reloadKey, onError]);

    useEffect(() => { setOpenKeys(new Set()); }, [accountId]);

    const totals = useMemo(() => {
        let adsets = 0;
        let ads = 0;
        let missing = false;
        campaigns.forEach((c) => {
            adsets += c.adsets.length;
            if (!c.settings_available) missing = true;
            c.adsets.forEach((s) => {
                ads += s.ads.length;
                if (!s.settings_available) missing = true;
            });
        });
        return { adsets, ads, missing };
    }, [campaigns]);

    const toggle = (key) => setOpenKeys((prev) => {
        const next = new Set(prev);
        if (next.has(key)) next.delete(key); else next.add(key);
        return next;
    });
    const expandCampaigns = () => setOpenKeys(new Set(campaigns.map((c, i) => nodeKey('c', c, i))));

    return (
        <>
            <style>{STYLES}</style>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    {t(language,
                        `${campaigns.length} campaigns · ${totals.adsets} ad sets · ${totals.ads} ads`,
                        `${campaigns.length} 個行銷活動 · ${totals.adsets} 個廣告組合 · ${totals.ads} 則廣告`)}
                </span>
                <button type="button" className="adlib-btn" onClick={expandCampaigns} disabled={!campaigns.length}>
                    {t(language, 'Expand campaigns', '展開所有行銷活動')}
                </button>
                <button type="button" className="adlib-btn" onClick={() => setOpenKeys(new Set())} disabled={!openKeys.size}>
                    {t(language, 'Collapse all', '全部收合')}
                </button>
            </div>

            {totals.missing && (
                <div role="status" style={{
                    padding: '10px 14px', borderRadius: 8, marginBottom: 12, fontSize: '0.88rem',
                    border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', background: 'var(--bg-secondary)',
                }}>
                    {t(language,
                        'Some campaigns or ad sets have no settings yet. Fetch from Facebook again to load them.',
                        '部分行銷活動或廣告組合尚未抓到設定，請重新從 Facebook 抓取一次。')}
                </div>
            )}

            {loaded && !loading && campaigns.length === 0 && (
                <div role="status" style={{
                    padding: '10px 14px', borderRadius: 8, fontSize: '0.88rem',
                    border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', background: 'var(--bg-secondary)',
                }}>
                    {status
                        ? t(language, 'No campaigns match this status.', '沒有符合此狀態的行銷活動。')
                        : t(language, 'No data yet. Click "Fetch from Facebook".', '尚無資料，請按「從 Facebook 重新抓取」。')}
                </div>
            )}

            <div className="adlib-tree" aria-busy={loading} style={{ opacity: loading ? 0.6 : 1 }}>
                {campaigns.map((campaign, i) => (
                    <CampaignNode key={nodeKey('c', campaign, i)} campaign={campaign} index={i} language={language}
                                  openKeys={openKeys} toggle={toggle} />
                ))}
            </div>
        </>
    );
};

export default StructureView;
