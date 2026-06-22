import { useEffect, useState } from 'react'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import ProgressBar from '../components/ProgressBar'

export default function Dashboard({ navigate }) {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/summary')
      .then(r => r.json())
      .then(setSummary)
      .catch(() => setError('Could not connect to Flask API. Make sure it\'s running on port 5000.'))
  }, [])

  if (error) return <ErrorMsg msg={error} />
  if (!summary) return <Loading />

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: '#1e293b' }}>Executive Project Summary</h1>
        <p style={{ color: '#64748b', marginTop: 4, fontSize: 14 }}>
          {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        <MetricCard value={summary.total_projects} label="Total Projects" color="#3b82f6" />
        <MetricCard value={summary.on_track}      label="On Track"       color="#22c55e" />
        <MetricCard value={summary.at_risk}       label="At Risk"        color="#f59e0b" />
        <MetricCard value={summary.delayed}       label="Delayed"        color="#ef4444" />
        <MetricCard value={summary.completed}     label="Completed"      color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>
        {/* Accomplishments */}
        <Card title="Recent Accomplishments">
          {summary.accomplishments.length === 0
            ? <Empty>No accomplishments recorded yet.</Empty>
            : summary.accomplishments.map((a, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 0', borderBottom: i < summary.accomplishments.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <span style={{ color: '#22c55e', fontSize: 18, lineHeight: 1 }}>✓</span>
                <span style={{ fontSize: 14, color: '#374151' }}>{a}</span>
              </div>
            ))
          }
        </Card>

        {/* Blockers */}
        <Card title="Open Blockers">
          {summary.blockers.length === 0
            ? <Empty>No blockers reported.</Empty>
            : summary.blockers.map((b, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 0', borderBottom: i < summary.blockers.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <span style={{ color: '#ef4444', fontSize: 18, lineHeight: 1 }}>!</span>
                <span style={{ fontSize: 14, color: '#374151' }}>{b}</span>
              </div>
            ))
          }
        </Card>
      </div>

      {/* Projects table */}
      <Card title="All Projects">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Project', 'Customer', 'Status', 'Progress', 'Owner'].map(h => (
                <th key={h} style={{ padding: '10px 14px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {summary.projects.map(([id, name, customer, status, progress, owner]) => (
              <tr key={id} style={{ borderBottom: '1px solid #f1f5f9' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                  onMouseLeave={e => e.currentTarget.style.background = 'white'}>
                <td style={{ padding: '12px 14px' }}>
                  <button onClick={() => navigate('project', id)}
                    style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontWeight: 600, fontSize: 14, padding: 0 }}>
                    {name}
                  </button>
                </td>
                <td style={{ padding: '12px 14px', color: '#374151' }}>{customer || 'N/A'}</td>
                <td style={{ padding: '12px 14px' }}><StatusBadge status={status} /></td>
                <td style={{ padding: '12px 14px', minWidth: 160 }}><ProgressBar value={progress} /></td>
                <td style={{ padding: '12px 14px', color: '#374151' }}>{owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function Card({ title, children }) {
  return (
    <div style={{ background: 'white', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9' }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>{title}</h2>
      </div>
      <div style={{ padding: '4px 20px 16px' }}>{children}</div>
    </div>
  )
}

function Empty({ children }) {
  return <p style={{ color: '#94a3b8', fontSize: 14, padding: '12px 0' }}>{children}</p>
}

function Loading() {
  return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>Loading...</div>
}

function ErrorMsg({ msg }) {
  return (
    <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 8, padding: 20, color: '#991b1b', fontSize: 14 }}>
      {msg}
    </div>
  )
}
