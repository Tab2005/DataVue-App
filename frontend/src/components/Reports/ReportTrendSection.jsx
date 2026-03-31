// frontend/src/components/Reports/ReportTrendSection.jsx
import React from 'react';
import TrendsChart from '../TrendsChart';

const ReportTrendSection = ({ data, selectedMetrics, language }) => {
  if (!data || !data.trends) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  return (
    <div style={{ marginBottom: '32px' }}>
      <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '32px 0' }} />
      <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        {t('II. Performance Trends', '二、 成效趨勢分析')}
      </h2>
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--glass-border)',
        borderRadius: '12px',
        padding: '24px'
      }}>
        <TrendsChart
          data={data.trends}
          metrics={selectedMetrics.slice(0, 3)} // Limit to 3 metrics for chart clarity in report
          language={language}
          height={350}
        />
      </div>
    </div>
  );
};

export default ReportTrendSection;
