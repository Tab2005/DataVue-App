// frontend/src/components/Reports/ReportCard.jsx
import React from 'react';
import { FiFileText, FiTrash2, FiCalendar, FiArrowRight, FiClock } from 'react-icons/fi';
import { Link } from 'react-router-dom';

const ReportCard = ({ report, onDelete, language }) => {
  const t = (en, zh) => (language === 'zh' ? zh : en);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'generated':
        return { label: t('Generated', '已產生'), color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' };
      case 'archived':
        return { label: t('Archived', '已封存'), color: '#6b7280', bg: 'rgba(107, 114, 128, 0.1)' };
      case 'draft':
      default:
        return { label: t('Draft', '草稿'), color: 'var(--text-secondary)', bg: 'var(--bg-hover)' };
    }
  };

  const badge = getStatusBadge(report.status);

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '12px',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      transition: 'transform 0.2s, box-shadow 0.2s',
      cursor: 'default',
      position: 'relative',
      overflow: 'hidden'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.3)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{
          padding: '10px',
          backgroundColor: badge.bg,
          borderRadius: '10px',
          color: badge.color
        }}>
          <FiFileText size={24} />
        </div>
        <div style={{
          fontSize: '0.75rem',
          padding: '4px 8px',
          borderRadius: '20px',
          backgroundColor: badge.bg,
          color: badge.color,
          fontWeight: 'bold',
          border: `1px solid ${badge.color}33`
        }}>
          {badge.label}
        </div>
      </div>

      <div style={{ marginTop: '4px' }}>
        <h3 style={{
          fontSize: '1.1rem',
          fontWeight: 'bold',
          color: 'var(--text-primary)',
          margin: '0 0 4px 0',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {report.name}
        </h3>
        <p style={{
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <FiClock size={14} />
          {report.ad_account_name || report.ad_account_id}
        </p>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '0.85rem',
        color: 'var(--text-tertiary)',
        backgroundColor: 'var(--bg-primary)',
        padding: '8px 12px',
        borderRadius: '8px',
        marginTop: '8px'
      }}>
        <FiCalendar size={14} />
        <span>{report.date_since}</span>
        <FiArrowRight size={12} />
        <span>{report.date_until}</span>
      </div>

      <div style={{
        display: 'flex',
        gap: '8px',
        marginTop: '16px'
      }}>
        <Link
          to={`/reports/${report.id}`}
          style={{
            flex: 1,
            backgroundColor: 'var(--accent-primary)',
            color: 'white',
            textAlign: 'center',
            padding: '10px',
            borderRadius: '8px',
            textDecoration: 'none',
            fontSize: '0.9rem',
            fontWeight: 'bold',
            transition: 'opacity 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.opacity = 0.9}
          onMouseLeave={(e) => e.target.style.opacity = 1}
        >
          {t('View Report', '查看報表')}
        </Link>
        <button
          onClick={() => onDelete(report.id)}
          style={{
            padding: '10px',
            borderRadius: '8px',
            border: '1px solid var(--glass-border)',
            backgroundColor: 'transparent',
            color: '#ef4444',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          <FiTrash2 size={18} />
        </button>
      </div>
    </div>
  );
};

export default ReportCard;
