export default function MetricCard({ value, label, color = '#7c3aed', onClick, active }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: active ? `${color}18` : 'var(--bg-card)',
        border: `1px solid ${active ? color + '66' : 'var(--border)'}`,
        borderRadius: 'var(--radius)',
        padding: '22px 24px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'var(--transition)',
        cursor: onClick ? 'pointer' : 'default',
        transform: active ? 'translateY(-1px)' : 'none',
        boxShadow: active ? `0 4px 20px ${color}22` : 'none',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = color + '88'; e.currentTarget.style.transform = 'translateY(-1px)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = active ? color + '66' : 'var(--border)'; e.currentTarget.style.transform = active ? 'translateY(-1px)' : 'none' }}
    >
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: 80, height: 80,
        background: `radial-gradient(circle at top right, ${color}${active ? '44' : '22'}, transparent 70%)`,
        pointerEvents: 'none',
        transition: 'var(--transition)',
      }} />
      <div style={{ fontSize: 11, color: active ? color : 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 10, transition: 'var(--transition)' }}>{label}</div>
      <div style={{ fontSize: 36, fontWeight: 700, color, lineHeight: 1, letterSpacing: '-1px' }}>{value}</div>
      {active && <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: color, opacity: 0.7 }} />}
    </div>
  )
}
