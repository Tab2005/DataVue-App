import { getMetricConfig } from '../../constants/analyticsConfig';
import AnalyticsKPICard from '../Analytics/AnalyticsKPICard';

const ReportKPISection = ({ data, selectedMetrics, language }) => {
  if (!data || !data.summary) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  const summary = data.summary;
  const prevSummary = data.prev_summary || {};

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
        {selectedMetrics.map((key) => {
          const config = getMetricConfig(key) || { label_zh: key, label_en: key, format: 'number' };
          const cur = summary[key] || 0;
          const prev = prevSummary[key] || 0;
          
          // Calculate change percentage
          let changeStr = '0%';
          if (prev > 0) {
            const diff = ((cur - prev) / prev) * 100;
            changeStr = `${diff > 0 ? '+' : ''}${diff.toFixed(1)}%`;
          } else if (cur > 0) {
            changeStr = '+100%';
          }

          return (
            <AnalyticsKPICard
              key={key}
              label={t(config.label_en, config.label_zh)}
              value={cur}
              prevValue={prev}
              change={changeStr}
              format={config.format}
              color={config.groupColor}
              isInverse={config.isInverse}
              language={language}
            />
          );
        })}
      </div>
    </div>
  );
};

export default ReportKPISection;
