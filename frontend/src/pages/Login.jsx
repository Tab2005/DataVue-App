import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const navigate = useNavigate();

    const handleSuccess = (credentialResponse) => {
        console.log('Login Success:', credentialResponse);
        const token = credentialResponse.credential;

        // Store the token
        localStorage.setItem('google_token', token);

        // Decode user info
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));

            const userInfo = JSON.parse(jsonPayload);
            localStorage.setItem('user_info', JSON.stringify(userInfo));
        } catch (error) {
            console.error('Failed to decode JWT', error);
        }

        // Redirect to dashboard
        navigate('/');
    };

    const handleError = () => {
        console.log('Login Failed');
        alert('Login Failed. Please try again.');
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            backgroundColor: 'var(--bg-primary)',
            color: 'var(--text-primary)'
        }}>
            <div style={{
                padding: '40px',
                borderRadius: 'var(--radius-xl)',
                backgroundColor: 'var(--bg-secondary)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                textAlign: 'center'
            }}>
                <h1 style={{ marginBottom: '24px' }}>Welcome Back</h1>
                <p style={{ marginBottom: '32px', color: 'var(--text-secondary)' }}>
                    Please sign in to access the dashboard.
                </p>

                <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <GoogleLogin
                        onSuccess={handleSuccess}
                        onError={handleError}
                        theme="filled_black"
                        shape="pill"
                    />
                </div>
            </div>
        </div>
    );
};

export default Login;
