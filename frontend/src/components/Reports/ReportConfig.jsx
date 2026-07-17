// frontend/src/components/Reports/ReportConfig.jsx
import React, { useEffect, useState } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { format, subDays } from 'date-fns';
import { lineService } from '../../services/lineService';
import StepBasicInfo from './config/StepBasicInfo';
import StepConfirm from './config/StepConfirm';
import StepMetricSelection from './config/StepMetricSelection';
import StepSchedule from './config/StepSchedule';

const defaultMetricsByModule = {
  ga4: ['activeUsers', 'sessions', 'screenPageViews', 'engagementRate'],
  fb_ads: ['spend', 'roas', 'purchases', 'cpc', 'ctr']
};

const defaultBreakdownByModule = {
  ga4: 'sessionSourceMedium',
  fb_ads: 'campaign'
};
const createInitialFormData = (initialData, initialEditData, teamId) => {
  if (initialEditData) {
    const moduleType = initialEditData.module_type || 'fb_ads';
    return {
      id: initialEditData.id,
      name: initialEditData.name || '',
      description: initialEditData.description || '',
      module_type: moduleType,
      ad_account_id: initialEditData.ad_account_id || '',
      ad_account_name: initialEditData.ad_account_name || '',
      date_since: initialEditData.date_since || format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      date_until: initialEditData.date_until || format(subDays(new Date(), 1), 'yyyy-MM-dd'),
      date_label: initialEditData.date_label || '',
      breakdown: initialEditData.breakdown || defaultBreakdownByModule[moduleType],
      team_id: initialEditData.team_id || teamId,
      selected_metrics: Array.isArray(initialEditData.selected_metrics)
        ? initialEditData.selected_metrics
        : (typeof initialEditData.selected_metrics === 'string' ? JSON.parse(initialEditData.selected_metrics) : []),
      is_automated: true,
      frequency: initialEditData.frequency || 'weekly',
      day_of_week: initialEditData.day_of_week || '1',
      day_of_month: initialEditData.day_of_month || '1',
      time_of_day: initialEditData.time_of_day || '08:00',
      is_notify_line: initialEditData.is_notify_line || false
    };
  }

  const moduleType = initialData.module_type || 'fb_ads';
  return {
    name: initialData.name || '',
    description: initialData.description || '',
    module_type: moduleType,
    ad_account_id: initialData.ad_account_id || '',
    ad_account_name: initialData.ad_account_name || '',
    date_since: initialData.date_since || format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    date_until: initialData.date_until || format(subDays(new Date(), 1), 'yyyy-MM-dd'),
    date_label: initialData.date_label || '',
    breakdown: initialData.breakdown || defaultBreakdownByModule[moduleType],
    team_id: initialData.team_id || null,
    selected_metrics: initialData.selected_metrics || defaultMetricsByModule[moduleType],
    is_automated: initialData.is_automated || false,
    frequency: initialData.frequency || 'weekly',
    day_of_week: initialData.day_of_week || '1',
    day_of_month: initialData.day_of_month || '1',
    time_of_day: initialData.time_of_day || '08:00',
    is_notify_line: initialData.is_notify_line || false
  };
};

const ReportConfig = ({ onSave, onCancel, initialData = {}, initialEditData = null, language, teamId }) => {
  const [step, setStep] = useState(1);
  const isEditMode = Boolean(initialEditData);
  const [formData, setFormData] = useState(() => createInitialFormData(initialData, initialEditData, teamId));

  const [lineStatus, setLineStatus] = useState({ is_linked: false });

  useEffect(() => {
    const fetchLineStatus = async () => {
      try {
        const status = await lineService.getStatus();
        setLineStatus(status);
      } catch (err) {
        console.error('Failed to fetch LINE status', err);
      }
    };
    fetchLineStatus();
  }, []);


  const t = (en, zh) => (language === 'zh' ? zh : en);
  const handleNext = () => setStep(s => s + 1);
  const handleBack = () => setStep(s => s - 1);

  const updateField = (field, value) => {
    setFormData(prev => {
      const newData = { ...prev, [field]: value };
      if (field === 'module_type' && value !== prev.module_type) {
        newData.ad_account_id = '';
        newData.ad_account_name = '';
        newData.selected_metrics = defaultMetricsByModule[value];
        newData.breakdown = defaultBreakdownByModule[value];
      }
      return newData;
    });
  };

  const renderStep = () => {
    const props = { formData, updateField, language, teamId, t };
    switch (step) {
      case 1:
        return <StepBasicInfo {...props} />;
      case 2:
        return <StepSchedule formData={formData} updateField={updateField} lineStatus={lineStatus} t={t} />;
      case 3:
        return <StepMetricSelection formData={formData} updateField={updateField} language={language} t={t} />;
      case 4:
        return <StepConfirm formData={formData} isEditMode={isEditMode} t={t} />;
      default:
        return null;
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
