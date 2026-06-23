const styles = {
  'On Track':   { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',   dot: '#22c55e' },
  'At Risk':    { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  dot: '#f59e0b' },
  'Delayed':    { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   dot: '#ef4444' },
  'Completed':  { color: '#888',    bg: 'rgba(136,136,136,0.1)', dot: '#555' },
  'In Progress':{ color: '#a855f7', bg: 'rgba(168,85,247,0.1)', dot: '#a855f7' },
}

export default function StatusBadge({ status }) {
  const s = styles[status] || styles['In Progress']
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: s.bg,
      color: s.color,
      padding: '3px 9px',
      borderRadius: 99,
      fontSize: 11,
      fontWeight: 600,
      whiteSpace: 'nowrap',
      border: `1px solid ${s.color}33`,
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: s.dot, flexShrink: 0 }} />
      {status}
    </span>
  )
}
