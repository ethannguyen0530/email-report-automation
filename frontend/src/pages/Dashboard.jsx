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
      .catch(() => setError('Cannot connect to Flask API on port 5001.'))
  }, [])

  if (error) return <ErrorMsg msg={error} />
  if (!summary) return <Loading />

  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

  return (
    <div style={{ maxWidth: 1100 }}>
      {/* Page header */}
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>{date}</p>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px', color: 'var(--text-primary)' }}>
          Executive Overview
        </h1>
      </div>

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 36 }}>
        <MetricCard value={summary.total_projects} label="Total"     color="#7c3aed" />
        <MetricCard value={summary.on_track}       label="On Track"  color="#22c55e" />
        <MetricCard value={summary.at_risk}        label="At Risk"   color="#f59e0b" />
        <MetricCard value={summary.delayed}        label="Delayed"   color="#ef4444" />
        <MetricCard value={summary.completed}      label="Completed" color="#555" />
      </div>

      {/* Two-col: accomplishments + blockers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
        <Card title="Recent Accomplishments" accent="#22c55e">
          {summary.accomplishments.length === 0
            ? <Empty>Nothing yet.</Empty>
            : summary.accomplishments.map((a, i) => (
              <Row key={i} last={i === summary.accomplishments.length - 1}>
                <span style={{ color: '#22c55e', fontSize: 14, marginTop: 1 }}>✓</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{a}</span>
              </Row>
            ))
          }
        </Card>

        <Card title="Open Blockers" accent="#ef4444">
          {summary.blockers.length === 0
            ? <Empty>No blockers.</Empty>
            : summary.blockers.map((b, i) => (
              <Row key={i} last={i === summary.blockers.length - 1}>
                <span style={{ color: '#ef4444', fontSize: 14, marginTop: 1 }}>!</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{b}</span>
              </Row>
            ))
          }
        </Card>
      </div>

      {/* Projects table */}
      <Card title="All Projects">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              {['Project', 'Customer', 'Status', 'Progress', 'Owner'].map(h => (
                <th key={h} style={{
                  padding: '10px 16px', textAlign: 'left',
                  color: 'var(--text-muted)', fontWeight: 600, fontSize: 11,
                  textTransform: 'uppercase', letterSpacing: '0.08em',
                  borderBottom: '1px solid var(--border)',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {summary.projects.map(([id, name, customer, status, progress, owner]) => (
              <tr key={id}
                style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                onClick={() => navigate('project', id)}
              >
                <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>{name}</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{customer || '—'}</td>
                <td style={{ padding: '14px 16px' }}><StatusBadge status={status} /></td>
                <td style={{ padding: '14px 16px', minWidth: 140 }}><ProgressBar value={progress} /></td>
                <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function Card({ title, accent, children }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {accent && <div style={{ width: 3, height: 14, borderRadius: 99, background: accent }} />}
        <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.1px' }}>{title}</h2>
      </div>
      <div style={{ padding: '4px 20px 12px' }}>{children}</div>
    </div>
  )
}

function Row({ children, last }) {
  return (
    <div style={{
      display: 'flex', gap: 10, alignItems: 'flex-start',
      padding: '10px 0',
      borderBottom: last ? 'none' : '1px solid var(--border)',
    }}>
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
