import { getMetricConfig } from '../../constants/analyticsConfig';
import AnalyticsKPICard from '../Analytics/AnalyticsKPICard';

const ReportKPISection = ({ data, selectedMetrics, language, dateSince, dateUntil }) => {
  if (!data || !data.summary) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  // Calculate comparison dates locally
  const getPrevRange = () => {
    if (!dateSince || !dateUntil) return '';
    try {
      const since = new Date(dateSince);
      const until = new Date(dateUntil);
      const diffTime = Math.abs(until - since);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      
      const pUntil = new Date(since);
      pUntil.setDate(pUntil.getDate() - 1);
      
      const pSince = new Date(pUntil);
      pSince.setDate(pSince.getDate() - diffDays + 1);
      
      const fmt = (d) => d.toISOString().split('T')[0];
      return `${fmt(pSince)} ~ ${fmt(pUntil)}`;
    } catch (e) {
      return '';
    }
  };

  const prevRange = getPrevRange();

  const summary = data.summary;
  const prevSummary = data.prev_summary || {};

  return (
    <div style={{ marginBottom: '32px' }}>
      <div className="report-kpi-header" style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2 style={{ 
            fontSize: '1.2rem', 
            color: '#fbbf24', 
            margin: 0, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            borderLeft: '4px solid #fbbf24',
            paddingLeft: '12px',
            fontWeight: 600
        }}>
            {t('I. Key Performance Indicators', '一、 關鍵指標總覽')}
        </h2>
        {prevRange && (
            <span style={{ 
                fontSize: '0.85rem', 
                color: 'var(--text-tertiary)', 
                backgroundColor: 'rgba(251, 191, 36, 0.05)', 
                padding: '4px 12px', 
                borderRadius: '20px',
                border: '1px solid rgba(251, 191, 36, 0.1)'
            }}>
                {t('VS Previous Period: ', '對比前一期：')}{prevRange}
            </span>
        )}
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
        gap: '12px'
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
