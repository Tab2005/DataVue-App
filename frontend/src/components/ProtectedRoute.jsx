import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('google_token');

    if (!token) {
        // If no token found, redirect to login page
        return <Navigate to="/login" replace />;
    }

    return children;
};

export default ProtectedRoute;
