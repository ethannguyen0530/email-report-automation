import { useEffect, useState } from 'react'

export default function Customers({ navigate }) {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [newName, setNewName] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [healthDetail, setHealthDetail] = useState(null) // { customerName, projects }
  const [allHealthProjects, setAllHealthProjects] = useState([])

  const load = () => {
    setLoading(true)
    Promise.all([
      fetch('/api/customers').then(r => r.json()),
      fetch('/api/health').then(r => r.json()),
      fetch('/api/email-stats').then(r => r.json()),
    ]).then(([custs, health, stats]) => {
      const healthMap = {}
      health.projects?.forEach(p => {
        if (p.customer) {
          if (!healthMap[p.customer]) healthMap[p.customer] = []
          healthMap[p.customer].push(p.score)
        }
      })
      const emailCountMap = {}
      stats.per_customer?.forEach(c => { emailCountMap[c.name] = c.count })
      setAllHealthProjects(health.projects || [])

      setCustomers(custs.map(c => ({
        ...c,
        avgHealth: healthMap[c.name]?.length
          ? Math.round(healthMap[c.name].reduce((a, b) => a + b, 0) / healthMap[c.name].length)
          : null,
        emailCount: emailCountMap[c.name] || 0,
      })))
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    if (!newName.trim()) return
    setAdding(true)
    setAddError(null)
    try {
      const res = await fetch('/api/customers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim() }),
      })
      const data = await res.json()
      if (data.error) { setAddError(data.error); setAdding(false); return }
      setNewName('')
      load()
    } catch { setAddError('Request failed') }
    setAdding(false)
  }

  const handleDelete = async (id) => {
    await fetch(`/api/customers/${id}`, { method: 'DELETE' })
    setConfirmDelete(null)
    load()
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6, fontFamily: 'var(--font-heading)' }}>Accounts</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.5px', fontFamily: 'var(--font-heading)' }}>Customer Management</h1>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '4px 12px', borderRadius: 99, fontWeight: 500 }}>
            {customers.length} customer{customers.length !== 1 ? 's' : ''}
          </span>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.6 }}>
          Customers are added automatically when emails are scanned. You can also add them manually or remove inactive ones here.
        </p>
      </div>

      {/* Add customer */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '20px 24px', marginBottom: 24 }}>
        <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14, fontFamily: 'var(--font-heading)' }}>Add Customer Manually</p>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="e.g. United Healthcare"
            style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'var(--bg)', color: 'var(--text-primary)', outline: 'none', fontFamily: 'var(--font-body)' }}
          />
          <button onClick={handleAdd} disabled={adding || !newName.trim()}
            style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: adding || !newName.trim() ? 'rgba(115,31,227,0.4)' : '#731FE3', color: 'white', fontSize: 13, fontWeight: 600, cursor: adding || !newName.trim() ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-body)', transition: 'all 0.15s' }}>
            {adding ? 'Adding...' : 'Add Customer'}
          </button>
        </div>
        {addError && <p style={{ fontSize: 12, color: '#dc2626', marginTop: 8 }}>{addError}</p>}
      </div>

      {/* Customer list */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>All Customers</h2>
        </div>

        {loading && <p style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>Loading...</p>}
        {!loading && customers.length === 0 && (
          <div style={{ padding: '32px 20px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No customers yet. Scan emails or add one manually above.</p>
          </div>
        )}

        {customers.map((c, i) => {
          const hColor = c.avgHealth === null ? 'var(--text-muted)' : c.avgHealth >= 70 ? '#16a34a' : c.avgHealth >= 40 ? '#d97706' : '#dc2626'
          return (
            <div key={c.id} style={{ padding: '16px 20px', borderBottom: i < customers.length - 1 ? '1px solid var(--border)' : 'none', display: 'flex', alignItems: 'center', gap: 16, transition: 'background 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {/* Avatar */}
              <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, rgba(115,31,227,0.15), rgba(115,31,227,0.08))', border: '1px solid rgba(115,31,227,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#731FE3', fontFamily: 'var(--font-heading)' }}>
                  {c.name.charAt(0).toUpperCase()}
                </span>
              </div>

              {/* Name + stats */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <button onClick={() => navigate('customer', c.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', padding: 0, textAlign: 'left', fontFamily: 'var(--font-body)' }}>
                  {c.name}
                </button>
                <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
                  <Stat label="Emails" value={c.emailCount} />
                </div>
              </div>

              {/* Health score — clickable breakdown */}
              {c.avgHealth !== null && (
                <div onClick={() => setHealthDetail({ customerName: c.name, projects: allHealthProjects.filter(p => p.customer === c.name) })}
                  title="Click for health breakdown"
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: `${hColor}10`, borderRadius: 8, border: `1px solid ${hColor}25`, cursor: 'pointer', transition: 'all 0.15s' }}
                  onMouseEnter={e => { e.currentTarget.style.background = `${hColor}18`; e.currentTarget.style.boxShadow = `0 2px 8px ${hColor}20` }}
                  onMouseLeave={e => { e.currentTarget.style.background = `${hColor}10`; e.currentTarget.style.boxShadow = 'none' }}
                >
                  <span style={{ fontSize: 13, fontWeight: 700, color: hColor }}>{c.avgHealth}</span>
                  <span style={{ fontSize: 11, color: hColor, opacity: 0.8 }}>health ↗</span>
                </div>
              )}

              {/* Delete */}
              {confirmDelete === c.id ? (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => handleDelete(c.id)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: '#dc2626', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                    Confirm Delete
                  </button>
                  <button onClick={() => setConfirmDelete(null)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'none', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>
                    Cancel
                  </button>
                </div>
              ) : (
                <button onClick={() => setConfirmDelete(c.id)}
                  style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'none', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer', opacity: 0.7, transition: 'all 0.15s' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#dc2626'; e.currentTarget.style.color = '#dc2626'; e.currentTarget.style.opacity = '1' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.opacity = '0.7' }}>
                  Remove
                </button>
              )}
            </div>
          )
        })}
      </div>

      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 16, lineHeight: 1.6 }}>
        ⚠ Removing a customer also deletes all their projects and update history. This cannot be undone.
      </p>

      {/* Health breakdown modal */}
      {healthDetail && (
        <div onClick={() => setHealthDetail(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(10,5,69,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-card)', borderRadius: 16, padding: '28px 32px', width: '100%', maxWidth: 460, boxShadow: '0 20px 60px rgba(10,5,69,0.3)', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-heading)', marginBottom: 4 }}>Health Breakdown</h2>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{healthDetail.customerName}</p>
              </div>
              <button onClick={() => setHealthDetail(null)} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', color: 'var(--text-muted)', fontSize: 16 }}>✕</button>
            </div>

            {healthDetail.projects.length === 0 ? (
              <p style={{ fontSize: 13, color: 'var(--text-muted)', padding: '12px 0' }}>No projects with health data yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {healthDetail.projects.map(p => {
                  const pc = p.score >= 70 ? '#16a34a' : p.score >= 40 ? '#d97706' : '#dc2626'
                  const tag = p.score >= 70 ? 'Healthy' : p.score >= 40 ? 'Needs Attention' : 'Critical'
                  return (
                    <div key={p.id} style={{ padding: '14px 16px', background: 'var(--bg)', borderRadius: 12, border: '1px solid var(--border)' }}>
                      {/* Project header */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{ width: 44, height: 44, borderRadius: '50%', background: `${pc}14`, border: `2px solid ${pc}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          <span style={{ fontSize: 13, fontWeight: 700, color: pc }}>{p.score}</span>
                        </div>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{p.name}</p>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 11, fontWeight: 600, color: pc, background: `${pc}12`, padding: '2px 8px', borderRadius: 99, border: `1px solid ${pc}25` }}>{tag}</span>
                            {p.last_updated && (
                              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                Score reflects data as of {new Date(p.last_updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      {/* Reasons */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                        {(p.reasons || []).map((r, ri) => {
                          const rc = r.type === 'ok' ? '#16a34a' : r.type === 'warn' ? '#d97706' : '#dc2626'
                          const icon = r.type === 'ok' ? '✓' : r.type === 'warn' ? '⚠' : '✗'
                          const impactStr = r.impact < 0 ? `−${Math.abs(r.impact)} pts` : r.impact === 0 ? '' : `+${r.impact} pts`
                          return (
                            <div key={ri} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', background: `${rc}06`, borderRadius: 8, border: `1px solid ${rc}15` }}>
                              <span style={{ color: rc, fontSize: 11, fontWeight: 700, width: 14, flexShrink: 0 }}>{icon}</span>
                              <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>{r.factor}</span>
                              {impactStr && <span style={{ fontSize: 11, fontWeight: 700, color: rc, flexShrink: 0 }}>{impactStr}</span>}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            <div style={{ marginTop: 16, padding: '10px 14px', background: 'rgba(115,31,227,0.05)', borderRadius: 10, border: '1px solid rgba(115,31,227,0.1)' }}>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--text-secondary)' }}>Score key:</strong> 70–100 = Healthy · 40–69 = Needs Attention · 0–39 = Critical
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
      <strong style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{value}</strong> {label}
    </span>
  )
}
