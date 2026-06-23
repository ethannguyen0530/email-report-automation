export default function MetricCard({ value, label, color = '#7c3aed', icon }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '22px 24px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'var(--transition)',
    }}
    onMouseEnter={e => e.currentTarget.style.borderColor = color + '55'}
    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: 80, height: 80,
        background: `radial-gradient(circle at top right, ${color}22, transparent 70%)`,
        pointerEvents: 'none',
      }} />
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 10 }}>{label}</div>
      <div style={{ fontSize: 36, fontWeight: 700, color, lineHeight: 1, letterSpacing: '-1px' }}>{value}</div>
    </div>
  )
}
