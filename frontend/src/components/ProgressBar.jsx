export default function ProgressBar({ value }) {
  const color = value >= 75 ? '#22c55e' : value >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, background: '#e2e8f0', borderRadius: 99, height: 8, overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, background: color, height: '100%', borderRadius: 99, transition: 'width 0.4s' }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color: '#64748b', width: 34, textAlign: 'right' }}>{value}%</span>
    </div>
  )
}
