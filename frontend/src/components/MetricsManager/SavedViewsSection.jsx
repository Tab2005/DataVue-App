import React from 'react';
import { FiEdit, FiFolder, FiTrash2, FiUser, FiUsers } from 'react-icons/fi';

const SavedViewsSection = ({ savedViews, txt, onLoadView, onEditView, onDeleteView }) => {
    if (savedViews.length === 0) return null;

    return (
        <div className="saved-views-section">
            <h3><FiFolder /> {txt.savedViews}</h3>
            <div className="saved-views-list">
                {savedViews.map(view => (
                    <div key={view.id} className="saved-view-item">
                        <div className="view-info">
                            {view.is_personal ? (
                                <FiUser className="view-icon" style={{ color: 'var(--accent-primary)' }} />
                            ) : (
                                <FiUsers className="view-icon" style={{ color: '#10b981' }} />
                            )}
                            <span className="view-name">{view.name}</span>
                            <span
                                className="view-type-badge"
                                style={{
                                    backgroundColor: view.is_personal ? 'rgba(45, 136, 255, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                                    color: view.is_personal ? 'var(--accent-primary)' : '#10b981',
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    fontSize: '0.7rem',
                                    fontWeight: 500
                                }}
                            >
                                {view.is_personal ? txt.personal : txt.team}
                            </span>
                            <span className="view-count">{view.metrics.length} {txt.metricsCount}</span>
                        </div>
                        <div className="view-actions">
                            <button onClick={() => onLoadView(view)} className="btn-load" title={txt.load}>
                                {txt.load}
                            </button>
                            <button onClick={() => onEditView(view)} className="btn-edit" title={txt.edit}>
                                <FiEdit />
                            </button>
                            <button onClick={() => onDeleteView(view.id)} className="btn-delete" title={txt.delete}>
                                <FiTrash2 />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SavedViewsSection;
