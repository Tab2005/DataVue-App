import React from 'react';
import RegularDataTab from './RegularDataTab';

const QueryTab = ({ context }) => (
    <RegularDataTab context={{ ...context, activeTab: 'query' }} />
);

export default QueryTab;
