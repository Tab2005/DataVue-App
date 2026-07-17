import React from 'react';
import { FiFacebook, FiGlobe, FiSettings } from 'react-icons/fi';
import ReportAdAccountSelector from '../ReportAdAccountSelector';
import ReportGA4PropertySelector from '../ReportGA4PropertySelector';

const StepBasicInfo = ({ formData, updateField, language, teamId, t }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiSettings color="var(--accent-primary)" /> {t('Step 1: Basic Information', '步驟 1：基本資訊')}
        </h2>

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
                style={{ padding: '12px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'var(--text-primary)' }}
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
                <div style={{ width: '20px', height: '20px', backgroundColor: 'white', borderRadius: '50%', boxShadow: '0 2px 4px rgba(0,0,0,0.2)', transition: 'all 0.3s ease' }} />
            </div>
        </div>
    </div>
);

export default StepBasicInfo;
