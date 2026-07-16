import React from 'react';
import RegularDataTab from './RegularDataTab';

const PageTab = ({ context }) => (
    <RegularDataTab context={{ ...context, activeTab: 'page' }} />
);

export default PageTab;
