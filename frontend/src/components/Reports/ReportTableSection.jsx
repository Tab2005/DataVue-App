// frontend/src/components/Reports/ReportTableSection.jsx
import React from 'react';
import AnalyticsTableRow from '../Analytics/AnalyticsTableRow';

const ReportTableSection = ({ data, columns, language, breakdown }) => {
  if (!data || !data.table_data) return null;

  const t = (en, zh) => (language === 'zh' ? zh : en);

  const getHeaderLabel = () => {
    switch (breakdown) {
      case 'campaign': return t('Campaign Name', '廣告活動名稱');
      case 'adset': return t('Ad Set Name', '廣告組合名稱');
      case 'ad': return t('Ad Name', '廣告名稱');
      default: return t('Name', '名稱');
    }
  };

  return (
    <div style={{ marginBottom: '32px' }}>
      <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '32px 0' }} />
      <h2 style={{ 
        fontSize: '1.2rem', 
        color: '#8b5cf6', 
        marginBottom: '20px', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px',
        borderLeft: '4px solid #8b5cf6',
        paddingLeft: '12px',
        fontWeight: 600
      }}>
        {t('III. Detailed Performance Breakdown', '三、 廣告明細成效圖表')}
      </h2>
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--glass-border)',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
                <th style={{ padding: '12px 16px', borderBottom: '1px solid var(--glass-border)', color: 'var(--text-secondary)', fontSize: '0.85rem', whiteSpace: 'nowrap', minWidth: '200px' }}>
                  {getHeaderLabel()}
                </th>
                {columns.map(col => (
                  <th key={col.key} style={{ padding: '12px 16px', borderBottom: '1px solid var(--glass-border)', color: 'var(--text-secondary)', fontSize: '0.85rem', textAlign: 'right', whiteSpace: 'nowrap', minWidth: '80px' }}>
                    {language === 'zh' ? col.label_zh : col.label_en}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.table_data.slice(0, 50).map((row, idx) => (
                <AnalyticsTableRow
                  key={row.id || idx}
                  row={row}
                  columns={columns}
                  rowIndex={idx}
                  showCheckbox={false}
                  language={language}
                  nameKey="name"
                />
              ))}
            </tbody>
          </table>
        </div>
        {data.table_data.length > 50 && (
          <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.85rem', borderTop: '1px solid var(--glass-border)' }}>
            {t(`Showing top 50 of ${data.table_data.length} items`, `顯示前 50 筆資料（共 ${data.table_data.length} 筆）`)}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportTableSection;
