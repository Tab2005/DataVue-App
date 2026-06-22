import React, { useState, useEffect } from 'react';
import { addCustomGroup, updateCustomGroup, deleteCustomGroup, isDefaultGroup, resetDefaultGroup } from '../utils/sourceGroups';

/**
 * SourceGroupModal - 新增/編輯來源分組的彈窗組件
 */
const SourceGroupModal = ({
    isOpen,
    onClose,
    onSave,
    propertyId,
    editGroup = null, // 傳入要編輯的分組，null 表示新增
    language = 'zh'
}) => {
    const [name, setName] = useState('');
    const [nameEn, setNameEn] = useState('');
    const [patterns, setPatterns] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const isEditing = editGroup !== null;
    const isDefault = editGroup && isDefaultGroup(editGroup.key);

    // 重置表單
    useEffect(() => {
        if (isOpen) {
            if (editGroup) {
                // 編輯模式：填入現有資料
                setName(editGroup.label_zh?.replace(/^[⭐📁🤖]\s*/, '') || '');
                setNameEn(editGroup.label_en?.replace(/^[⭐📁🤖]\s*/, '').replace(' (Group)', '') || '');
                setPatterns(editGroup.patterns?.join(', ') || '');
            } else {
                // 新增模式：清空
                setName('');
                setNameEn('');
                setPatterns('');
            }
            setError('');
        }
    }, [isOpen, editGroup]);

    const t = (zh, en) => language === 'zh' ? zh : en;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // 驗證
        if (!name.trim()) {
            setError(t('請輸入分組名稱', 'Please enter group name'));
            return;
        }

        const patternList = patterns.split(',').map(p => p.trim()).filter(Boolean);
        if (patternList.length === 0) {
            setError(t('請輸入至少一個匹配模式', 'Please enter at least one pattern'));
            return;
        }

        setLoading(true);

        try {
            if (isEditing) {
                updateCustomGroup(propertyId, editGroup.key, name.trim(), nameEn.trim(), patternList);
            } else {
                addCustomGroup(propertyId, name.trim(), nameEn.trim(), patternList);
            }

            onSave(); // 通知父元件重新載入
            onClose();
        } catch (err) {
            setError(err.message || t('儲存失敗', 'Save failed'));
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = () => {
        if (!editGroup || isDefault) return;

        if (window.confirm(t('確定要刪除此分組嗎？', 'Are you sure you want to delete this group?'))) {
            try {
                deleteCustomGroup(propertyId, editGroup.key);
                onSave();
                onClose();
            } catch (err) {
                setError(err.message || t('刪除失敗', 'Delete failed'));
            }
        }
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
            backdropFilter: 'blur(4px)'
        }}>
            <div style={{
                background: 'var(--bg-primary, #1a1a2e)',
                borderRadius: '16px',
                padding: '24px',
                width: '90%',
                maxWidth: '450px',
                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
            }}>
                {/* Header */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '20px'
                }}>
                    <h3 style={{ margin: 0, color: 'var(--text-primary, white)', fontSize: '18px' }}>
                        {isEditing ? (isDefault ? '📌 ' : '✏️ ') : '⭐ '}
                        {isEditing
                            ? t('編輯分組', 'Edit Group')
                            : t('新增來源分組', 'Add Source Group')
                        }
                    </h3>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-secondary, #888)',
                            fontSize: '24px',
                            cursor: 'pointer',
                            padding: '4px'
                        }}
                    >
                        ×
                    </button>
                </div>

                {/* Notice for default groups (editable but not deletable) */}
                {isDefault && (
                    <div style={{
                        padding: '12px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: '8px',
                        marginBottom: '16px',
                        color: '#60a5fa',
                        fontSize: '13px'
                    }}>
                        📌 {t('預設分組可以編輯，但無法刪除', 'Default groups can be edited but not deleted')}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    {/* Group Name */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontSize: '13px',
                            fontWeight: 600,
                            color: 'var(--text-secondary, #aaa)'
                        }}>
                            {t('分組名稱', 'Group Name')} *
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={t('例如：付費廣告', 'e.g., Paid Ads')}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px',
                                boxSizing: 'border-box'
                            }}
                        />
                    </div>

                    {/* Name English (optional) */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontSize: '13px',
                            fontWeight: 600,
                            color: 'var(--text-secondary, #aaa)'
                        }}>
                            {t('英文名稱（選填）', 'English Name (optional)')}
                        </label>
                        <input
                            type="text"
                            value={nameEn}
                            onChange={(e) => setNameEn(e.target.value)}
                            placeholder={t('例如：Paid Ads', 'e.g., Paid Ads')}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px',
                                boxSizing: 'border-box'
                            }}
                        />
                    </div>

                    {/* Patterns */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontSize: '13px',
                            fontWeight: 600,
                            color: 'var(--text-secondary, #aaa)'
                        }}>
                            {t('匹配模式', 'Patterns')} *
                        </label>
                        <textarea
                            value={patterns}
                            onChange={(e) => setPatterns(e.target.value)}
                            placeholder={t('多個模式以逗號分隔，例如：cpc, paid, ppc, ads', 'Separate with commas, e.g., cpc, paid, ppc, ads')}
                            rows={3}
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'var(--text-primary, white)',
                                fontSize: '14px',
                                resize: 'vertical',
                                boxSizing: 'border-box'
                            }}
                        />
                        <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted, #666)' }}>
                            💡 {t('會匹配包含這些關鍵字的來源', 'Will match sources containing these keywords')}
                        </div>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div style={{
                            padding: '12px',
                            background: 'rgba(234, 67, 53, 0.1)',
                            border: '1px solid rgba(234, 67, 53, 0.3)',
                            borderRadius: '8px',
                            marginBottom: '16px',
                            color: '#ea4335',
                            fontSize: '13px'
                        }}>
                            ⚠️ {error}
                        </div>
                    )}

                    {/* Buttons */}
                    <div style={{
                        display: 'flex',
                        gap: '12px',
                        justifyContent: 'flex-end'
                    }}>
                        {/* Delete button (only for custom groups in edit mode) */}
                        {isEditing && !isDefault && (
                            <button
                                type="button"
                                onClick={handleDelete}
                                style={{
                                    padding: '10px 20px',
                                    borderRadius: '8px',
                                    border: '1px solid rgba(234, 67, 53, 0.3)',
                                    background: 'rgba(234, 67, 53, 0.1)',
                                    color: '#ea4335',
                                    fontSize: '14px',
                                    cursor: 'pointer',
                                    marginRight: 'auto'
                                }}
                            >
                                🗑️ {t('刪除', 'Delete')}
                            </button>
                        )}

                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
                                background: 'transparent',
                                color: 'var(--text-secondary, #aaa)',
                                fontSize: '14px',
                                cursor: 'pointer'
                            }}
                        >
                            {t('取消', 'Cancel')}
                        </button>

                        {/* Save button (now also for default groups) */}
                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                padding: '10px 24px',
                                borderRadius: '8px',
                                border: 'none',
                                background: 'var(--accent-primary, #6366f1)',
                                color: 'white',
                                fontSize: '14px',
                                fontWeight: '600',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                opacity: loading ? 0.7 : 1
                            }}
                        >
                            {loading ? '...' : t('儲存', 'Save')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SourceGroupModal;
