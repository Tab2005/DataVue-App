import {
    cardStyle,
    histItemStyle,
    inpStyle,
    labelSt,
    panelStyle,
    ROAS_COLOR,
    scoreColor,
    selStyle,
} from './scoreLabShared';

export const AccessScreen = ({ isMobile, t, loading }) => (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
        <section style={panelStyle}>
            <h1 style={{ margin: '0 0 8px', color: 'var(--text-primary)' }}>{t('Score Lab', '評分工作台')}</h1>
            <div style={{ color: 'var(--text-secondary)' }}>
                {loading
                    ? t('Checking workspace access...', '正在確認工作區權限...')
                    : t('No access to Meta Andromeda in this workspace.', '此工作區無 Meta Andromeda 存取權限。')}
            </div>
        </section>
    </div>
);

export const SelectField = ({ label, value, onChange, children }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{label}</span>
        <select value={value} onChange={e => onChange(e.target.value)} style={selStyle}>
            {children}
        </select>
    </label>
);

export const InputField = ({ label, value, onChange, placeholder }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{label}</span>
        <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={inpStyle} />
    </label>
);

export const TextAreaField = ({ label, value, onChange, placeholder }) => (
    <label style={{ display: 'grid', gap: '5px' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{label}</span>
        <textarea value={value} onChange={e => onChange(e.target.value)} rows={3} placeholder={placeholder} style={inpStyle} />
    </label>
);

export const ScoreGauge = ({ score }) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
        <div style={{
            width: '88px',
            height: '88px',
            borderRadius: '50%',
            border: `5px solid ${scoreColor(score)}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: `${scoreColor(score)}18`,
        }}>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: scoreColor(score) }}>
                {score ?? '--'}
            </span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>/ 100</span>
    </div>
);

export const Badge = ({ children, color }) => (
    <span style={{
        padding: '2px 9px',
        borderRadius: '999px',
        fontSize: '0.72rem',
        fontWeight: 700,
        background: `${color}22`,
        color,
    }}>
        {children}
    </span>
);

export const DriverList = ({ items, color, labelKey }) => (
    <div style={cardStyle}>
        <div style={labelSt}>{labelKey}</div>
        {items && items.length > 0
            ? (
                <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                    {items.map(d => <li key={d} style={{ color }}>{d}</li>)}
                </ul>
            )
            : <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>--</div>
        }
    </div>
);

export const HistoryItem = ({ item, selected, onClick }) => (
    <button
        type="button"
        onClick={onClick}
        style={{
            ...histItemStyle,
            borderColor: selected ? 'var(--accent-primary)' : 'var(--glass-border)',
            background: selected ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.01)',
        }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.score_event_id}
            </span>
            <div style={{ display: 'flex', gap: '5px', flexShrink: 0 }}>
                {item.overall_score != null && (
                    <Badge color={scoreColor(item.overall_score)}>{item.overall_score}</Badge>
                )}
                {item.roas_band && (
                    <Badge color={ROAS_COLOR[item.roas_band]}>{item.roas_band.toUpperCase()}</Badge>
                )}
            </div>
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', marginTop: '3px' }}>
            {item.objective} · {item.placement_family} · {item.market}
        </div>
    </button>
);
