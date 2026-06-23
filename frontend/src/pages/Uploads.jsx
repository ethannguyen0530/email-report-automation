import { useState, useRef, useCallback } from 'react'

const ACCEPTED = '.pdf,.txt,.doc,.docx,.csv,.png,.jpg,.jpeg,.gif,.webp'

export default function Uploads() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef()

  const handleFiles = useCallback(async (incoming) => {
    const list = Array.from(incoming)
    if (!list.length) return

    setUploading(true)
    const results = []

    for (const file of list) {
      const form = new FormData()
      form.append('file', file)

      try {
        const res = await fetch('/api/upload', { method: 'POST', body: form })
        const data = await res.json()
        results.push({ name: file.name, size: file.size, type: file.type, status: 'done', url: data.url })
      } catch {
        results.push({ name: file.name, size: file.size, type: file.type, status: 'error' })
      }
    }

    setFiles(prev => [...results, ...prev])
    setUploading(false)
  }, [])

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Files & Assets</p>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>Uploads</h1>
      </div>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent-light)' : 'var(--border)'}`,
          borderRadius: 16,
          padding: '52px 32px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? 'rgba(124,58,237,0.06)' : 'var(--bg-card)',
          transition: 'all 0.2s ease',
          marginBottom: 28,
          boxShadow: dragging ? '0 0 0 4px rgba(124,58,237,0.1)' : 'none',
        }}
      >
        <input ref={inputRef} type="file" multiple accept={ACCEPTED} style={{ display: 'none' }}
          onChange={e => handleFiles(e.target.files)} />

        <div style={{
          width: 52, height: 52, borderRadius: 14,
          background: 'rgba(124,58,237,0.12)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 16px',
          border: '1px solid rgba(124,58,237,0.2)',
        }}>
          <UploadIcon />
        </div>

        <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
          {dragging ? 'Drop to upload' : 'Drag files here, or click to browse'}
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          PDF, Word, CSV, TXT, PNG, JPG, GIF, WEBP
        </p>

        {uploading && (
          <div style={{ marginTop: 16, color: 'var(--accent-light)', fontSize: 13 }}>Uploading...</div>
        )}
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Uploaded Files</h2>
          </div>
          {files.map((f, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 20px',
              borderBottom: i < files.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <FileTypeIcon type={f.type} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{formatSize(f.size)}</p>
              </div>
              {f.type.startsWith('image/') && f.url && (
                <img src={f.url} alt={f.name} style={{ width: 40, height: 40, borderRadius: 6, objectFit: 'cover', border: '1px solid var(--border)' }} />
              )}
              <StatusDot status={f.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function FileTypeIcon({ type }) {
  const isImage = type.startsWith('image/')
  const color = isImage ? '#a855f7' : '#7c3aed'
  return (
    <div style={{ width: 36, height: 36, borderRadius: 8, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: `1px solid ${color}28` }}>
      {isImage
        ? <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="1" y="2" width="14" height="12" rx="2" stroke={color} strokeWidth="1.2"/><circle cx="5.5" cy="6" r="1.5" fill={color}/><path d="M1 11l3.5-3.5L7 10l3-3 5 4" stroke={color} strokeWidth="1.2" strokeLinejoin="round"/></svg>
        : <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M9 1H3.5A1.5 1.5 0 002 2.5v11A1.5 1.5 0 003.5 15h9a1.5 1.5 0 001.5-1.5V6L9 1z" stroke={color} strokeWidth="1.2"/><path d="M9 1v5h5" stroke={color} strokeWidth="1.2"/></svg>
      }
    </div>
  )
}

function StatusDot({ status }) {
  return (
    <span style={{
      width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
      background: status === 'done' ? '#22c55e' : '#ef4444',
      boxShadow: status === 'done' ? '0 0 6px #22c55e88' : '0 0 6px #ef444488',
    }} />
  )
}

function UploadIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <path d="M11 14V4M11 4L7.5 7.5M11 4L14.5 7.5" stroke="#a855f7" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 15v2.5A1.5 1.5 0 004.5 19h13a1.5 1.5 0 001.5-1.5V15" stroke="#a855f7" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  )
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
