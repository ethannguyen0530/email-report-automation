import { useEffect, useState } from 'react'

function fmtDateTime(str) {
  if (!str) return '—'
  try {
    return new Date(str).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit', hour12: true,
    })
  } catch { return str?.slice(0, 16) || '—' }
}

function fmtDateShort(str) {
  if (!str) return '—'
  try {
    return new Date(str).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true })
  } catch { return str?.slice(0, 16) || '—' }
}

export default function Emails() {
  const [emails, setEmails] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [activeCustomer, setActiveCustomer] = useState(null) // null = "All"

  const loadEmails = (customer) => {
    setLoading(true)
    const url = customer ? `/api/emails?customer=${encodeURIComponent(customer)}` : '/api/emails'
    fetch(url)
      .then(r => r.json())
      .then(data => { setEmails(data); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    loadEmails(null)
    fetch('/api/email-stats').then(r => r.json()).then(setStats).catch(() => {})
  }, [])

  const handleCustomerClick = (name) => {
    const next = activeCustomer === name ? null : name
    setActiveCustomer(next)
    setSelected(null)
    loadEmails(next)
  }

  const flaggedEmails = emails.filter(e => e.flagged)
  const normalEmails = emails.filter(e => !e.flagged)

  return (
    <div style={{ maxWidth: 1200 }}>
      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6, fontFamily: 'var(--font-heading)' }}>Inbox</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.5px', fontFamily: 'var(--font-heading)' }}>Scanned Emails</h1>
          {emails.length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '4px 12px', borderRadius: 99, fontWeight: 500 }}>
              {emails.length} {activeCustomer ? `for ${activeCustomer}` : 'total'} · no duplicates
            </span>
          )}
          {stats?.flagged > 0 && !activeCustomer && (
            <span style={{ fontSize: 12, fontWeight: 600, background: 'rgba(220,38,38,0.08)', color: '#dc2626', border: '1px solid rgba(220,38,38,0.2)', padding: '4px 12px', borderRadius: 99 }}>
              ⚠ {stats.flagged} need review
            </span>
          )}
        </div>
      </div>

      {/* Stats row */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
          <StatCard label="All Time" value={stats.total} color="#731FE3" />
          <StatCard label="Last 7 Days" value={stats.weekly} color="#16a34a" />
          <StatCard label="Last 30 Days" value={stats.monthly} color="#F86442" />
        </div>
      )}

      {/* Per-customer filter chips */}
      {stats?.per_customer?.length > 0 && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px 20px', marginBottom: 20 }}>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 14, fontFamily: 'var(--font-heading)' }}>
            Filter by Customer <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>— click to filter emails</span>
          </p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {/* "All" chip */}
            <button
              onClick={() => handleCustomerClick(null)}
              style={{
                background: !activeCustomer ? 'rgba(115,31,227,0.1)' : 'var(--bg)',
                border: `1px solid ${!activeCustomer ? '#731FE3' : 'var(--border)'}`,
                borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.15s',
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, color: !activeCustomer ? '#731FE3' : 'var(--text-primary)' }}>All</span>
            </button>

            {stats.per_customer.map(c => (
              <button
                key={c.name}
                onClick={() => handleCustomerClick(c.name)}
                style={{
                  background: activeCustomer === c.name ? 'rgba(115,31,227,0.1)' : 'var(--bg)',
                  border: `1px solid ${activeCustomer === c.name ? '#731FE3' : 'var(--border)'}`,
                  borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.15s',
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 600, color: activeCustomer === c.name ? '#731FE3' : 'var(--text-primary)' }}>{c.count}</span>
                <span style={{ fontSize: 12, color: activeCustomer === c.name ? '#731FE3' : 'var(--text-secondary)' }}>{c.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Email list + detail pane */}
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '380px 1fr' : '1fr', gap: 16, alignItems: 'start' }}>
        {/* List */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          {loading && <p style={{ padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>Loading...</p>}
          {!loading && emails.length === 0 && (
            <div style={{ padding: '32px 20px', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 6 }}>
                {activeCustomer ? `No emails linked to ${activeCustomer}.` : 'No emails scanned yet.'}
              </p>
              {activeCustomer && <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Customer filtering links emails via AI extraction. Emails scanned before this update or mock data won't appear here.</p>}
              {!activeCustomer && <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Click "Scan Now" on the Overview page or wait for the next scheduled scan.</p>}
            </div>
          )}

          {/* Flagged emails section */}
          {!activeCustomer && flaggedEmails.length > 0 && (
            <>
              <div style={{ padding: '10px 18px', background: 'rgba(220,38,38,0.04)', borderBottom: '1px solid rgba(220,38,38,0.12)' }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: '#dc2626', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  ⚠ Needs Review ({flaggedEmails.length})
                </p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>These emails couldn't be confidently extracted — please review manually.</p>
              </div>
              {flaggedEmails.map((email, i) => (
                <EmailRow key={email.id} email={email} selected={selected} onSelect={setSelected}
                  isLast={i === flaggedEmails.length - 1 && normalEmails.length === 0} flagged />
              ))}
              {normalEmails.length > 0 && (
                <div style={{ padding: '10px 18px', background: 'rgba(115,31,227,0.03)', borderBottom: '1px solid var(--border)' }}>
                  <p style={{ fontSize: 11, fontWeight: 700, color: '#731FE3', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Processed ({normalEmails.length})
                  </p>
                </div>
              )}
            </>
          )}

          {!activeCustomer && normalEmails.map((email, i) => (
            <EmailRow key={email.id} email={email} selected={selected} onSelect={setSelected}
              isLast={i === normalEmails.length - 1} />
          ))}

          {/* Customer-filtered view: show all results (flagged + normal) without section headers */}
          {activeCustomer && emails.map((email, i) => (
            <EmailRow key={email.id} email={email} selected={selected} onSelect={setSelected}
              isLast={i === emails.length - 1} flagged={email.flagged} />
          ))}
        </div>

        {/* Full email detail pane */}
        {selected && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border)', background: 'var(--bg)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12, lineHeight: 1.4, fontFamily: 'var(--font-heading)' }}>
                    {selected.subject || '(no subject)'}
                  </h2>
                  <div style={{ display: 'grid', gap: 5 }}>
                    <MetaRow label="From" value={selected.sender} />
                    <MetaRow label="Received" value={fmtDateTime(selected.date)} />
                    {selected.processed && <MetaRow label="Processed" value={fmtDateTime(selected.processed_at)} color="#16a34a" />}
                  </div>
                </div>
                <button onClick={() => setSelected(null)}
                  style={{ background: 'var(--bg-hover)', border: '1px solid var(--border)', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: '6px 10px', borderRadius: 6 }}>
                  ✕
                </button>
              </div>

              {/* Status tags */}
              <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
                <Tag color="#731FE3">Gmail ID: {selected.gmail_id?.slice(0, 12)}...</Tag>
                {selected.flagged
                  ? <Tag color="#dc2626">⚠ Needs Review</Tag>
                  : selected.processed
                    ? <Tag color="#16a34a">✓ Extracted &amp; stored</Tag>
                    : <Tag color="#d97706">Pending extraction</Tag>
                }
              </div>

              {selected.flagged && selected.flag_reason && (
                <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.18)', borderRadius: 8 }}>
                  <p style={{ fontSize: 12, color: '#dc2626', fontWeight: 600, marginBottom: 2 }}>Why flagged:</p>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{selected.flag_reason}</p>
                </div>
              )}
            </div>

            {/* Body */}
            <div style={{ padding: '20px 22px', overflowY: 'auto', maxHeight: '60vh' }}>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 12, fontFamily: 'var(--font-heading)' }}>Email Body</p>
              {selected.body
                ? <pre style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'var(--font-body)', wordBreak: 'break-word' }}>{selected.body}</pre>
                : <p style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>No body content available.</p>
              }
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function EmailRow({ email, selected, onSelect, isLast, flagged }) {
  return (
    <div
      onClick={() => onSelect(selected?.id === email.id ? null : email)}
      style={{
        padding: '14px 18px',
        borderBottom: !isLast ? '1px solid var(--border)' : 'none',
        cursor: 'pointer',
        background: selected?.id === email.id ? 'rgba(115,31,227,0.06)' : flagged ? 'rgba(220,38,38,0.02)' : 'transparent',
        borderLeft: selected?.id === email.id ? '3px solid #731FE3' : flagged ? '3px solid rgba(220,38,38,0.4)' : '3px solid transparent',
        transition: 'all 0.15s',
      }}
      onMouseEnter={e => { if (selected?.id !== email.id) e.currentTarget.style.background = 'var(--bg-hover)' }}
      onMouseLeave={e => { if (selected?.id !== email.id) e.currentTarget.style.background = flagged ? 'rgba(220,38,38,0.02)' : 'transparent' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
            {flagged && <span title="Needs manual review" style={{ fontSize: 11 }}>⚠</span>}
            <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {email.subject || '(no subject)'}
            </p>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{email.sender}</p>
          <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{fmtDateShort(email.date)}</p>
        </div>
        <span style={{
          fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 99, flexShrink: 0, marginTop: 2,
          background: flagged ? 'rgba(220,38,38,0.08)' : email.processed ? 'rgba(22,163,74,0.1)' : 'rgba(217,119,6,0.1)',
          color: flagged ? '#dc2626' : email.processed ? '#16a34a' : '#d97706',
          border: `1px solid ${flagged ? 'rgba(220,38,38,0.2)' : email.processed ? 'rgba(22,163,74,0.2)' : 'rgba(217,119,6,0.2)'}`,
        }}>
          {flagged ? 'review' : email.processed ? 'processed' : 'pending'}
        </span>
      </div>
      {!selected && (
        <p style={{ fontSize: 12, color: email.ai_summary ? '#731FE3' : 'var(--text-muted)', marginTop: 5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontStyle: email.ai_summary ? 'normal' : 'italic' }}>
          {email.ai_summary || email.body?.trim().slice(0, 100) || '—'}
        </p>
      )}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '18px 22px' }}>
      <p style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginBottom: 8, fontFamily: 'var(--font-heading)' }}>{label}</p>
      <p style={{ fontSize: 30, fontWeight: 600, color, lineHeight: 1, letterSpacing: '-0.5px', fontFamily: 'var(--font-heading)' }}>{value ?? '—'}</p>
    </div>
  )
}

function MetaRow({ label, value, color }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', minWidth: 70, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 13, color: color || 'var(--text-secondary)', wordBreak: 'break-all' }}>{value}</span>
    </div>
  )
}

function Tag({ children, color }) {
  return (
    <span style={{ fontSize: 11, fontWeight: 500, padding: '3px 10px', borderRadius: 99, background: `${color}12`, color, border: `1px solid ${color}25` }}>
      {children}
    </span>
  )
}
