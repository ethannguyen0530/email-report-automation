export default function ProgressBar({ value }) {
  const color = value >= 75 ? '#22c55e' : value >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, background: 'rgba(13,6,31,0.08)', borderRadius: 99, height: 5, overflow: 'hidden' }}>
        <div style={{
          width: `${value}%`,
          background: `linear-gradient(90deg, ${color}99, ${color})`,
          height: '100%', borderRadius: 99,
          boxShadow: `0 0 6px ${color}66`,
          transition: 'width 0.5s ease',
        }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', width: 32, textAlign: 'right' }}>{value}%</span>
    </div>
  )
}
