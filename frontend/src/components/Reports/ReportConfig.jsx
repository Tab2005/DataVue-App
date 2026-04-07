// frontend/src/components/Reports/ReportConfig.jsx
import React, { useState } from 'react';
import { FiChevronRight, FiChevronLeft, FiSettings, FiCalendar, FiActivity, FiCheckCircle } from 'react-icons/fi';
import ReportAdAccountSelector from './ReportAdAccountSelector';
import { MetricSelector } from '../Analytics';
import { getMetricConfig, METRIC_GROUPS } from '../../constants/analyticsConfig';
import { format, subDays, startOfWeek, endOfWeek, subMonths, startOfMonth, endOfMonth } from 'date-fns';

const ReportConfig = ({ onSave, onCancel, initialData = {}, language, teamId }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: initialData.name || '',
    description: initialData.description || '',
    ad_account_id: initialData.ad_account_id || '',
    ad_account_name: initialData.ad_account_name || '',
    date_since: initialData.date_since || format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    date_until: initialData.date_until || format(subDays(new Date(), 1), 'yyyy-MM-dd'),
    date_label: initialData.date_label || '',
    selected_metrics: initialData.selected_metrics || ['spend', 'roas', 'purchases', 'cpc', 'ctr'],
    breakdown: initialData.breakdown || 'campaign',
    team_id: initialData.team_id || null
  });

  const t = (en, zh) => (language === 'zh' ? zh : en);

  const handleNext = () => setStep(s => s + 1);
  const handleBack = () => setStep(s => s - 1);

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

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
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Ad Account', '廣告帳號')}</label>
              <ReportAdAccountSelector
                teamId={teamId}
                selectedId={formData.ad_account_id}
                onSelect={(id, name) => {
                  updateField('ad_account_id', id);
                  updateField('ad_account_name', name);
                }}
                language={language}
              />
            </div>
          </div>
        );
      case 2:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiCalendar color="var(--accent-primary)" /> {t('Step 2: Date Range', '步驟 2：日期範圍')}
            </h2>
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
                  style={{ padding: '10px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white' }}
                />
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{t('End Date', '結束日期')}</label>
                <input
                  type="date"
                  value={formData.date_until}
                  onChange={(e) => updateField('date_until', e.target.value)}
                  style={{ padding: '10px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white' }}
                />
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{t('Analysis Level', '分析層級')}</label>
              <select
                value={formData.breakdown}
                onChange={(e) => updateField('breakdown', e.target.value)}
                style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white' }}
              >
                <option value="account">{t('Account Overview', '整體總覽')}</option>
                <option value="campaign">{t('Campaign Level', '廣告活動層級')}</option>
                <option value="adset">{t('Ad Set Level', '廣告組合層級')}</option>
                <option value="ad">{t('Ad Level', '廣告層級')}</option>
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
               {METRIC_GROUPS.map((group) => {
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
              <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)', marginBottom: '8px' }}>{t('Ready to Create', '準備就緒')}</h2>
              <p style={{ color: 'var(--text-secondary)' }}>
                {t('Confirm your settings and click save to create the report draft.', '確認您的設定無誤後，點擊儲存以建立報表草稿。')}
              </p>
            </div>
            <div style={{ width: '100%', backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Name', '報表名稱')}:</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 'bold' }}>{formData.name}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Account', '廣告帳號')}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{formData.ad_account_name || formData.ad_account_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{t('Range', '日期範圍')}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{formData.date_since} ~ {formData.date_until}</span>
              </div>
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
              {t('Create & Run', '建立並產生報表')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportConfig;
