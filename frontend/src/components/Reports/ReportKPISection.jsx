// frontend/src/components/Reports/ReportKPISection.jsx
import React from 'react';
import AnalyticsKPICard from '../Analytics/AnalyticsKPICard';

const ReportKPISection = ({ data, selectedMetrics, language }) => {
  if (!data || !data.summary) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  // Extract metrics from summary based on selectedMetrics
  // In WeeklyReport, summary is a snapshot of the calculated totals
  const summary = data.summary;

  return (
    <div style={{ marginBottom: '32px' }}>
      <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        {t('I. Key Performance Indicators', '一、 關鍵指標總覽')}
      </h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        {selectedMetrics.map((key, index) => (
          <AnalyticsKPICard
            key={key}
            metricKey={key}
            currentValue={summary[key]}
            previousValue={data.prev_summary ? data.prev_summary[key] : null}
            language={language}
          />
        ))}
      </div>
    </div>
  );
};

export default ReportKPISection;
