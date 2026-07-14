import React from 'react';

const fieldStyle = {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)'
};

const FacebookSettingsTab = ({
    fbData,
    fbLoading,
    handleFbSubmit,
    language,
    setFbData,
    t,
    teamId,
    teamName,
    tokenInfo,
}) => (
    <>
        {teamId && (
            <div style={{
                marginBottom: '20px', padding: '12px', borderRadius: '8px',
                backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#60a5fa', fontSize: '0.9rem'
            }}>
                {language === 'zh'
                    ? `⚠️ 您正在為團隊「${teamName}」設定 API。此 Token 將授權給團隊所有成員查看廣告數據。`
                    : `⚠️ You are setting API for team "${teamName}". This token will allow all team members to view ad data.`}
            </div>
        )}

        {tokenInfo && (
            <>
                {tokenInfo.expires_at && tokenInfo.token_exists === false && (
                    <div style={{
                        marginBottom: '20px', padding: '12px', borderRadius: '8px',
                        backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
                            <span>⚠️</span>
                            <span>{language === 'zh' ? '權杖資料不同步' : 'Token Data Out of Sync'}</span>
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                            {language === 'zh'
                                ? `到期日期 ${new Date(tokenInfo.expires_at).toLocaleDateString()} 存在，但實際權杖遺失。請重新設定連線。`
                                : `Expiration date ${new Date(tokenInfo.expires_at).toLocaleDateString()} exists, but actual token is missing. Please reconnect.`
                            }
                        </div>
                    </div>
                )}

                {tokenInfo.expires_at && tokenInfo.token_exists !== false && (
                    <div style={{
                        marginBottom: '20px', padding: '12px', borderRadius: '8px',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)', border: '1px solid rgba(74, 222, 128, 0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                    }}>
                        <div>
                            <div style={{ color: '#4ade80', fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '4px' }}>
                                {language === 'zh' ? '✓ 權杖狀態正常' : '✓ Token Active'}
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                {language === 'zh' ? '到期時間: ' : 'Exp: '}
                                {new Date(tokenInfo.expires_at).toLocaleDateString()}
                            </div>
                        </div>
                        <div style={{
                            background: '#4ade80', color: 'black', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold'
                        }}>
                            {tokenInfo.days_remaining} {language === 'zh' ? '天後到期' : 'Days Left'}
                        </div>
                    </div>
                )}

                {!tokenInfo.expires_at && (
                    <div style={{
                        marginBottom: '20px', padding: '12px', borderRadius: '8px',
                        backgroundColor: tokenInfo.error ? 'rgba(248, 113, 113, 0.1)' : 'rgba(100, 100, 100, 0.1)',
                        border: tokenInfo.error ? '1px solid rgba(248, 113, 113, 0.3)' : '1px solid rgba(100, 100, 100, 0.2)',
                        color: tokenInfo.error ? '#f87171' : 'var(--text-secondary)',
                        fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px'
                    }}>
                        <span>{tokenInfo.error ? '⚠️' : '⚪'}</span>
                        {tokenInfo.error
                            ? (language === 'zh' ? '無法連線到後端服務 (Timeout)' : 'Connection Timeout / Server Error')
                            : (language === 'zh' ? '尚未連線或權杖已過期' : 'Not Connected or Token Expired')
                        }
                    </div>
                )}
            </>
        )}

        <form onSubmit={handleFbSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.appId}</label>
                <input type="text" required value={fbData.appId} onChange={(e) => setFbData({ ...fbData, appId: e.target.value })}
                    style={fieldStyle} />
            </div>
            <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.appSecret}</label>
                <input type="password" required value={fbData.appSecret} onChange={(e) => setFbData({ ...fbData, appSecret: e.target.value })}
                    style={fieldStyle} />
            </div>
            <div>
                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>{t.fb.shortToken}</label>
                <input type="password" required value={fbData.shortToken} onChange={(e) => setFbData({ ...fbData, shortToken: e.target.value })}
                    style={fieldStyle} />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '16px', justifyContent: 'flex-end' }}>
                <button type="submit" disabled={fbLoading}
                    style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', background: fbLoading ? 'gray' : 'var(--accent-primary)', color: 'white', cursor: fbLoading ? 'not-allowed' : 'pointer' }}>
                    {fbLoading ? t.common.processing : t.fb.save}
                </button>
            </div>
        </form>
    </>
);

export default FacebookSettingsTab;
