import React from 'react';
import { FiCalendar, FiMessageSquare } from 'react-icons/fi';
import { endOfMonth, endOfWeek, format, startOfMonth, startOfWeek, subDays, subMonths } from 'date-fns';

const StepSchedule = ({ formData, updateField, lineStatus, t }) => {
    const handleQuickDate = (preset) => {
        const today = new Date();
        let since;
        let until;
        switch (preset) {
            case 'last_week':
                since = format(startOfWeek(subDays(today, 7), { weekStartsOn: 1 }), 'yyyy-MM-dd');
                until = format(endOfWeek(subDays(today, 7), { weekStartsOn: 1 }), 'yyyy-MM-dd');
                break;
            case 'last_month':
                since = format(startOfMonth(subMonths(today, 1)), 'yyyy-MM-dd');
                until = format(endOfMonth(subMonths(today, 1)), 'yyyy-MM-dd');
                break;
            case 'this_week':
                since = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd');
                until = format(today, 'yyyy-MM-dd');
                break;
            default:
                return;
        }
        updateField('date_since', since);
        updateField('date_until', until);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiCalendar color="var(--accent-primary)" /> {formData.is_automated ? t('Step 2: Schedule Settings', '步驟 2：排程設定') : t('Step 2: Date Range', '步驟 2：日期範圍')}
            </h2>

            {!formData.is_automated ? (
                <>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                        {['this_week', 'last_week', 'last_month'].map(p => (
                            <button
                                key={p}
                                onClick={() => handleQuickDate(p)}
                                style={{ flex: 1, padding: '8px', borderRadius: '8px', border: '1px solid var(--glass-border)', backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.85rem' }}
                            >
                                {p === 'this_week' && t('This Week', '本週')}
                                {p === 'last_week' && t('Last Week', '上週')}
                                {p === 'last_month' && t('Last Month', '上個月')}
                            </button>
                        ))}
                    </div>
                    <div style={{ display: 'flex', gap: '16px' }}>
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{t('Start Date', '開始日期')}</label>
                            <input type="date" value={formData.date_since} onChange={(e) => updateField('date_since', e.target.value)} style={{ padding: '10px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                        </div>
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{t('End Date', '結束日期')}</label>
                            <input type="date" value={formData.date_until} onChange={(e) => updateField('date_until', e.target.value)} style={{ padding: '10px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                        </div>
                    </div>
                </>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Frequency', '產生頻率')}</label>
                        <select value={formData.frequency} onChange={(e) => updateField('frequency', e.target.value)} style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }}>
                            <option value="daily">{t('Daily', '每日')}</option>
                            <option value="weekly">{t('Weekly', '每週')}</option>
                            <option value="monthly">{t('Monthly', '每月')}</option>
                        </select>
                    </div>

                    {formData.frequency === 'weekly' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Day of Week', '每週執行日')}</label>
                            <select value={formData.day_of_week} onChange={(e) => updateField('day_of_week', e.target.value)} style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }}>
                                <option value="1">{t('Monday', '週一')}</option>
                                <option value="2">{t('Tuesday', '週二')}</option>
                                <option value="3">{t('Wednesday', '週三')}</option>
                                <option value="4">{t('Thursday', '週四')}</option>
                                <option value="5">{t('Friday', '週五')}</option>
                                <option value="6">{t('Saturday', '週六')}</option>
                                <option value="0">{t('Sunday', '週日')}</option>
                            </select>
                        </div>
                    )}

                    {formData.frequency === 'monthly' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Day of Month', '每月執行日')}</label>
                            <input type="number" min="1" max="28" value={formData.day_of_month} onChange={(e) => updateField('day_of_month', e.target.value)} style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                        </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Execution Time', '執行時間 (UTC+8)')}</label>
                        <input type="time" value={formData.time_of_day} onChange={(e) => updateField('time_of_day', e.target.value)} style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                    </div>

                    <div style={{ marginTop: '8px', padding: '16px', borderRadius: '12px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <FiMessageSquare color={lineStatus?.is_linked ? '#06c755' : 'var(--text-tertiary)'} />
                                <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{t('LINE Notification', 'LINE 通知推播')}</span>
                            </div>
                            <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '44px', height: '22px' }}>
                                <input type="checkbox" disabled={!lineStatus?.is_linked} checked={formData.is_notify_line} onChange={(e) => updateField('is_notify_line', e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{ position: 'absolute', cursor: lineStatus?.is_linked ? 'pointer' : 'not-allowed', inset: 0, backgroundColor: formData.is_notify_line ? '#06c755' : '#444', transition: '.4s', borderRadius: '34px' }}>
                                    <span style={{ position: 'absolute', height: '18px', width: '18px', left: formData.is_notify_line ? '24px' : '2px', bottom: '2px', backgroundColor: 'white', transition: '.4s', borderRadius: '50%' }}></span>
                                </span>
                            </label>
                        </div>
                        {!lineStatus?.is_linked && (
                            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                {t('Please link your LINE account in Integration Center first.', '⚠️ 請先至「整合中心」連結您的 LINE 帳號以啟用推播功能。')}
                            </p>
                        )}
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Analysis Level', '分析層級')}</label>
                <select value={formData.breakdown} onChange={(e) => updateField('breakdown', e.target.value)} style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }}>
                    {formData.module_type === 'ga4' ? (
                        <>
                            <option value="sessionSourceMedium">{t('Source / Medium', '來源 / 媒介')}</option>
                            <option value="pagePath">{t('Page Path', '網頁路徑')}</option>
                            <option value="country">{t('Country', '國家')}</option>
                        </>
                    ) : (
                        <>
                            <option value="account">{t('Account Overview', '整體總覽')}</option>
                            <option value="campaign">{t('Campaign Level', '廣告活動層級')}</option>
                            <option value="adset">{t('Ad Set Level', '廣告組合層級')}</option>
                            <option value="ad">{t('Ad Level', '廣告層級')}</option>
                        </>
                    )}
                </select>
            </div>
        </div>
    );
};

export default StepSchedule;
