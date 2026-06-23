import { useEffect, useState } from 'react'
import StatusBadge from '../components/StatusBadge'
import ProgressBar from '../components/ProgressBar'

export default function CustomerDetail({ id, navigate }) {
  const [customer, setCustomer] = useState(null)

  useEffect(() => {
    fetch(`/api/customers/${id}`)
      .then(r => r.json())
      .then(setCustomer)
  }, [id])

  if (!customer) return <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: 40 }}>Loading...</div>

  return (
    <div style={{ maxWidth: 900 }}>
      <button onClick={() => navigate('dashboard')}
        style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 13, padding: 0, marginBottom: 24 }}>
        ← Back to Overview
      </button>

      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Customer</p>
        <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px' }}>{customer.name}</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6 }}>
          {customer.projects.length} project{customer.projects.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Projects</h2>
        </div>
        {customer.projects.length === 0
          ? <p style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No projects found.</p>
          : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Project', 'Status', 'Progress', 'Owner'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid var(--border)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {customer.projects.map(p => (
                  <tr key={p.id} style={{ borderBottom: '1px solid var(--border)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '12px 16px' }}>
                      <button onClick={() => navigate('project', p.id)}
                        style={{ background: 'none', border: 'none', color: 'var(--accent-light)', cursor: 'pointer', fontWeight: 600, fontSize: 13, padding: 0 }}>
                        {p.name}
                      </button>
                    </td>
                    <td style={{ padding: '12px 16px' }}><StatusBadge status={p.status} /></td>
                    <td style={{ padding: '12px 16px', minWidth: 160 }}><ProgressBar value={p.progress} /></td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{p.owner}</td>
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
