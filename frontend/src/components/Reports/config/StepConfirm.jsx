import React from 'react';
import { FiCheckCircle } from 'react-icons/fi';

const StepConfirm = ({ formData, isEditMode, t }) => (
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

export default StepConfirm;
