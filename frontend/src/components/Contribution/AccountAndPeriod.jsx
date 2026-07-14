import React from 'react';

import {
    computePeriod,
    InfoPanel,
    primaryButtonStyle,
    secondaryButtonStyle,
    Section,
    selectStyle,
    t,
} from './ContributionShared';

const AccountAndPeriod = ({
    language,
    isMobile,
    accountId,
    onAccountChange,
    onRefreshCampaigns,
    refreshing,
    campaignsCount,
    periodDays,
    onPeriodChange,
    onSubmit,
    submitting,
    canSubmit,
    accountList,
    loadingAccounts,
    dataCoverage,
}) => {
    // docs/27 任務 6.1：分析請求區間若超出實際快取涵蓋範圍，後端會自動
    // clamp 到快取實際涵蓋範圍（並在結果附加說明），不會把缺口日子當假的
    // 零花費資料餵進模型。這裡只是先讓使用者知道「選了 N 天但可能沒那麼
    // 多可用資料」，不是唯一把關點，也不因此停用送出按鈕。
    const requestedStart = accountId ? computePeriod(periodDays).dateStart : null;
    const coverageInsufficient = Boolean(
        dataCoverage?.first_date && requestedStart && requestedStart < dataCoverage.first_date
    );
    return (
        <Section
            title={t(language, 'Ad Account & Period', '廣告帳戶與分析期間')}
            subtitle={t(
                language,
                'Pick an ad account and analysis period, then run MMM. Defaults to the most recent 180 days.',
                '選擇廣告帳戶與分析期間後開始 MMM 分析。預設為最近 180 天。'
            )}
        >
            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: isMobile ? '1fr' : '1.4fr 1fr auto',
                    gap: '12px',
                    alignItems: 'flex-end',
                }}
            >
                <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {t(language, 'Ad Account', '廣告帳戶')}
                    </span>
                    <select
                        value={accountId}
                        onChange={(e) => onAccountChange(e.target.value)}
                        style={selectStyle}
                        disabled={loadingAccounts}
                    >
                        <option value="">
                            {loadingAccounts
                                ? t(language, 'Loading...', '載入中…')
                                : t(language, 'Select an account', '請選擇帳戶')}
                        </option>
                        {accountList.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                                {acc.name} · {acc.id}
                            </option>
                        ))}
                    </select>
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {t(language, 'Period (days)', '分析區間（天）')}
                    </span>
                    <select
                        value={periodDays}
                        onChange={(e) => onPeriodChange(Number(e.target.value))}
                        style={selectStyle}
                    >
                        <option value={90}>90</option>
                        <option value={180}>180</option>
                        <option value={365}>365</option>
                    </select>
                </label>

                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        type="button"
                        onClick={onRefreshCampaigns}
                        disabled={!accountId || refreshing}
                        style={{
                            ...secondaryButtonStyle,
                            opacity: !accountId || refreshing ? 0.5 : 1,
                        }}
                    >
                        {refreshing
                            ? t(language, 'Refreshing…', '抓取中…')
                            : t(language, 'Refresh Data', '抓取資料')}
                    </button>
                    <button
                        type="button"
                        onClick={onSubmit}
                        disabled={!canSubmit || submitting}
                        style={{
                            ...primaryButtonStyle,
                            opacity: !canSubmit || submitting ? 0.5 : 1,
                        }}
                    >
                        {submitting
                            ? t(language, 'Submitting…', '送出中…')
                            : t(language, 'Run Analysis', '開始分析')}
                    </button>
                </div>
            </div>

            {accountId && (
                <div
                    style={{
                        marginTop: '10px',
                        color: 'var(--text-secondary)',
                        fontSize: '0.78rem',
                    }}
                >
                    {t(
                        language,
                        `Cached campaigns: ${campaignsCount}. If 0, click Refresh Data to fetch from Meta.`,
                        `快取中活動數：${campaignsCount}。若為 0 請先按「抓取資料」從 Meta 拉取。`
                    )}
                    {dataCoverage?.first_date && (
                        <span>
                            {' · '}
                            {t(
                                language,
                                `Cached data covers ${dataCoverage.first_date} ~ ${dataCoverage.last_date} (${dataCoverage.days_covered} days).`,
                                `快取資料涵蓋 ${dataCoverage.first_date} ~ ${dataCoverage.last_date}（共 ${dataCoverage.days_covered} 天）。`
                            )}
                        </span>
                    )}
                </div>
            )}

            {coverageInsufficient && (
                <div style={{ marginTop: '10px' }}>
                    <InfoPanel
                        message={t(
                            language,
                            `Requested period starts before cached data (${dataCoverage.first_date}). Analysis will automatically use the actually cached range instead of padding missing days with zero.`,
                            `選擇的區間早於實際快取起點（${dataCoverage.first_date}），分析會自動改用實際可用的快取區間，不會把缺口日子當成 0 花費餵進模型。`
                        )}
                    />
                </div>
            )}
        </Section>
    );
};

export default AccountAndPeriod;
