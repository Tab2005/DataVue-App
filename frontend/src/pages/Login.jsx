import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate, Link } from 'react-router-dom';

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

        // Check for return_to param
        const params = new URLSearchParams(window.location.search);
        const returnTo = params.get('return_to');

        if (returnTo) {
            navigate(decodeURIComponent(returnTo));
        } else {
            navigate('/dashboard');
        }
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
                textAlign: 'center',
                maxWidth: '420px',
                width: '90%'
            }}>
                <h1 style={{ marginBottom: '12px' }}>歡迎使用 DataVue</h1>
                <p style={{ marginBottom: '28px', color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    請使用 Google 帳號登入以進入分析儀表板
                </p>

                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
                    <GoogleLogin
                        onSuccess={handleSuccess}
                        onError={handleError}
                        theme="filled_black"
                        shape="pill"
                    />
                </div>

                <div style={{
                    marginTop: '24px',
                    paddingTop: '16px',
                    borderTop: '1px solid var(--border-color, rgba(255,255,255,0.1))',
                    fontSize: '0.8rem',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '16px'
                }}>
                    <Link to="/privacy" style={{ color: 'inherit', textDecoration: 'underline' }}>隱私權政策</Link>
                    <span>•</span>
                    <Link to="/terms" style={{ color: 'inherit', textDecoration: 'underline' }}>服務條款</Link>
                </div>
            </div>
        </div>
    );
};

export default Login;
