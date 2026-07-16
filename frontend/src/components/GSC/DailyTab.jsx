import React from 'react';
import RegularDataTab from './RegularDataTab';

const DailyTab = ({ context }) => (
    <RegularDataTab context={{ ...context, activeTab: 'daily' }} />
);

export default DailyTab;
