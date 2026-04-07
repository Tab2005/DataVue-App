// frontend/src/components/Reports/WeeklyReportTemplate.jsx
import React from 'react';
import ReportKPISection from './ReportKPISection';
import ReportTrendSection from './ReportTrendSection';
import ReportTableSection from './ReportTableSection';
import ReportNoteEditor from './ReportNoteEditor';
import { FiCpu, FiPrinter, FiRefreshCcw, FiZap } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { getMetricConfig } from '../../constants/analyticsConfig';

const WeeklyReportTemplate = ({ 
  report, 
  onUpdate, 
  onGenerate, 
  onGenerateAI, 
  isGenerating, 
  isAnalyzing, 
  language 
}) => {
  const t = (en, zh) => (language === 'zh' ? zh : en);

  if (!report || report.status === 'draft') {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', backgroundColor: 'var(--bg-secondary)', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
        <FiZap size={48} color="var(--accent-primary)" style={{ marginBottom: '16px' }} />
        <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)', marginBottom: '12px' }}>{t('Draft Report', '此報表尚為草稿')}</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>{t('Generate the report to fetch data and start analysis.', '請點擊下方按鈕以抓取廣告資料並開始分析。')}</p>
        <button
          onClick={onGenerate}
          disabled={isGenerating}
          style={{
            padding: '12px 32px',
            backgroundColor: 'var(--accent-primary)',
            color: 'white',
            borderRadius: '10px',
            border: 'none',
            fontWeight: 'bold',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            margin: '0 auto',
            opacity: isGenerating ? 0.7 : 1
          }}
        >
          {isGenerating ? <FiRefreshCcw className="spin" /> : <FiZap />}
          {isGenerating ? t('Broadcasting...', '正在抓取中...') : t('Generate Now', '立即產生報表')}
        </button>
      </div>
    );
  }

  const reportData = report.report_data;
  const selectedMetrics = report.selected_metrics || [];

  return (
    <div style={{ padding: '0 0 80px 0' }}>
      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
            {report.ad_account_name || report.ad_account_id}
          </div>
          <h1 style={{ fontSize: '2.4rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0 0 8px 0' }}>{report.name}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-secondary)' }}>
            <span style={{ backgroundColor: 'var(--bg-secondary)', padding: '4px 10px', borderRadius: '6px', fontSize: '0.85rem' }}>
              {report.date_since} ~ {report.date_until}
            </span>
            <span style={{ fontSize: '0.85rem' }}>{report.date_label}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => window.print()}
            style={{ padding: '10px 20px', borderRadius: '10px', border: '1px solid var(--glass-border)', backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          >
            <FiPrinter /> {t('Print / PDF', '列印 / 匯出 PDF')}
          </button>
          <button
            onClick={onGenerate}
            disabled={isGenerating}
            style={{ 
               padding: '10px 20px', 
               borderRadius: '10px', 
               border: '1px solid var(--glass-border)', 
               backgroundColor: 'var(--bg-secondary)', 
               color: 'var(--text-primary)', 
               display: 'flex', 
               alignItems: 'center', 
               gap: '8px', 
               cursor: isGenerating ? 'not-allowed' : 'pointer',
               opacity: isGenerating ? 0.7 : 1
            }}
          >
            <FiRefreshCcw className={isGenerating ? 'spin' : ''} /> {isGenerating ? t('Refreshing...', '正在刷更新資料...') : t('Refresh Data', '重新產生資料')}
          </button>
        </div>
      </div>

      {/* I. KPI Section */}
      <ReportKPISection data={reportData} selectedMetrics={selectedMetrics} language={language} />

      {/* II. Trend Section */}
      <ReportTrendSection data={reportData} selectedMetrics={selectedMetrics} language={language} />

      {/* III. Table Section */}
      <ReportTableSection 
        data={reportData} 
        columns={selectedMetrics.map(k => {
          const cfg = getMetricConfig(k) || { label_zh: k, label_en: k, format: 'number' };
          return {
            key: k,
            label_zh: cfg.label_zh,
            label_en: cfg.label_en,
            format: cfg.format
          };
        })} 
        breakdown={report.breakdown} 
        language={language} 
      />

      {/* IV. AI Summary Section */}
      <div style={{ marginBottom: '32px' }}>
        <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '32px 0' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            {t('IV. AI Performance Insights', '四、 AI 成效分析摘要')}
          </h2>
          <button
            onClick={onGenerateAI}
            disabled={isAnalyzing}
            style={{
              padding: '8px 16px',
              backgroundColor: 'var(--bg-hover)',
              border: '1px solid var(--glass-border)',
              color: 'var(--text-primary)',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.85rem'
            }}
          >
            {isAnalyzing ? <FiRefreshCcw className="spin" /> : <FiCpu />}
            {report.ai_summary ? t('Regenerate AI', '重新分析') : t('Generate AI Insights', '開始 AI 生成')}
          </button>
        </div>
        <div style={{
          backgroundColor: 'rgba(59, 130, 246, 0.05)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '12px',
          padding: '24px',
          minHeight: '100px'
        }}>
          {report.ai_summary ? (
             <div className="report-ai-content" style={{ color: 'var(--text-primary)', lineHeight: '1.8' }}>
                <ReactMarkdown>{report.ai_summary}</ReactMarkdown>
             </div>
          ) : (
            <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '20px' }}>
              {isAnalyzing ? t('AI is analyzing your data...', 'AI 正在分析您的數據...') : t('No AI summary available yet.', '尚未產生 AI 摘要。')}
            </div>
          )}
        </div>
      </div>

      {/* V. Manual Notes Section */}
      <ReportNoteEditor
        sections={report.sections}
        onSave={(newSections) => onUpdate({ sections: newSections })}
        language={language}
      />
    </div>
  );
};

export default WeeklyReportTemplate;
