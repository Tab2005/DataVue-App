import React from 'react';

const DeviceTab = ({ context }) => {
    const {
        analytics,
        DEVICE_NAMES,
        language,
        t,
        tableContainerStyle,
        tableHeaderStyle
    } = context;

    return (
                        /* Device Distribution Tab */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>📱 {t('裝置分佈', 'Traffic by Device')}</span>
                            </div>

                            {/* Device Cards */}
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '16px',
                                padding: '16px'
                            }}>
                                {(() => {
                                    const totalClicks = analytics.reduce((sum, row) => sum + row.clicks, 0);
                                    return analytics.map((row, idx) => {
                                        const deviceType = row.keys?.[0] || 'UNKNOWN';
                                        const device = DEVICE_NAMES[deviceType] || { zh: deviceType, en: deviceType, color: '#6B7280' };
                                        const sharePercent = totalClicks > 0 ? (row.clicks / totalClicks * 100) : 0;

                                        return (
                                            <div key={idx} style={{
                                                background: 'var(--bg-primary)',
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '12px',
                                                padding: '20px',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '12px'
                                            }}>
                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center'
                                                }}>
                                                    <span style={{
                                                        fontSize: '18px',
                                                        fontWeight: '600',
                                                        color: device.color
                                                    }}>
                                                        {language === 'zh' ? device.zh : device.en}
                                                    </span>
                                                    <span style={{
                                                        fontSize: '24px',
                                                        fontWeight: '700',
                                                        color: device.color
                                                    }}>
                                                        {sharePercent.toFixed(1)}%
                                                    </span>
                                                </div>

                                                {/* Progress bar */}
                                                <div style={{
                                                    width: '100%',
                                                    height: '8px',
                                                    background: 'var(--bg-hover)',
                                                    borderRadius: '4px',
                                                    overflow: 'hidden'
                                                }}>
                                                    <div style={{
                                                        width: `${sharePercent}%`,
                                                        height: '100%',
                                                        background: device.color,
                                                        borderRadius: '4px',
                                                        transition: 'width 0.5s ease'
                                                    }} />
                                                </div>

                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    fontSize: '13px',
                                                    color: 'var(--text-secondary)'
                                                }}>
                                                    <span>{t('點擊', 'Clicks')}: <strong style={{ color: 'var(--text-primary)' }}>{row.clicks.toLocaleString()}</strong></span>
                                                    <span>{t('曝光', 'Impr.')}: <strong style={{ color: 'var(--text-primary)' }}>{row.impressions.toLocaleString()}</strong></span>
                                                </div>

                                                <div style={{
                                                    fontSize: '12px',
                                                    color: 'var(--text-secondary)'
                                                }}>
                                                    CTR: {(row.ctr * 100).toFixed(2)}% | {t('排名', 'Pos')}: {row.position.toFixed(1)}
                                                </div>
                                            </div>
                                        );
                                    });
                                })()}
                            </div>
                        </div>
    );
};

export default DeviceTab;
