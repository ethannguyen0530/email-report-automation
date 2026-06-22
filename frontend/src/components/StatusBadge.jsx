const colors = {
  'On Track':  { bg: '#dcfce7', color: '#166534' },
  'At Risk':   { bg: '#fef9c3', color: '#854d0e' },
  'Delayed':   { bg: '#fee2e2', color: '#991b1b' },
  'Completed': { bg: '#e2e8f0', color: '#334155' },
  'In Progress':{ bg: '#dbeafe', color: '#1e40af' },
}

export default function StatusBadge({ status }) {
  const style = colors[status] || { bg: '#e2e8f0', color: '#334155' }
  return (
    <span style={{
      background: style.bg,
      color: style.color,
      padding: '3px 10px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {status}
    </span>
  )
}
