// frontend/src/components/Reports/ReportTrendSection.jsx
import React from 'react';
import TrendsChart from '../TrendsChart';

const ReportTrendSection = ({ data, selectedMetrics, language }) => {
  if (!data || !data.trends) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  return (
    <div style={{ marginBottom: '32px' }}>
      <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '32px 0' }} />
      <h2 style={{ 
        fontSize: '1.2rem', 
        color: '#6366f1', 
        marginBottom: '20px', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px',
        borderLeft: '4px solid #6366f1',
        paddingLeft: '12px',
        fontWeight: 600
      }}>
        {t('II. Performance Trends', '二、 成效趨勢分析')}
      </h2>
      <div className="report-section-card" style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--glass-border)',
        borderRadius: '12px',
        padding: '24px'
      }}>
        <TrendsChart
          data={data.trends}
          metrics={selectedMetrics.slice(0, 3)} // Show top 3 metrics trends
          xAxisKey="date"
          language={language}
          height={380}
          title={t('Metric Trends Analysis', '各項指標趨勢分析')}
        />
      </div>
    </div>
  );
};

export default ReportTrendSection;
