import React, { useMemo } from 'react';

import {
    ErrorPanel,
    InfoPanel,
    inputStyle,
    primaryButtonStyle,
    secondaryButtonStyle,
    Section,
    t,
} from './ContributionShared';

const GroupEditor = ({
    language,
    campaigns,
    groups,
    editing,
    onEdit,
    onCancel,
    onSave,
    saving,
    saveError,
    onReset,
    resetting,
    resetError,
}) => {
    const campaignsById = useMemo(() => {
        const map = new Map();
        campaigns.forEach((c) => map.set(String(c.campaign_id), c));
        return map;
    }, [campaigns]);

    const draft = editing || groups;

    const allCampaignIds = useMemo(
        () => campaigns.map((c) => String(c.campaign_id)),
        [campaigns]
    );

    const handleMove = (campaignId, targetGroupKey) => {
        const next = (editing || groups).map((g) => ({ ...g, campaign_ids: [...g.campaign_ids] }));
        next.forEach((g) => {
            g.campaign_ids = g.campaign_ids.filter((cid) => cid !== campaignId);
        });
        const target = next.find((g) => g.group_key === targetGroupKey);
        if (target) target.campaign_ids.push(campaignId);
        onEdit(next);
    };

    const handleRename = (groupKey, newName) => {
        const next = (editing || groups).map((g) =>
            g.group_key === groupKey ? { ...g, group_name: newName } : g
        );
        onEdit(next);
    };

    return (
        <Section
            title={t(language, 'Group Editor', '活動分組編輯')}
            subtitle={t(
                language,
                'Move campaigns between groups or rename them, then save. Saved groups become the active set for the next analysis.',
                '拖拉活動到不同組別或重新命名後儲存。儲存後的分組將作為下次分析的主分組。'
            )}
        >
            {saveError && <ErrorPanel message={saveError} />}
            {resetError && <ErrorPanel message={resetError} />}

            {draft.length === 0 && (
                <InfoPanel message={t(language, 'No groups to edit.', '沒有可編輯的分組。')} />
            )}

            <div style={{ display: 'grid', gap: '10px' }}>
                {draft.map((group) => (
                    <div
                        key={group.group_key}
                        style={{
                            padding: '12px 14px',
                            borderRadius: '10px',
                            border: '1px solid var(--glass-border)',
                            background: 'rgba(255,255,255,0.03)',
                        }}
                    >
                        <div
                            style={{
                                display: 'flex',
                                gap: '8px',
                                alignItems: 'center',
                                marginBottom: '8px',
                                flexWrap: 'wrap',
                            }}
                        >
                            <span
                                style={{
                                    fontSize: '0.78rem',
                                    color: 'var(--text-secondary)',
                                    fontWeight: 600,
                                }}
                            >
                                {group.group_key}
                            </span>
                            <input
                                value={group.group_name}
                                onChange={(e) => handleRename(group.group_key, e.target.value)}
                                style={{ ...inputStyle, flex: '1 1 200px' }}
                            />
                            <span
                                style={{
                                    fontSize: '0.72rem',
                                    color: 'var(--text-secondary)',
                                }}
                            >
                                {group.campaign_ids.length} {t(language, 'campaigns', '個活動')}
                            </span>
                        </div>
                        {/* docs/27 任務 4.4：把某組活動全搬走後，明確告知使用者這個
                            空組會在儲存時被移除（handleSaveGroups 送出前已過濾），
                            避免使用者以為卡住、無從得知空組的下場。只在「有未儲存
                            編輯」時顯示——已儲存的分組理論上不會有空組。 */}
                        {editing && group.campaign_ids.length === 0 && (
                            <div
                                style={{
                                    marginBottom: '8px',
                                    padding: '6px 10px',
                                    borderRadius: '8px',
                                    background: 'rgba(245, 158, 11, 0.08)',
                                    border: '1px dashed rgba(245, 158, 11, 0.35)',
                                    color: '#fbbf24',
                                    fontSize: '0.74rem',
                                }}
                            >
                                {t(
                                    language,
                                    'This group has no campaigns left and will be removed when you save.',
                                    '此組已無任何活動，將於儲存時移除。'
                                )}
                            </div>
                        )}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {group.campaign_ids.length === 0 && !editing && (
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                    {t(language, 'No campaigns.', '無活動。')}
                                </span>
                            )}
                            {group.campaign_ids.map((cid) => {
                                const campaign = campaignsById.get(String(cid));
                                return (
                                    <div
                                        key={`${group.group_key}-${cid}`}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '4px 8px',
                                            borderRadius: '999px',
                                            background: 'rgba(59, 130, 246, 0.12)',
                                            color: '#93c5fd',
                                            fontSize: '0.78rem',
                                        }}
                                    >
                                        <span title={campaign?.campaign_name || cid}>
                                            {campaign?.campaign_name || cid}
                                        </span>
                                        <select
                                            value={group.group_key}
                                            onChange={(e) => handleMove(cid, e.target.value)}
                                            style={{
                                                background: 'transparent',
                                                border: 'none',
                                                color: '#bfdbfe',
                                                fontSize: '0.72rem',
                                                cursor: 'pointer',
                                            }}
                                        >
                                            {draft.map((g) => (
                                                <option key={g.group_key} value={g.group_key}>
                                                    → {g.group_key}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            {allCampaignIds.length > 0 && (
                <div
                    style={{
                        marginTop: '12px',
                        fontSize: '0.78rem',
                        color: 'var(--text-secondary)',
                    }}
                >
                    {t(
                        language,
                        'Hint: use the small selector on each campaign chip to move it to another group. Rerun analysis afterwards.',
                        '提示：點選活動徽章上的小選擇器即可移到其他組別，之後再重跑分析。'
                    )}
                </div>
            )}

            <div style={{ marginTop: '14px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                    type="button"
                    onClick={onReset}
                    disabled={resetting || saving}
                    title={t(
                        language,
                        'Clear current groups (including manual edits) and regenerate with the latest auto-grouping rules.',
                        '清除目前分組（含手動編輯）並以最新的自動分組規則重新產生。'
                    )}
                    style={{
                        ...secondaryButtonStyle,
                        marginRight: 'auto',
                        opacity: resetting || saving ? 0.5 : 1,
                    }}
                >
                    {resetting
                        ? t(language, 'Resetting…', '重設中…')
                        : t(language, 'Reset to Auto', '重設為自動分組')}
                </button>
                {editing && (
                    <button type="button" onClick={onCancel} style={secondaryButtonStyle}>
                        {t(language, 'Cancel', '取消')}
                    </button>
                )}
                <button
                    type="button"
                    onClick={onSave}
                    disabled={!editing || saving}
                    style={{
                        ...primaryButtonStyle,
                        opacity: !editing || saving ? 0.5 : 1,
                    }}
                >
                    {saving
                        ? t(language, 'Saving…', '儲存中…')
                        : t(language, 'Save Groups', '儲存分組')}
                </button>
            </div>
        </Section>
    );
};

export default GroupEditor;
