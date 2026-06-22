export default function MetricCard({ value, label, color = '#3b82f6' }) {
  return (
    <div style={{
      background: 'white',
      borderRadius: 12,
      padding: '20px 24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      borderTop: `4px solid ${color}`,
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 40, fontWeight: 700, color, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 13, color: '#64748b', marginTop: 6, fontWeight: 500 }}>{label}</div>
    </div>
  )
}
