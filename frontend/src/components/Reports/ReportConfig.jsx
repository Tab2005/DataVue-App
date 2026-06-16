// frontend/src/components/Reports/ReportConfig.jsx
import React, { useState, useEffect } from 'react';
import { FiChevronRight, FiChevronLeft, FiSettings, FiCalendar, FiActivity, FiCheckCircle, FiMessageSquare, FiFacebook, FiGlobe } from 'react-icons/fi';
import ReportAdAccountSelector from './ReportAdAccountSelector';
import ReportGA4PropertySelector from './ReportGA4PropertySelector';
import { lineService } from '../../services/lineService';
import { MetricSelector } from '../Analytics';
import { getMetricConfig, METRIC_GROUPS, getGroupsByModule } from '../../constants/analyticsConfig';
import { format, subDays, startOfWeek, endOfWeek, subMonths, startOfMonth, endOfMonth } from 'date-fns';

const ReportConfig = ({ onSave, onCancel, initialData = {}, initialEditData = null, language, teamId }) => {
  const [step, setStep] = useState(1);
  const [isEditMode, setIsEditMode] = useState(false);
  const [formData, setFormData] = useState({
    name: initialData.name || '',
    description: initialData.description || '',
    module_type: initialData.module_type || 'fb_ads',
    ad_account_id: initialData.ad_account_id || '',
    ad_account_name: initialData.ad_account_name || '',
    date_since: initialData.date_since || format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    date_until: initialData.date_until || format(subDays(new Date(), 1), 'yyyy-MM-dd'),
    date_label: initialData.date_label || '',
    breakdown: initialData.breakdown || (initialData.module_type === 'ga4' ? 'sessionSourceMedium' : 'campaign'),
    team_id: initialData.team_id || null,
    selected_metrics: initialData.selected_metrics || (initialData.module_type === 'ga4' ? ['activeUsers', 'sessions', 'screenPageViews', 'engagementRate'] : ['spend', 'roas', 'purchases', 'cpc', 'ctr']),
    // Automation fields
    is_automated: initialData.is_automated || false,
    frequency: initialData.frequency || 'weekly',
    day_of_week: initialData.day_of_week || '1', // Monday
    day_of_month: initialData.day_of_month || '1',
    time_of_day: initialData.time_of_day || '08:00',
    is_notify_line: initialData.is_notify_line || false
  });

  const [lineStatus, setLineStatus] = useState({ is_linked: false });

  useEffect(() => {
    const fetchLineStatus = async () => {
      try {
        const status = await lineService.getStatus();
        setLineStatus(status);
      } catch (err) {
        console.error("Failed to fetch LINE status", err);
      }
    };
    fetchLineStatus();
  }, []);

  // 編輯模式：回填資料
  useEffect(() => {
    if (initialEditData) {
      setIsEditMode(true);
      const mType = initialEditData.module_type || 'fb_ads';
      setFormData(prev => ({
        ...prev,
        id: initialEditData.id,
        name: initialEditData.name || '',
        module_type: mType,
        ad_account_id: initialEditData.ad_account_id || '',
        ad_account_name: initialEditData.ad_account_name || '',
        breakdown: initialEditData.breakdown || (mType === 'ga4' ? 'sessionSourceMedium' : 'campaign'),
        selected_metrics: Array.isArray(initialEditData.selected_metrics) 
          ? initialEditData.selected_metrics 
          : (typeof initialEditData.selected_metrics === 'string' ? JSON.parse(initialEditData.selected_metrics) : []),
        is_automated: true, // 既然是從編輯排程進入，強制為 true
        frequency: initialEditData.frequency || 'weekly',
        day_of_week: initialEditData.day_of_week || '1',
        day_of_month: initialEditData.day_of_month || '1',
        time_of_day: initialEditData.time_of_day || '08:00',
        is_notify_line: initialEditData.is_notify_line || false,
        team_id: initialEditData.team_id || teamId
      }));
    }
  }, [initialEditData, teamId]);


  const t = (en, zh) => (language === 'zh' ? zh : en);

  const handleNext = () => setStep(s => s + 1);
  const handleBack = () => setStep(s => s - 1);

  const updateField = (field, value) => {
    setFormData(prev => {
        const newData = { ...prev, [field]: value };
        // 當切換 module_type 時，重置相關欄位
        if (field === 'module_type' && value !== prev.module_type) {
            newData.ad_account_id = '';
            newData.ad_account_name = '';
            if (value === 'ga4') {
                newData.selected_metrics = ['activeUsers', 'sessions', 'screenPageViews', 'engagementRate'];
                newData.breakdown = 'sessionSourceMedium';
            } else {
                newData.selected_metrics = ['spend', 'roas', 'purchases', 'cpc', 'ctr'];
                newData.breakdown = 'campaign';
            }
        }
        return newData;
    });
  };

  const currentMetricGroups = getGroupsByModule(formData.module_type);

  const handleQuickDate = (preset) => {
    const today = new Date();
    let since, until;
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
      default: return;
    }
    setFormData(prev => ({ ...prev, date_since: since, date_until: until }));
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiSettings color="var(--accent-primary)" /> {t('Step 1: Basic Information', '步驟 1：基本資訊')}
            </h2>

            {/* Module Type Selector */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Report Type', '報表類型')}</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div 
                  onClick={() => updateField('module_type', 'fb_ads')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: formData.module_type === 'fb_ads' ? '2px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                    backgroundColor: formData.module_type === 'fb_ads' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'all 0.2s'
                  }}
                >
                  <FiFacebook size={24} color={formData.module_type === 'fb_ads' ? 'var(--accent-primary)' : 'var(--text-tertiary)'} />
                  <span style={{ fontSize: '0.9rem', color: formData.module_type === 'fb_ads' ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: formData.module_type === 'fb_ads' ? '600' : 'normal' }}>
                    {t('Facebook Ads', 'Facebook 廣告')}
                  </span>
                </div>
                <div 
                  onClick={() => updateField('module_type', 'ga4')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: formData.module_type === 'ga4' ? '2px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                    backgroundColor: formData.module_type === 'ga4' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'all 0.2s'
                  }}
                >
                  <FiGlobe size={24} color={formData.module_type === 'ga4' ? 'var(--accent-primary)' : 'var(--text-tertiary)'} />
                  <span style={{ fontSize: '0.9rem', color: formData.module_type === 'ga4' ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: formData.module_type === 'ga4' ? '600' : 'normal' }}>
                    {t('GA4 Website', 'GA4 網站數據')}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Report Name', '報表名稱')}</label>
              <input
                type="text"
                placeholder={t('e.g. 2026 W09 Weekly Report', '例如：2026 W09 每週報表')}
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-primary)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)'
                }}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {formData.module_type === 'ga4' ? t('GA4 Property', 'GA4 資源') : t('Ad Account', '廣告帳號')}
              </label>
              {formData.module_type === 'ga4' ? (
                <ReportGA4PropertySelector
                  selectedId={formData.ad_account_id}
                  onSelect={(id, name) => {
                    updateField('ad_account_id', id);
                    updateField('ad_account_name', name);
                  }}
                  language={language}
                />
              ) : (
                <ReportAdAccountSelector
                  teamId={teamId}
                  selectedId={formData.ad_account_id}
                  onSelect={(id, name) => {
                    updateField('ad_account_id', id);
                    updateField('ad_account_name', name);
                  }}
                  language={language}
                />
              )}
            </div>
            <div style={{ 
                marginTop: '12px',
                padding: '16px',
                backgroundColor: 'rgba(99, 102, 241, 0.05)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <div>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', margin: '0 0 4px 0' }}>{t('Automate this Report', '自動化此報表')}</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>{t('Automatically generate reports on a recurring schedule.', '設定排程，系統將定期為您自動產生報表。')}</p>
                </div>
                <div 
                    onClick={() => updateField('is_automated', !formData.is_automated)}
                    style={{
                        width: '50px',
                        height: '26px',
                        backgroundColor: formData.is_automated ? 'var(--accent-primary)' : 'var(--bg-primary)',
                        borderRadius: '13px',
                        padding: '3px',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        border: '1px solid var(--glass-border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: formData.is_automated ? 'flex-end' : 'flex-start'
                    }}
                >
                    <div style={{ 
                        width: '20px', 
                        height: '20px', 
                        backgroundColor: 'white', 
                        borderRadius: '50%', 
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        transition: 'all 0.3s ease'
                    }} />
                </div>
            </div>
          </div>

        );
      case 2:
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
                      style={{
                        flex: 1,
                        padding: '8px',
                        borderRadius: '8px',
                        border: '1px solid var(--glass-border)',
                        backgroundColor: 'var(--bg-primary)',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        fontSize: '0.85rem'
                      }}
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
                    <input
                      type="date"
                      value={formData.date_since}
                      onChange={(e) => updateField('date_since', e.target.value)}
                      style={{ padding: '10px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                    />
                  </div>
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{t('End Date', '結束日期')}</label>
                    <input
                      type="date"
                      value={formData.date_until}
                      onChange={(e) => updateField('date_until', e.target.value)}
                      style={{ padding: '10px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Frequency', '產生頻率')}</label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => updateField('frequency', e.target.value)}
                    style={{ padding: '12px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                  >
                    <option value="daily">{t('Daily', '每日')}</option>
                    <option value="weekly">{t('Weekly', '每週')}</option>
                    <option value="monthly">{t('Monthly', '每月')}</option>
                  </select>
                </div>

                {formData.frequency === 'weekly' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Day of Week', '每週執行日')}</label>
                    <select
                      value={formData.day_of_week}
                      onChange={(e) => updateField('day_of_week', e.target.value)}
                      style={{ padding: '12px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                    >
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
                    <input
                      type="number"
                      min="1"
                      max="28"
                      value={formData.day_of_month}
                      onChange={(e) => updateField('day_of_month', e.target.value)}
                      style={{ padding: '12px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                    />
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Execution Time', '執行時間 (UTC+8)')}</label>
                  <input
                    type="time"
                    value={formData.time_of_day}
                    onChange={(e) => updateField('time_of_day', e.target.value)}
                    style={{ padding: '12px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
                  />
                </div>

                {/* LINE Notification Toggle */}
                <div style={{ 
                    marginTop: '8px',
                    padding: '16px', 
                    borderRadius: '12px', 
                    backgroundColor: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--glass-border)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <FiMessageSquare color={lineStatus?.is_linked ? "#06c755" : "var(--text-tertiary)"} />
                            <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{t('LINE Notification', 'LINE 通知推播')}</span>
                        </div>
                        <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '44px', height: '22px' }}>
                            <input 
                                type="checkbox"
                                disabled={!lineStatus?.is_linked}
                                checked={formData.is_notify_line}
                                onChange={(e) => updateField('is_notify_line', e.target.checked)}
                                style={{ opacity: 0, width: 0, height: 0 }}
                            />
                            <span style={{
                                position: 'absolute', cursor: lineStatus?.is_linked ? 'pointer' : 'not-allowed', inset: 0,
                                backgroundColor: formData.is_notify_line ? '#06c755' : '#444',
                                transition: '.4s', borderRadius: '34px'
                            }}>
                                <span style={{
                                    position: 'absolute', height: '18px', width: '18px', left: formData.is_notify_line ? '24px' : '2px', bottom: '2px',
                                    backgroundColor: 'white', transition: '.4s', borderRadius: '50%'
                                }}></span>
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
              <select
                value={formData.breakdown}
                onChange={(e) => updateField('breakdown', e.target.value)}
                style={{ padding: '12px', backgroundColor: '#ffffff', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#000000' }}
              >
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
      case 3:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiActivity color="var(--accent-primary)" /> {t('Step 3: Metric Selection', '步驟 3：指標選擇')}
            </h2>
            <div style={{ 
              maxHeight: '450px', 
              overflowY: 'auto', 
              padding: '16px',
              backgroundColor: 'rgba(255,255,255,0.02)',
              borderRadius: '12px',
              border: '1px solid var(--glass-border)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '20px'
            }}>
               {currentMetricGroups.map((group) => {
                 const groupKeys = group.metrics.map(m => m.key);
                 const isAllSelected = groupKeys.every(k => formData.selected_metrics.includes(k));
                 
                 const handleToggleGroup = () => {
                   if (isAllSelected) {
                     // Remove all from this group
                     updateField('selected_metrics', formData.selected_metrics.filter(k => !groupKeys.includes(k)));
                   } else {
                     // Add all from this group (and avoid duplicates)
                     const otherMetrics = formData.selected_metrics.filter(k => !groupKeys.includes(k));
                     updateField('selected_metrics', [...otherMetrics, ...groupKeys]);
                   }
                 };

                 return (
                   <div key={group.id} style={{
                     backgroundColor: 'rgba(255, 255, 255, 0.03)',
                     border: `1px solid ${group.color}30`,
                     borderRadius: '12px',
                     padding: '16px',
                   }}>
                     <div style={{ 
                       fontSize: '0.9rem', 
                       fontWeight: '600', 
                       color: group.color, 
                       marginBottom: '12px',
                       display: 'flex',
                       alignItems: 'center',
                       justifyContent: 'space-between',
                       gap: '8px'
                     }}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: group.color }} />
                        {language === 'zh' ? group.label_zh : group.label_en}
                       </div>
                       
                       <label style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '6px', 
                          fontSize: '0.75rem', 
                          cursor: 'pointer',
                          backgroundColor: isAllSelected ? `${group.color}20` : 'transparent',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          border: `1px solid ${group.color}40`,
                          transition: 'all 0.2s'
                       }}>
                          <input 
                            type="checkbox" 
                            checked={isAllSelected}
                            onChange={handleToggleGroup}
                            style={{ accentColor: group.color, scale: '0.8' }}
                          />
                          {t('Select All', '全選')}
                       </label>
                     </div>
                     <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                       {group.metrics.map((metric) => (
                         <label key={metric.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                           <input
                             type="checkbox"
                             checked={formData.selected_metrics.includes(metric.key)}
                             onChange={() => {
                               const current = [...formData.selected_metrics];
                               if (current.includes(metric.key)) {
                                 updateField('selected_metrics', current.filter(k => k !== metric.key));
                               } else {
                                 updateField('selected_metrics', [...current, metric.key]);
                               }
                             }}
                             style={{ width: '16px', height: '16px', accentColor: group.color, cursor: 'pointer' }}
                           />
                           <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                             {language === 'zh' ? metric.label_zh : metric.label_en}
                           </span>
                         </label>
                       ))}
                     </div>
                   </div>
                 );
               })}
            </div>
          </div>
        );
      case 4:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px', padding: '20px 0' }}>
            <FiCheckCircle size={64} color="#10b981" />
            <div style={{ textAlign: 'center' }}>
              <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)', marginBottom: '8px' }}>
                {isEditMode ? t('Save Changes', '確認修改') : t('Ready to Create', '準備就緒')}
              </h2>
              <p style={{ color: 'var(--text-secondary)' }}>
                {isEditMode 
                  ? t('Confirm your updated settings and click save.', '確認修改後的設定無誤後，點擊儲存。')
                  : t('Confirm your settings and click save to create the report draft.', '確認您的設定無誤後，點擊儲存以建立報表草稿。')}
              </p>
            </div>
            <div style={{ width: '100%', backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Mode', '執行模式')}:</span>
                <span style={{ color: formData.is_automated ? 'var(--accent-primary)' : 'var(--text-primary)', fontWeight: 'bold' }}>
                    {formData.is_automated ? t('Automated Schedule', '自動排程') : t('Manual Report', '手動報表')}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Type', '報表類型')}:</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>
                  {formData.module_type === 'ga4' ? t('GA4 Website', 'GA4 網站數據') : t('Facebook Ads', 'Facebook 廣告')}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Name', '報表名稱')}:</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>{formData.name}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{formData.module_type === 'ga4' ? t('Property', 'GA4 資源') : t('Account', '廣告帳號')}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{formData.ad_account_name || formData.ad_account_id}</span>
              </div>
              {formData.is_automated ? (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>{t('Frequency', '頻率')}:</span>
                    <span style={{ color: 'var(--text-primary)' }}>
                        {formData.frequency === 'daily' && t('Daily', '每日')}
                        {formData.frequency === 'weekly' && t('Weekly', '每週')}
                        {formData.frequency === 'monthly' && t('Monthly', '每月')}
                        {` @ ${formData.time_of_day}`}
                    </span>
                  </div>
              ) : (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>{t('Range', '日期範圍')}:</span>
                    <span style={{ color: 'var(--text-primary)' }}>{formData.date_since} ~ {formData.date_until}</span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Metrics', '指標數量')}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{formData.selected_metrics.length}</span>
              </div>
            </div>
          </div>
        );
      default: return null;
    }
  };

  return (
    <div style={{
      maxWidth: '600px',
      margin: '0 auto',
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: '16px',
      border: '1px solid var(--glass-border)',
      boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
      overflow: 'visible'
    }}>
      {/* ProgressBar */}
      <div style={{ height: '4px', backgroundColor: 'var(--bg-primary)', display: 'flex' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} style={{
            flex: 1,
            backgroundColor: i <= step ? 'var(--accent-primary)' : 'transparent',
            transition: 'background 0.3s ease'
          }} />
        ))}
      </div>

      <div style={{ padding: '32px' }}>
        {renderStep()}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '40px', gap: '16px' }}>
          <button
            onClick={step === 1 ? onCancel : handleBack}
            style={{
              padding: '12px 24px',
              borderRadius: '10px',
              border: '1px solid var(--glass-border)',
              backgroundColor: 'transparent',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {step === 1 ? t('Cancel', '取消') : <><FiChevronLeft /> {t('Back', '上一步')}</>}
          </button>

          {step < 4 ? (
            <button
              onClick={handleNext}
              disabled={step === 1 && (!formData.name || !formData.ad_account_id)}
              style={{
                padding: '12px 32px',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: 'var(--accent-primary)',
                color: 'white',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 'bold',
                opacity: (step === 1 && (!formData.name || !formData.ad_account_id)) ? 0.5 : 1
              }}
            >
              {t('Next', '下一步')} <FiChevronRight />
            </button>
          ) : (
            <button
              onClick={() => onSave(formData)}
              style={{
                padding: '12px 32px',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: '#10b981',
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              {isEditMode ? t('Save Changes', '儲存修改') : t('Create & Run', '建立並產生報表')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportConfig;
