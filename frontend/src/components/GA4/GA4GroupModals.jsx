import React from 'react';
import { deleteCustomContentGroup, saveCustomContentGroup } from '../../utils/contentGroups';
import ContentGroupModal from '../ContentGroupModal';
import SourceGroupModal from '../SourceGroupModal';

const GA4GroupModals = ({
    analyticsData,
    contentDimension,
    editingContentGroup,
    editingGroup,
    language,
    reloadContentGroups,
    reloadSourceGroups,
    selectedProperty,
    setContentTypeFilter,
    setEditingContentGroup,
    setEditingGroup,
    setShowContentGroupModal,
    setShowGroupModal,
    showContentGroupModal,
    showGroupModal
}) => (
    <>
        <SourceGroupModal
            isOpen={showGroupModal}
            onClose={() => {
                setShowGroupModal(false);
                setEditingGroup(null);
            }}
            onSave={reloadSourceGroups}
            propertyId={selectedProperty}
            editGroup={editingGroup}
            language={language}
        />

        <ContentGroupModal
            isOpen={showContentGroupModal}
            onClose={() => {
                setShowContentGroupModal(false);
                setEditingContentGroup(null);
            }}
            onSave={(group) => {
                saveCustomContentGroup(selectedProperty, group);
                reloadContentGroups();
            }}
            onDelete={(groupKey) => {
                deleteCustomContentGroup(selectedProperty, groupKey);
                setContentTypeFilter('all');
                reloadContentGroups();
            }}
            group={editingContentGroup}
            language={language}
            previewData={analyticsData?.rows || []}
            dimension={contentDimension}
        />
    </>
);

export default GA4GroupModals;
