// frontend/src/components/Reports/ReportNoteEditor.jsx
import React, { useState, useEffect } from 'react';
import { FiEdit3, FiSave } from 'react-icons/fi';

const ReportNoteEditor = ({ sections = [], onSave, language }) => {
  const [localSections, setLocalSections] = useState(sections.length > 0 ? sections : [{ title: '本週備註與後續建議', content: '', order: 0 }]);
  const [isSaving, setIsSaving] = useState(false);

  const t = (en, zh) => (language === 'zh' ? zh : en);

  const handleUpdate = (index, content) => {
    const newSections = [...localSections];
    newSections[index].content = content;
    setLocalSections(newSections);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(localSections);
    } finally {
      setIsSaving(false);
    }
  };

  // Auto-save debounced
  useEffect(() => {
    const timer = setTimeout(() => {
      if (JSON.stringify(localSections) !== JSON.stringify(sections)) {
        handleSave();
      }
    }, 2000);
    return () => clearTimeout(timer);
  }, [localSections]);

  return (
    <div style={{ marginBottom: '32px' }}>
      <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '32px 0' }} />
      <h2 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        {t('V. Notes & Recommendations', '五、 本週備註與後續建議')}
        {isSaving && <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 'normal', marginLeft: '12px' }}>{t('Saving...', '正在儲存...')}</span>}
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {localSections.map((section, idx) => (
          <div key={idx} style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--glass-border)',
            borderRadius: '12px',
            padding: '20px'
          }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
               <FiEdit3 /> {section.title}
            </h3>
            <textarea
              value={section.content}
              onChange={(e) => handleUpdate(idx, e.target.value)}
              placeholder={t('Enter your notes or recommendations here...', '在此輸入本週的成效解析、觀察或是下週的優化建議...')}
              style={{
                width: '100%',
                minHeight: '150px',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                padding: '16px',
                fontSize: '0.95rem',
                lineHeight: '1.6',
                resize: 'vertical'
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReportNoteEditor;
