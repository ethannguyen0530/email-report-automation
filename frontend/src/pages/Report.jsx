import { useEffect, useState } from 'react'

export default function Report() {
  const [html, setHtml] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(null)

  useEffect(() => {
    fetch('/api/report')
      .then(r => r.text())
      .then(text => { setHtml(text); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const sendReport = async () => {
    setSending(true)
    setSent(null)
    try {
      const res = await fetch('/api/send-report', { method: 'POST' })
      const data = await res.json()
      setSent(data.ok ? 'success' : 'error')
    } catch {
      setSent('error')
    }
    setSending(false)
  }

  return (
    <div style={{ maxWidth: 1000 }}>
      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Output</p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>Executive Report</h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {sent === 'success' && <span style={{ fontSize: 13, color: '#22c55e' }}>✓ Sent</span>}
            {sent === 'error' && <span style={{ fontSize: 13, color: '#ef4444' }}>Failed — check .env credentials</span>}
            <button onClick={sendReport} disabled={sending}
              style={{
                background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
                border: 'none', color: 'white', padding: '9px 20px',
                borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: sending ? 'not-allowed' : 'pointer',
                opacity: sending ? 0.6 : 1,
                boxShadow: '0 0 16px rgba(124,58,237,0.3)',
              }}>
              {sending ? 'Sending...' : 'Send via Email + Slack'}
            </button>
          </div>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        {loading
          ? <p style={{ padding: 24, color: 'var(--text-muted)', fontSize: 13 }}>Generating report...</p>
          : <iframe srcDoc={html} style={{ width: '100%', height: '75vh', border: 'none', display: 'block' }} title="Executive Report" />
        }
      </div>
    </div>
  )
}
