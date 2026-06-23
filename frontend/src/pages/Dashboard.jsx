import { useEffect, useState } from 'react'
import MetricCard from '../components/MetricCard'
import StatusSelect from '../components/StatusSelect'
import ProgressBar from '../components/ProgressBar'

const DONE_STATUSES = ['Completed']
const STALE_DAYS = 7

function isStale(lastUpdated, status) {
  if (DONE_STATUSES.includes(status)) return false
  if (!lastUpdated) return true
  const diff = (Date.now() - new Date(lastUpdated)) / (1000 * 60 * 60 * 24)
  return diff > STALE_DAYS
}

function fmtDate(str) {
  if (!str) return '—'
  try {
    const d = new Date(str)
    const now = new Date()
    const diff = Math.floor((now - d) / (1000 * 60 * 60 * 24))
    if (diff === 0) return 'Today'
    if (diff === 1) return 'Yesterday'
    if (diff < 7) return `${diff}d ago`
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch { return str?.slice(0, 10) || '—' }
}

export default function Dashboard({ navigate }) {
  const [summary, setSummary] = useState(null)
  const [projects, setProjects] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/summary')
      .then(r => r.json())
      .then(data => {
        setSummary(data)
        setProjects(data.projects)
      })
      .catch(() => setError('Cannot connect to Flask API. Run: bash ~/email-report-automation/start.sh'))
  }, [])

  const updateStatus = (id, status) =>
    setProjects(prev => prev.map(p => p.id === id ? { ...p, status } : p))

  if (error) return <ErrorMsg msg={error} />
  if (!summary) return <Loading />

  const staleCount = projects.filter(p => isStale(p.last_updated, p.status)).length
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>{date}</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>Executive Overview</h1>
          {staleCount > 0 && (
            <span style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.25)', padding: '4px 12px', borderRadius: 99, fontSize: 12, fontWeight: 600 }}>
              {staleCount} project{staleCount > 1 ? 's' : ''} need attention
            </span>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 36 }}>
        <MetricCard value={summary.total_projects} label="Total"     color="#7c3aed" />
        <MetricCard value={summary.on_track}       label="On Track"  color="#22c55e" />
        <MetricCard value={summary.at_risk}        label="At Risk"   color="#f59e0b" />
        <MetricCard value={summary.delayed}        label="Delayed"   color="#ef4444" />
        <MetricCard value={summary.completed}      label="Completed" color="#555" />
      </div>

      {/* Accomplishments + Blockers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
        <Card title="Recent Accomplishments" accent="#22c55e">
          {summary.accomplishments.length === 0 ? <Empty>Nothing recorded yet.</Empty>
            : summary.accomplishments.map((a, i) => (
              <Row key={i} last={i === summary.accomplishments.length - 1}>
                <span style={{ color: '#22c55e', fontSize: 14 }}>✓</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{a}</span>
              </Row>
            ))}
        </Card>
        <Card title="Open Blockers" accent="#ef4444">
          {summary.blockers.length === 0 ? <Empty>No blockers.</Empty>
            : summary.blockers.map((b, i) => (
              <Row key={i} last={i === summary.blockers.length - 1}>
                <span style={{ color: '#ef4444', fontSize: 14 }}>!</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{b}</span>
              </Row>
            ))}
        </Card>
      </div>

      {/* Projects table */}
      <Card title="All Projects">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              {['Project', 'Customer', 'Status', 'Progress', 'Owner', 'Last Updated'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid var(--border)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {projects.map(p => {
              const stale = isStale(p.last_updated, p.status)
              return (
                <tr key={p.id}
                  style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s', background: stale ? 'rgba(239,68,68,0.03)' : 'transparent' }}
                  onMouseEnter={e => e.currentTarget.style.background = stale ? 'rgba(239,68,68,0.07)' : 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = stale ? 'rgba(239,68,68,0.03)' : 'transparent'}
                >
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {stale && <span title="No update in 7+ days" style={{ color: '#ef4444', fontSize: 16, lineHeight: 1 }}>⚑</span>}
                      <button onClick={() => navigate('project', p.id)}
                        style={{ background: 'none', border: 'none', color: stale ? '#ef4444' : 'var(--text-primary)', cursor: 'pointer', fontWeight: 600, fontSize: 13, padding: 0, textAlign: 'left' }}>
                        {p.name}
                      </button>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{p.customer || '—'}</td>
                  <td style={{ padding: '14px 16px' }} onClick={e => e.stopPropagation()}>
                    <StatusSelect projectId={p.id} value={p.status} onChange={s => updateStatus(p.id, s)} />
                  </td>
                  <td style={{ padding: '14px 16px', minWidth: 140 }}><ProgressBar value={p.progress} /></td>
                  <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{p.owner}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ fontSize: 12, color: stale ? '#ef4444' : 'var(--text-muted)', fontWeight: stale ? 600 : 400 }}>
                      {fmtDate(p.last_updated)}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function Card({ title, accent, children }) {
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
        {accent && <div style={{ width: 3, height: 14, borderRadius: 99, background: accent }} />}
        <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{title}</h2>
      </div>
      <div style={{ padding: '4px 20px 12px' }}>{children}</div>
    </div>
  )
}

function Row({ children, last }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '10px 0', borderBottom: last ? 'none' : '1px solid var(--border)' }}>
      {children}
    </div>
  )
}

function Empty({ children }) {
  return <p style={{ color: 'var(--text-muted)', fontSize: 13, padding: '12px 0' }}>{children}</p>
}

function Loading() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 32, height: 32, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    </div>
  )
}

function ErrorMsg({ msg }) {
  return (
    <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius)', padding: 20, color: '#ef4444', fontSize: 13 }}>
      {msg}
    </div>
  )
}
