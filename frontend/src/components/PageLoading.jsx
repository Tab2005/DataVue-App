import React from 'react';
import './PageLoading.css';

/**
 * PageLoading Component
 * Used as Suspense fallback for lazy-loaded pages
 */
const PageLoading = () => {
    return (
        <div className="page-loading">
            <div className="page-loading-spinner">
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
                <div className="spinner-ring"></div>
            </div>
            <p className="page-loading-text">Loading...</p>
        </div>
    );
};

export default PageLoading;
