import React from 'react';
import { FiSave, FiUser, FiUsers } from 'react-icons/fi';

const SaveViewModal = ({
    isOpen,
    selectedMetrics,
    selectedTeamId,
    newViewName,
    saveToTeam,
    txt,
    onClose,
    onNameChange,
    onSaveToTeamChange,
    onSave
}) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="save-modal" onClick={e => e.stopPropagation()}>
                <h3><FiSave /> {txt.saveView}</h3>
                <p>{selectedMetrics.size} {txt.metricsCount} {txt.selected.toLowerCase()}</p>
                <input
                    type="text"
                    value={newViewName}
                    onChange={(e) => onNameChange(e.target.value)}
                    placeholder={txt.viewNamePlaceholder}
                    autoFocus
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') onSave();
                        if (e.key === 'Escape') onClose();
                    }}
                />

                {selectedTeamId && (
                    <div className="save-scope-toggle">
                        <button
                            onClick={() => onSaveToTeamChange(false)}
                            className={!saveToTeam ? 'active personal' : ''}
                        >
                            <FiUser /> {txt.personal}
                        </button>
                        <button
                            onClick={() => onSaveToTeamChange(true)}
                            className={saveToTeam ? 'active team' : ''}
                        >
                            <FiUsers /> {txt.team}
                        </button>
                    </div>
                )}

                <div className="modal-actions">
                    <button onClick={onClose} className="btn-secondary">
                        {txt.cancel}
                    </button>
                    <button onClick={onSave} className="btn-primary" disabled={!newViewName.trim()}>
                        <FiSave /> {txt.save}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SaveViewModal;
