import { useEffect, useState } from 'react'

export default function Settings() {
  const [recipients, setRecipients] = useState([])
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [position, setPosition] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [sendTime, setSendTime] = useState(null)

  const load = () =>
    fetch('/api/recipients').then(r => r.json()).then(setRecipients)

  useEffect(() => {
    load()
    fetch('/api/status').then(r => r.json()).then(d => setSendTime(d.report_send_time))
  }, [])

  const add = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setAdding(true)
    try {
      const res = await fetch('/api/recipients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), name: name.trim(), position: position.trim() }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Failed to add recipient')
      } else {
        setEmail('')
        setName('')
        setPosition('')
        setSuccess(`${email.trim()} added`)
        load()
        setTimeout(() => setSuccess(null), 3000)
      }
    } catch {
      setError('Network error')
    }
    setAdding(false)
  }

  const remove = async (id, recipientEmail) => {
    await fetch(`/api/recipients/${id}`, { method: 'DELETE' })
    setRecipients(prev => prev.filter(r => r.id !== id))
  }

  const inputStyle = {
    width: '100%', padding: '9px 12px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid var(--border)',
    borderRadius: 8, color: 'var(--text-primary)',
    fontSize: 13, outline: 'none',
    fontFamily: 'var(--font-body)',
    boxSizing: 'border-box',
  }

  return (
    <div style={{ maxWidth: 680 }}>
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, fontFamily: 'var(--font-heading)' }}>Configuration</p>
        <h1 style={{ fontSize: 30, fontWeight: 600, letterSpacing: '-0.5px', fontFamily: 'var(--font-heading)' }}>Report Recipients</h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.6 }}>
          Manage who receives the executive summary when it is sent via email. Changes take effect immediately.
        </p>
      </div>

      {/* Add form */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, fontFamily: 'var(--font-heading)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Add Recipient</h2>
        <form onSubmit={add}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Email Address *</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="leader@autonomize.ai"
                required
                style={inputStyle}
                onFocus={e => e.target.style.borderColor = '#731FE3'}
                onBlur={e => e.target.style.borderColor = 'var(--border)'}
              />
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Name (optional)</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Ujjwal Rajbhandari"
                style={inputStyle}
                onFocus={e => e.target.style.borderColor = '#731FE3'}
                onBlur={e => e.target.style.borderColor = 'var(--border)'}
              />
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Position (optional)</label>
              <input
                type="text"
                value={position}
                onChange={e => setPosition(e.target.value)}
                placeholder="CEO, VP of Engineering..."
                style={inputStyle}
                onFocus={e => e.target.style.borderColor = '#731FE3'}
                onBlur={e => e.target.style.borderColor = 'var(--border)'}
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button type="submit" disabled={adding || !email.trim()}
              style={{
                background: 'linear-gradient(135deg, #731FE3, #9B51E0)',
                border: 'none', color: '#fff',
                padding: '9px 20px', borderRadius: 8,
                fontSize: 13, fontWeight: 600,
                cursor: adding || !email.trim() ? 'not-allowed' : 'pointer',
                opacity: adding || !email.trim() ? 0.5 : 1,
                fontFamily: 'var(--font-heading)',
                boxShadow: '0 0 16px rgba(115,31,227,0.3)',
              }}>
              {adding ? 'Adding...' : '+ Add Recipient'}
            </button>
            {error && <span style={{ fontSize: 13, color: '#ef4444' }}>{error}</span>}
            {success && <span style={{ fontSize: 13, color: '#22c55e' }}>+ {success}</span>}
          </div>
        </form>
      </div>

      {/* Recipients list */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-heading)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Current Recipients
          </h2>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{recipients.length} {recipients.length === 1 ? 'person' : 'people'}</span>
        </div>

        {recipients.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 6 }}>No recipients added yet.</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Add at least one email address to enable report delivery.</p>
          </div>
        ) : (
          recipients.map((r, i) => (
            <div key={r.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '14px 20px',
              borderBottom: i < recipients.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: '50%',
                  background: 'rgba(115,31,227,0.15)',
                  border: '1px solid rgba(115,31,227,0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 600, color: '#c084fc',
                  flexShrink: 0,
                }}>
                  {(r.name || r.email).charAt(0).toUpperCase()}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 1 }}>
                    {r.name && <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', margin: 0 }}>{r.name}</p>}
                    {r.position && (
                      <span style={{
                        fontSize: 11, color: '#a78bfa',
                        background: 'rgba(115,31,227,0.1)',
                        border: '1px solid rgba(115,31,227,0.2)',
                        borderRadius: 4, padding: '1px 7px',
                        fontWeight: 500, letterSpacing: '0.02em',
                      }}>{r.position}</span>
                    )}
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>{r.email}</p>
                </div>
              </div>
              <button onClick={() => remove(r.id, r.email)}
                style={{
                  background: 'none', border: '1px solid rgba(239,68,68,0.2)',
                  color: '#ef4444', padding: '5px 12px', borderRadius: 6,
                  fontSize: 12, cursor: 'pointer', transition: 'var(--transition)',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.1)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>

      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 16, lineHeight: 1.6 }}>
        These recipients receive the executive report when sent manually or automatically
        {sendTime ? ` at ${sendTime} daily` : ''}.
        The REPORT_RECIPIENTS value in .env is used as a fallback if this list is empty.
      </p>
    </div>
  )
}
