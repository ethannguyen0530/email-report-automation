import { useEffect, useState } from 'react'
import StatusBadge from '../components/StatusBadge'
import ProgressBar from '../components/ProgressBar'

export default function ProjectDetail({ id, navigate }) {
  const [project, setProject] = useState(null)

  useEffect(() => {
    fetch(`/api/projects/${id}`)
      .then(r => r.json())
      .then(setProject)
  }, [id])

  if (!project) return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>Loading...</div>

  return (
    <div>
      <button onClick={() => navigate('dashboard')}
        style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: 14, marginBottom: 20, padding: 0 }}>
        ← Back to Dashboard
      </button>

      <div style={{ background: 'white', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', padding: 28, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>{project.name}</h1>
            <p style={{ color: '#64748b', fontSize: 14 }}>
              Customer: <strong style={{ color: '#374151' }}>{project.customer || 'N/A'}</strong>
              {' · '}Owner: <strong style={{ color: '#374151' }}>{project.owner}</strong>
            </p>
          </div>
          <StatusBadge status={project.status} />
        </div>
        <div style={{ marginTop: 20, maxWidth: 360 }}>
          <p style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Progress</p>
          <ProgressBar value={project.progress} />
        </div>
      </div>

      <div style={{ background: 'white', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9' }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>Update History</h2>
        </div>
        {project.updates.length === 0
          ? <p style={{ padding: 20, color: '#94a3b8', fontSize: 14 }}>No updates recorded.</p>
          : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  {['Date', 'Summary', 'Milestone', 'Blocker'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {project.updates.map(u => (
                  <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px', color: '#64748b', whiteSpace: 'nowrap' }}>{u.date}</td>
                    <td style={{ padding: '12px 16px', color: '#374151' }}>{u.summary}</td>
                    <td style={{ padding: '12px 16px', color: '#374151' }}>{u.milestone || '—'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      {u.blocker
                        ? <span style={{ background: '#fee2e2', color: '#991b1b', padding: '3px 8px', borderRadius: 4, fontSize: 12 }}>{u.blocker}</span>
                        : <span style={{ color: '#94a3b8' }}>None</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        }
      </div>
    </div>
  )
}
