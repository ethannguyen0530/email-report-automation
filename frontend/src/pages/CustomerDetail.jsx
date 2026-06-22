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

  if (!customer) return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>Loading...</div>

  return (
    <div>
      <button onClick={() => navigate('dashboard')}
        style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: 14, marginBottom: 20, padding: 0 }}>
        ← Back to Dashboard
      </button>

      <div style={{ background: 'white', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', padding: 28, marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>{customer.name}</h1>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>{customer.projects.length} project{customer.projects.length !== 1 ? 's' : ''}</p>
      </div>

      <div style={{ background: 'white', borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9' }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>Projects</h2>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Project', 'Status', 'Progress', 'Owner'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {customer.projects.map(p => (
              <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '12px 16px' }}>
                  <button onClick={() => navigate('project', p.id)}
                    style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontWeight: 600, fontSize: 14, padding: 0 }}>
                    {p.name}
                  </button>
                </td>
                <td style={{ padding: '12px 16px' }}><StatusBadge status={p.status} /></td>
                <td style={{ padding: '12px 16px', minWidth: 160 }}><ProgressBar value={p.progress} /></td>
                <td style={{ padding: '12px 16px', color: '#374151' }}>{p.owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
