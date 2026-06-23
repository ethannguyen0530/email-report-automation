import { useState, useRef, useCallback, useEffect } from 'react'

const ACCEPTED = '.pdf,.txt,.doc,.docx,.csv,.xlsx,.pptx'

export default function Uploads() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef()

  // Listen for SSE file_processed events
  useEffect(() => {
    const es = new EventSource('/api/stream')
    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'file_processed') {
          setFiles(prev => prev.map(f =>
            f.name === msg.filename
              ? { ...f, extracting: false, extracted: msg }
              : f
          ))
        }
      } catch {}
    }
    return () => es.close()
  }, [])

  const handleFiles = useCallback(async (incoming) => {
    const list = Array.from(incoming).filter(f => {
      const ext = f.name.split('.').pop().toLowerCase()
      return ['pdf','txt','doc','docx','csv','xlsx','pptx'].includes(ext)
    })
    if (!list.length) return
    setUploading(true)

    for (const file of list) {
      const form = new FormData()
      form.append('file', file)
      const entry = { name: file.name, size: file.size, status: 'uploading', extracting: false, extracted: null }
      setFiles(prev => [entry, ...prev])

      try {
        const res = await fetch('/api/upload', { method: 'POST', body: form })
        const data = await res.json()
        if (data.filename) {
          // trigger AI extraction
          setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'uploaded', extracting: true } : f))
          fetch('/api/process-file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: data.filename }),
          }).catch(() => {})
        } else {
          setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'error' } : f))
        }
      } catch {
        setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'error' } : f))
      }
    }
    setUploading(false)
  }, [])

  const onDrop = (e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }
  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6, fontFamily: 'var(--font-heading)' }}>Data Ingestion</p>
        <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.5px', fontFamily: 'var(--font-heading)', marginBottom: 6 }}>Upload Files</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Upload project status documents, reports, or notes. The AI will extract customer, project, status, and blockers — exactly like email scanning — and add the data to your dashboard and executive report.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDrop={onDrop} onDragOver={onDragOver} onDragLeave={onDragLeave}
        onClick={() => inputRef.current.click()}
        style={{
          border: `2px dashed ${dragging ? '#731FE3' : 'var(--border)'}`,
          borderRadius: 16, padding: '52px 32px', textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? 'rgba(115,31,227,0.06)' : 'var(--bg-card)',
          transition: 'all 0.2s ease', marginBottom: 28,
          boxShadow: dragging ? '0 0 0 4px rgba(115,31,227,0.1)' : 'none',
        }}
      >
        <input ref={inputRef} type="file" multiple accept={ACCEPTED} style={{ display: 'none' }}
          onChange={e => handleFiles(e.target.files)} />

        <div style={{ width: 52, height: 52, borderRadius: 14, background: 'rgba(115,31,227,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', border: '1px solid rgba(115,31,227,0.2)' }}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M11 14V4M11 4L7.5 7.5M11 4L14.5 7.5" stroke="#731FE3" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 15v2.5A1.5 1.5 0 004.5 19h13a1.5 1.5 0 001.5-1.5V15" stroke="#731FE3" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
        </div>
        <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
          {dragging ? 'Drop to extract & load' : 'Drag files here, or click to browse'}
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), CSV, TXT</p>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', opacity: 0.7 }}>AI extracts project data and loads it into your dashboard automatically</p>
        {uploading && <div style={{ marginTop: 16, color: '#731FE3', fontSize: 13, fontWeight: 500 }}>Uploading...</div>}
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Processed Files</h2>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>— {files.length} file{files.length !== 1 ? 's' : ''}</span>
          </div>
          {files.map((f, i) => (
            <div key={i} style={{ padding: '16px 20px', borderBottom: i < files.length - 1 ? '1px solid var(--border)' : 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(115,31,227,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid rgba(115,31,227,0.2)' }}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M9 1H3.5A1.5 1.5 0 002 2.5v11A1.5 1.5 0 003.5 15h9a1.5 1.5 0 001.5-1.5V6L9 1z" stroke="#731FE3" strokeWidth="1.2"/><path d="M9 1v5h5" stroke="#731FE3" strokeWidth="1.2"/></svg>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{formatSize(f.size)}</p>
                </div>
                <StatusChip file={f} />
              </div>

              {/* Extraction result */}
              {f.extracted && f.extracted.status === 'ok' && (
                <div style={{ marginTop: 12, padding: '12px 14px', background: 'rgba(22,163,74,0.06)', border: '1px solid rgba(22,163,74,0.2)', borderRadius: 10, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                  {f.extracted.customer && <ExResult label="Customer" value={f.extracted.customer} color="#16a34a" />}
                  {f.extracted.project && <ExResult label="Project" value={f.extracted.project} color="#731FE3" />}
                  {f.extracted.confidence !== undefined && <ExResult label="Confidence" value={`${f.extracted.confidence}/100`} color={f.extracted.confidence >= 70 ? '#16a34a' : f.extracted.confidence >= 40 ? '#d97706' : '#dc2626'} />}
                  <p style={{ fontSize: 12, color: '#16a34a', fontWeight: 600, alignSelf: 'center', marginLeft: 'auto' }}>✓ Added to dashboard</p>
                </div>
              )}
              {f.extracted && f.extracted.status === 'duplicate' && (
                <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(107,114,128,0.06)', border: '1px solid rgba(107,114,128,0.2)', borderRadius: 10 }}>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>File already processed — skipped to avoid duplicates.</p>
                </div>
              )}
              {f.extracted && f.extracted.status === 'error' && (
                <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.2)', borderRadius: 10 }}>
                  <p style={{ fontSize: 12, color: '#dc2626' }}>Extraction failed: {f.extracted.error || 'unknown error'}</p>
                </div>
              )}
              {f.extracting && (
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 14, height: 14, border: '2px solid rgba(115,31,227,0.2)', borderTopColor: '#731FE3', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                  <p style={{ fontSize: 12, color: '#731FE3' }}>AI extracting project data...</p>
                  <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ExResult({ label, value, color }) {
  return (
    <div>
      <p style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 2 }}>{label}</p>
      <p style={{ fontSize: 13, fontWeight: 600, color }}>{value}</p>
    </div>
  )
}

function StatusChip({ file }) {
  if (file.status === 'error') return <span style={{ fontSize: 11, fontWeight: 600, color: '#dc2626', background: 'rgba(220,38,38,0.08)', padding: '3px 10px', borderRadius: 99, border: '1px solid rgba(220,38,38,0.2)' }}>Error</span>
  if (file.extracting) return <span style={{ fontSize: 11, fontWeight: 600, color: '#731FE3', background: 'rgba(115,31,227,0.08)', padding: '3px 10px', borderRadius: 99, border: '1px solid rgba(115,31,227,0.2)' }}>Extracting...</span>
  if (file.extracted?.status === 'ok') return <span style={{ fontSize: 11, fontWeight: 600, color: '#16a34a', background: 'rgba(22,163,74,0.08)', padding: '3px 10px', borderRadius: 99, border: '1px solid rgba(22,163,74,0.2)' }}>✓ Processed</span>
  if (file.extracted?.status === 'duplicate') return <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', background: 'var(--bg)', padding: '3px 10px', borderRadius: 99, border: '1px solid var(--border)' }}>Duplicate</span>
  return <span style={{ fontSize: 11, fontWeight: 600, color: '#d97706', background: 'rgba(217,119,6,0.08)', padding: '3px 10px', borderRadius: 99, border: '1px solid rgba(217,119,6,0.2)' }}>Uploading...</span>
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
