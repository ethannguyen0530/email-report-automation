import { useState, useRef, useEffect } from 'react'
import StatusBadge from './StatusBadge'

const OPTIONS = ['On Track', 'At Risk', 'Delayed', 'Completed', 'In Progress']

export default function StatusSelect({ projectId, value, onChange }) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const ref = useRef()

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const select = async (status) => {
    if (status === value) { setOpen(false); return }
    setSaving(true)
    setOpen(false)
    await fetch(`/api/projects/${projectId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    onChange(status)
    setSaving(false)
  }

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(o => !o) }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, opacity: saving ? 0.5 : 1 }}
        title="Click to change status"
      >
        <StatusBadge status={value} />
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 4 }}>▾</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, zIndex: 999, marginTop: 4,
          background: '#1e1e1e', border: '1px solid var(--border)',
          borderRadius: 10, padding: 4, minWidth: 140,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
        }}>
          {OPTIONS.map(opt => (
            <button key={opt} onClick={() => select(opt)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                width: '100%', padding: '8px 10px', border: 'none',
                background: opt === value ? 'rgba(255,255,255,0.05)' : 'none',
                cursor: 'pointer', borderRadius: 6, textAlign: 'left',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
              onMouseLeave={e => e.currentTarget.style.background = opt === value ? 'rgba(255,255,255,0.05)' : 'none'}
            >
              <StatusBadge status={opt} />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
