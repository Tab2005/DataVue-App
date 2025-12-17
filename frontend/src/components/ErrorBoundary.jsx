import React from 'react';

/**
 * ErrorBoundary Component
 * 
 * Catches JavaScript errors anywhere in the child component tree,
 * logs the error, and displays a fallback UI instead of crashing the whole app.
 * 
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * 
 * Or with custom fallback:
 * <ErrorBoundary fallback={<CustomErrorUI />}>
 *   <YourComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // Log error to console (could also send to error reporting service)
        console.error('[ErrorBoundary] Caught error:', error);
        console.error('[ErrorBoundary] Error info:', errorInfo);

        this.setState({ errorInfo });

        // Optional: Send to error reporting service
        // logErrorToService(error, errorInfo);
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        });
    };

    render() {
        if (this.state.hasError) {
            // Custom fallback UI provided via props
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default fallback UI
            return (
                <div style={styles.container}>
                    <div style={styles.card}>
                        <div style={styles.iconContainer}>
                            <span style={styles.icon}>⚠️</span>
                        </div>
                        <h2 style={styles.title}>發生錯誤 / Something went wrong</h2>
                        <p style={styles.message}>
                            此區塊發生未預期的錯誤。請嘗試重新整理頁面。
                        </p>
                        <p style={styles.messageEn}>
                            An unexpected error occurred. Please try refreshing the page.
                        </p>

                        <div style={styles.buttonContainer}>
                            <button
                                style={styles.primaryButton}
                                onClick={() => window.location.reload()}
                            >
                                重新整理 / Refresh
                            </button>
                            <button
                                style={styles.secondaryButton}
                                onClick={this.handleReset}
                            >
                                重試 / Try Again
                            </button>
                        </div>

                        {/* Show error details in development */}
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <details style={styles.details}>
                                <summary style={styles.summary}>錯誤詳情 / Error Details</summary>
                                <pre style={styles.errorText}>
                                    {this.state.error.toString()}
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </details>
                        )}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

const styles = {
    container: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        padding: '20px',
    },
    card: {
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        padding: '32px',
        maxWidth: '500px',
        width: '100%',
        textAlign: 'center',
        border: '1px solid rgba(255, 255, 255, 0.1)',
    },
    iconContainer: {
        marginBottom: '16px',
    },
    icon: {
        fontSize: '48px',
    },
    title: {
        color: '#fff',
        fontSize: '1.25rem',
        fontWeight: '600',
        marginBottom: '12px',
    },
    message: {
        color: 'rgba(255, 255, 255, 0.7)',
        fontSize: '0.95rem',
        marginBottom: '4px',
    },
    messageEn: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: '0.85rem',
        marginBottom: '24px',
    },
    buttonContainer: {
        display: 'flex',
        gap: '12px',
        justifyContent: 'center',
        flexWrap: 'wrap',
    },
    primaryButton: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: '#fff',
        border: 'none',
        borderRadius: '8px',
        padding: '10px 24px',
        fontSize: '0.9rem',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
    },
    secondaryButton: {
        background: 'rgba(255, 255, 255, 0.1)',
        color: '#fff',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '8px',
        padding: '10px 24px',
        fontSize: '0.9rem',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'transform 0.2s',
    },
    details: {
        marginTop: '24px',
        textAlign: 'left',
    },
    summary: {
        color: 'rgba(255, 255, 255, 0.5)',
        cursor: 'pointer',
        fontSize: '0.85rem',
    },
    errorText: {
        background: 'rgba(0, 0, 0, 0.3)',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '0.75rem',
        color: '#ff6b6b',
        overflow: 'auto',
        maxHeight: '200px',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
    },
};

export default ErrorBoundary;
