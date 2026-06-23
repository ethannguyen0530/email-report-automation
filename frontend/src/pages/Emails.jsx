import { useEffect, useState } from 'react'

function fmtDateTime(str) {
  if (!str) return '—'
  try {
    return new Date(str).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true })
  } catch { return str?.slice(0, 16) || '—' }
}

export default function Emails() {
  const [emails, setEmails] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/emails')
      .then(r => r.json())
      .then(data => { setEmails(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Inbox</p>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>Scanned Emails</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: 20 }}>
        {/* List */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          {loading && <p style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>Loading...</p>}
          {!loading && emails.length === 0 && (
            <p style={{ padding: 24, color: 'var(--text-muted)', fontSize: 13 }}>
              No emails scanned yet. Run option 2 in main.py first.
            </p>
          )}
          {emails.map((email, i) => (
            <div key={email.id}
              onClick={() => setSelected(selected?.id === email.id ? null : email)}
              style={{
                padding: '14px 20px',
                borderBottom: i < emails.length - 1 ? '1px solid var(--border)' : 'none',
                cursor: 'pointer',
                background: selected?.id === email.id ? 'rgba(124,58,237,0.08)' : 'transparent',
                borderLeft: selected?.id === email.id ? '3px solid var(--accent)' : '3px solid transparent',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { if (selected?.id !== email.id) e.currentTarget.style.background = 'var(--bg-hover)' }}
              onMouseLeave={e => { if (selected?.id !== email.id) e.currentTarget.style.background = 'transparent' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {email.subject || '(no subject)'}
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{email.sender}</p>
                  {/* Received + processed timestamps */}
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      Received: <span style={{ color: 'var(--text-secondary)' }}>{fmtDateTime(email.date)}</span>
                    </span>
                    {email.processed && (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        Processed: <span style={{ color: '#22c55e' }}>{fmtDateTime(email.processed_at)}</span>
                      </span>
                    )}
                  </div>
                </div>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 99, flexShrink: 0, marginTop: 2,
                  background: email.processed ? 'rgba(34,197,94,0.1)' : 'rgba(245,158,11,0.1)',
                  color: email.processed ? '#22c55e' : '#f59e0b',
                  border: `1px solid ${email.processed ? 'rgba(34,197,94,0.2)' : 'rgba(245,158,11,0.2)'}`,
                }}>
                  {email.processed ? 'processed' : 'pending'}
                </span>
              </div>
              {email.body && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {email.body.trim().slice(0, 90)}...
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Detail pane */}
        {selected && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden', display: 'flex', flexDirection: 'column', maxHeight: '80vh' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>{selected.subject}</h2>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 2 }}>From: <span style={{ color: 'var(--text-secondary)' }}>{selected.sender}</span></p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 2 }}>Received: <span style={{ color: 'var(--text-secondary)' }}>{fmtDateTime(selected.date)}</span></p>
                {selected.processed && (
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Processed: <span style={{ color: '#22c55e' }}>{fmtDateTime(selected.processed_at)}</span></p>
                )}
              </div>
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 20, lineHeight: 1, padding: 4 }}>×</button>
            </div>
            <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>
              <pre style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'inherit' }}>
                {selected.body || 'No body content.'}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
