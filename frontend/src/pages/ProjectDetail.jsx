import { useEffect, useState } from 'react'
import StatusBadge from '../components/StatusBadge'
import ProgressBar from '../components/ProgressBar'

export default function ProjectDetail({ id, navigate }) {
  const [project, setProject] = useState(null)

  useEffect(() => {
    fetch(`/api/projects/${id}`).then(r => r.json()).then(setProject)
  }, [id])

  if (!project) return <Loading />

  return (
    <div style={{ maxWidth: 900 }}>
      <button onClick={() => navigate('dashboard')} style={backBtn}>← Back</button>

      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px' }}>{project.name}</h1>
          <StatusBadge status={project.status} />
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6 }}>
          {project.customer && <><span style={{ color: 'var(--text-secondary)' }}>{project.customer}</span> · </>}
          Owner: <span style={{ color: 'var(--text-secondary)' }}>{project.owner}</span>
        </p>
      </div>

      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Progress</span>
          <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{project.progress}%</span>
        </div>
        <ProgressBar value={project.progress} />
      </div>

      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Update History</h2>
        </div>
        {project.updates.length === 0
          ? <p style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No updates recorded.</p>
          : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Date', 'Summary', 'Milestone', 'Blocker'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid var(--border)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {project.updates.map(u => (
                  <tr key={u.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{u.date}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{u.summary}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{u.milestone || '—'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      {u.blocker
                        ? <span style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', padding: '3px 8px', borderRadius: 6, fontSize: 11, border: '1px solid rgba(239,68,68,0.2)' }}>{u.blocker}</span>
                        : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>None</span>
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

const backBtn = {
  background: 'none', border: 'none', color: 'var(--text-muted)',
  cursor: 'pointer', fontSize: 13, padding: 0, marginBottom: 24,
  display: 'flex', alignItems: 'center', gap: 4,
  transition: 'color 0.15s',
}

function Loading() {
  return <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: 40 }}>Loading...</div>
}
