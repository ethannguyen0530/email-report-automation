import { useEffect, useRef, useState } from 'react'
import MetricCard from '../components/MetricCard'
import StatusSelect from '../components/StatusSelect'
import ProgressBar from '../components/ProgressBar'

const DONE_STATUSES = ['Completed']
const STALE_DAYS = 7

const FILTER_MAP = {
  'Total':     null,
  'On Track':  'On Track',
  'At Risk':   'At Risk',
  'Delayed':   'Delayed',
  'Completed': 'Completed',
}

function isStale(lastUpdated, status) {
  if (DONE_STATUSES.includes(status)) return false
  if (!lastUpdated) return true
  const diff = (Date.now() - new Date(lastUpdated)) / (1000 * 60 * 60 * 24)
  return diff > STALE_DAYS
}

function fmtDate(str) {
  if (!str) return '—'
  try {
    const d = new Date(str)
    const diff = Math.floor((Date.now() - d) / (1000 * 60 * 60 * 24))
    if (diff === 0) return 'Today'
    if (diff === 1) return 'Yesterday'
    if (diff < 7) return `${diff}d ago`
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch { return str?.slice(0, 10) || '—' }
}

export default function Dashboard({ navigate }) {
  const [summary, setSummary] = useState(null)
  const [projects, setProjects] = useState([])
  const [health, setHealth] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [filter, setFilter] = useState(null)
  const [error, setError] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanMsg, setScanMsg] = useState(null)
  const [liveStatus, setLiveStatus] = useState(null)
  const [healthModal, setHealthModal] = useState(false)
  const [projectHealthModal, setProjectHealthModal] = useState(null) // health project object
  const [emailModal, setEmailModal] = useState(null) // { loading, email, error }
  const _emailAbort = useRef(null)   // AbortController for in-flight email-detail fetch
  const _updateVer = useRef(0)       // version counter to discard stale status re-fetches

  const loadData = () => {
    fetch('/api/summary')
      .then(r => r.json())
      .then(data => { setSummary(data); setProjects(data.projects) })
      .catch(() => setError('Cannot connect to Flask API. Run: bash ~/email-report-automation/start.sh'))
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => {})
    fetch('/api/alerts').then(r => r.json()).then(setAlerts).catch(() => {})
  }

  useEffect(() => {
    loadData()
    const es = new EventSource('/api/stream')
    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'scan_complete' || msg.type === 'connected') {
          setLiveStatus({ time: msg.time, newEmails: msg.new_emails || 0, total: msg.total || 0, flagged: msg.flagged || 0 })
          if (msg.new_emails > 0) loadData()
        }
      } catch {}
    }
    es.onerror = () => {}
    return () => es.close()
  }, [])

  const openEmailModal = (gmailId) => {
    if (!gmailId) {
      setEmailModal({ loading: false, email: null, error: 'No source email linked to this item (may be from an older scan).' })
      return
    }
    // Cancel any in-flight request so rapid row-clicks always show the last-clicked email
    if (_emailAbort.current) _emailAbort.current.abort()
    const controller = new AbortController()
    _emailAbort.current = controller
    setEmailModal({ loading: true, email: null, error: null })
    fetch(`/api/email-detail/${encodeURIComponent(gmailId)}`, { signal: controller.signal })
      .then(r => r.json())
      .then(data => {
        if (data.error) setEmailModal({ loading: false, email: null, error: data.error })
        else setEmailModal({ loading: false, email: data, error: null })
      })
      .catch(err => {
        if (err.name === 'AbortError') return
        setEmailModal({ loading: false, email: null, error: 'Failed to load email.' })
      })
  }

  const scanNow = async () => {
    setScanning(true)
    setScanMsg(null)
    try {
      const res = await fetch('/api/scan-now', { method: 'POST' })
      const data = await res.json()
      setScanMsg(data.ok ? 'Scan started — data updates in ~30s' : 'Scan failed')
      setTimeout(() => { loadData(); setScanMsg(null) }, 30000)
    } catch {
      setScanMsg('Scan failed — server unreachable')
    }
    setScanning(false)
  }

  const updateStatus = (id, newStatus) => {
    setProjects(prev => prev.map(p => p.id === id ? { ...p, status: newStatus } : p))
    // Version counter: if the user changes status again before this re-fetch resolves,
    // the older chain is stale and must not overwrite the newer optimistic state.
    const v = ++_updateVer.current
    Promise.all([
      fetch('/api/summary').then(r => r.json()),
      fetch('/api/health').then(r => r.json()),
      fetch('/api/alerts').then(r => r.json()),
    ]).then(([sumData, healthData, alertsData]) => {
      if (v < _updateVer.current) return  // a newer updateStatus call is in flight — discard this stale result
      setSummary(sumData)
      // Re-apply this call's change on top of server data in case the re-fetch narrowly
      // raced with the PATCH commit (server data reflects old value).
      setProjects(sumData.projects.map(p => p.id === id ? { ...p, status: newStatus } : p))
      setHealth(healthData)
      setAlerts(alertsData)
    }).catch(() => {})
  }

  const handleFilter = (label) => {
    const next = FILTER_MAP[label]
    setFilter(prev => prev === next ? null : next)
  }

  if (error) return <ErrorMsg msg={error} />
  if (!summary) return <Loading />

  const visibleProjects = filter ? projects.filter(p => p.status === filter) : projects
  const staleCount = projects.filter(p => isStale(p.last_updated, p.status)).length
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  const portfolioScore = health?.portfolio_score ?? null
  const healthColor = portfolioScore === null ? '#731FE3' : portfolioScore >= 70 ? '#16a34a' : portfolioScore >= 40 ? '#d97706' : '#dc2626'
  const alertCount = (alerts?.stale_customers?.length || 0) + (alerts?.flagged_emails || 0)

  const metrics = [
    { label: 'Total',     value: summary.total_projects, color: '#7c3aed' },
    { label: 'On Track',  value: summary.on_track,       color: '#22c55e' },
    { label: 'At Risk',   value: summary.at_risk,        color: '#f59e0b' },
    { label: 'Delayed',   value: summary.delayed,        color: '#ef4444' },
    { label: 'Completed', value: summary.completed,      color: '#6b7280' },
  ]

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 36 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>{date}</p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>Executive Overview</h1>
            {staleCount > 0 && (
              <span style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.25)', padding: '4px 12px', borderRadius: 99, fontSize: 12, fontWeight: 600 }}>
                {staleCount} need attention
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Live indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(115,31,227,0.1)', border: '1px solid rgba(115,31,227,0.2)', padding: '5px 12px', borderRadius: 99 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#731FE3', boxShadow: '0 0 6px #731FE3', display: 'inline-block', animation: 'pulse 2s ease-in-out infinite' }} />
              <span style={{ fontSize: 11, color: '#c084fc', fontWeight: 500 }}>
                {liveStatus ? `Live · ${liveStatus.total} emails tracked` : 'Live'}
              </span>
            </div>
            <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }`}</style>
            {scanMsg && <span style={{ fontSize: 12, color: scanMsg.includes('failed') ? '#ef4444' : '#22c55e' }}>{scanMsg}</span>}
            <button onClick={scanNow} disabled={scanning}
              style={{ background: 'rgba(115,31,227,0.12)', border: '1px solid rgba(115,31,227,0.3)', color: '#c084fc', padding: '7px 14px', borderRadius: 8, fontSize: 12, fontWeight: 500, cursor: scanning ? 'not-allowed' : 'pointer', opacity: scanning ? 0.6 : 1, display: 'flex', alignItems: 'center', gap: 6, transition: 'var(--transition)' }}>
              <span style={{ fontSize: 14, lineHeight: 1 }}>{scanning ? '⟳' : '↻'}</span>
              {scanning ? 'Scanning...' : 'Scan Now'}
            </button>
          </div>
        </div>
      </div>

      {/* Smart Alerts */}
      {alertCount > 0 && (
        <div style={{ background: 'rgba(248,100,66,0.06)', border: '1px solid rgba(248,100,66,0.2)', borderRadius: 'var(--radius)', padding: '14px 20px', marginBottom: 24, display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#F86442', textTransform: 'uppercase', letterSpacing: '0.08em', flexShrink: 0 }}>⚡ Smart Alerts</span>
          {alerts?.stale_customers?.map(c => (
            <span key={c.name} style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'rgba(248,100,66,0.08)', padding: '4px 12px', borderRadius: 99, border: '1px solid rgba(248,100,66,0.15)' }}>
              No update from <strong>{c.name}</strong> in 7+ days
            </span>
          ))}
          {alerts?.flagged_emails > 0 && (
            <span style={{ fontSize: 12, color: '#dc2626', background: 'rgba(220,38,38,0.08)', padding: '4px 12px', borderRadius: 99, border: '1px solid rgba(220,38,38,0.2)' }}>
              ⚠ {alerts.flagged_emails} email{alerts.flagged_emails !== 1 ? 's' : ''} need manual review
            </span>
          )}
        </div>
      )}

      {/* Portfolio Health + Metrics */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 36, alignItems: 'stretch' }}>
        {portfolioScore !== null && (
          <>
            <div onClick={() => setHealthModal(true)} title="Click for breakdown"
              style={{ background: 'var(--bg-card)', border: `1px solid ${healthColor}33`, borderRadius: 'var(--radius)', padding: '20px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minWidth: 120, gap: 8, flexShrink: 0, cursor: 'pointer', transition: 'all 0.15s' }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = `0 4px 16px ${healthColor}22`; e.currentTarget.style.borderColor = `${healthColor}55` }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.borderColor = `${healthColor}33` }}
            >
              <div style={{ position: 'relative', width: 64, height: 64 }}>
                <svg viewBox="0 0 64 64" style={{ transform: 'rotate(-90deg)', width: 64, height: 64 }}>
                  <circle cx="32" cy="32" r="26" fill="none" stroke={`${healthColor}18`} strokeWidth="6" />
                  <circle cx="32" cy="32" r="26" fill="none" stroke={healthColor} strokeWidth="6"
                    strokeDasharray={`${2 * Math.PI * 26}`}
                    strokeDashoffset={`${2 * Math.PI * 26 * (1 - portfolioScore / 100)}`}
                    strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
                </svg>
                <span style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, color: healthColor }}>{portfolioScore}</span>
              </div>
              <p style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, textAlign: 'center', fontFamily: 'var(--font-heading)', lineHeight: 1.3 }}>Portfolio Health</p>
              <p style={{ fontSize: 10, color: healthColor, opacity: 0.7 }}>click for details</p>
            </div>

            {/* Health breakdown modal */}
            {healthModal && (
              <div onClick={() => setHealthModal(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(10,5,69,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
                <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-card)', borderRadius: 16, padding: '28px 32px', width: '100%', maxWidth: 480, boxShadow: '0 20px 60px rgba(10,5,69,0.3)', border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                    <div>
                      <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-heading)', marginBottom: 4 }}>Portfolio Health Breakdown</h2>
                      <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Score is based on status, blockers, and recency of updates</p>
                    </div>
                    <button onClick={() => setHealthModal(false)} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', color: 'var(--text-muted)', fontSize: 16 }}>✕</button>
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 10 }}>Click any score circle for a detailed breakdown</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {health?.projects?.map(p => {
                      const pc = p.score >= 70 ? '#16a34a' : p.score >= 40 ? '#d97706' : '#dc2626'
                      const tag = p.score >= 70 ? 'Healthy' : p.score >= 40 ? 'Watch' : 'Critical'
                      return (
                        <div key={p.id} style={{ padding: '12px 14px', background: 'var(--bg)', borderRadius: 10, border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12, transition: 'background 0.1s' }}
                          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'var(--bg)'}
                        >
                          <div onClick={() => { setHealthModal(false); setProjectHealthModal(p) }}
                            title="Click for detailed breakdown"
                            style={{ width: 40, height: 40, borderRadius: '50%', background: `${pc}14`, border: `1.5px solid ${pc}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, cursor: 'pointer', transition: 'all 0.15s' }}
                            onMouseEnter={e => { e.currentTarget.style.background = `${pc}28`; e.currentTarget.style.transform = 'scale(1.1)' }}
                            onMouseLeave={e => { e.currentTarget.style.background = `${pc}14`; e.currentTarget.style.transform = 'scale(1)' }}
                          >
                            <span style={{ fontSize: 12, fontWeight: 700, color: pc }}>{p.score}</span>
                          </div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</p>
                            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{p.customer}</p>
                          </div>
                          <span style={{ fontSize: 11, fontWeight: 600, color: pc, background: `${pc}12`, padding: '3px 10px', borderRadius: 99, border: `1px solid ${pc}25`, flexShrink: 0 }}>{tag}</span>
                        </div>
                      )
                    })}
                  </div>
                  <div style={{ marginTop: 20, padding: '12px 14px', background: 'rgba(115,31,227,0.05)', borderRadius: 10, border: '1px solid rgba(115,31,227,0.1)' }}>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      <strong style={{ color: 'var(--text-secondary)' }}>How it's calculated:</strong> Starts at 100. Deductions: Delayed (−35), At Risk (−20), Active blocker (−25), No update in 14d (−20), No update in 7d (−10), Very low progress &lt;20% (−10).
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, flex: 1 }}>
          {metrics.map(({ label, value, color }) => (
            <MetricCard key={label} value={value} label={label} color={color}
              active={filter === FILTER_MAP[label]} onClick={() => handleFilter(label)} />
          ))}
        </div>
      </div>

      {/* Accomplishments + Blockers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
        <Card title="Recent Accomplishments" accent="#22c55e" subtitle="click any row to see source email">
          {summary.accomplishments.length === 0 ? <Empty>Nothing recorded yet.</Empty>
            : (() => {
              const items = summary.accomplishments_rich || summary.accomplishments.map(t => ({ text: t, gmail_id: null }))
              return items.map((a, i) => (
                <Row key={i} last={i === items.length - 1} onClick={() => openEmailModal(a.gmail_id)} clickable>
                  <span style={{ color: '#22c55e', fontSize: 14, flexShrink: 0 }}>✓</span>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{a.text || a}</span>
                  {a.gmail_id && <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 'auto', flexShrink: 0 }}>→</span>}
                </Row>
              ))
            })()}
        </Card>
        <Card title="Open Blockers" accent="#ef4444" subtitle="click any row to see source email">
          {summary.blockers.length === 0 ? <Empty>No blockers.</Empty>
            : (() => {
              const items = summary.blockers_rich || summary.blockers.map(t => ({ text: t, gmail_id: null }))
              return items.map((b, i) => (
                <Row key={i} last={i === items.length - 1} onClick={() => openEmailModal(b.gmail_id)} clickable>
                  <span style={{ color: '#ef4444', fontSize: 14, flexShrink: 0 }}>!</span>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{b.text || b}</span>
                  {b.gmail_id && <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 'auto', flexShrink: 0 }}>→</span>}
                </Row>
              ))
            })()}
        </Card>
      </div>

      {/* Projects table */}
      <Card
        title={filter ? `${filter} Projects` : 'All Projects'}
        accent={filter ? metrics.find(m => m.label === filter)?.color : undefined}
        right={filter && (
          <button onClick={() => setFilter(null)}
            style={{ fontSize: 12, color: 'var(--text-muted)', background: 'none', border: '1px solid var(--border)', borderRadius: 6, padding: '3px 10px', cursor: 'pointer' }}>
            Clear filter ×
          </button>
        )}
        subtitle={filter ? `${visibleProjects.length} of ${projects.length} projects` : `${projects.length} projects`}
      >
        {visibleProjects.length === 0 ? (
          <Empty>No projects with status "{filter}".</Empty>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {['Health', 'Project', 'Customer', 'Status', 'Progress', 'Owner', 'Last Updated'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid var(--border)' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleProjects.map(p => {
                const stale = isStale(p.last_updated, p.status)
                const hs = health?.projects?.find(h => h.id === p.id)
                const hScore = hs?.score ?? null
                const hColor = hScore === null ? 'var(--text-muted)' : hScore >= 70 ? '#16a34a' : hScore >= 40 ? '#d97706' : '#dc2626'
                return (
                  <tr key={p.id}
                    style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s', background: stale ? 'rgba(239,68,68,0.03)' : 'transparent' }}
                    onMouseEnter={e => e.currentTarget.style.background = stale ? 'rgba(239,68,68,0.07)' : 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = stale ? 'rgba(239,68,68,0.03)' : 'transparent'}
                  >
                    <td style={{ padding: '14px 16px', width: 60 }}>
                      {hScore !== null ? (
                        <div onClick={e => { e.stopPropagation(); setProjectHealthModal(hs) }}
                          title="Click for health breakdown"
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, borderRadius: '50%', background: `${hColor}14`, border: `1.5px solid ${hColor}44`, cursor: 'pointer', transition: 'all 0.15s' }}
                          onMouseEnter={e => { e.currentTarget.style.background = `${hColor}28`; e.currentTarget.style.transform = 'scale(1.1)' }}
                          onMouseLeave={e => { e.currentTarget.style.background = `${hColor}14`; e.currentTarget.style.transform = 'scale(1)' }}
                        >
                          <span style={{ fontSize: 11, fontWeight: 700, color: hColor }}>{hScore}</span>
                        </div>
                      ) : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {stale && <span title="No update in 7+ days" style={{ color: '#ef4444', fontSize: 16, lineHeight: 1 }}>⚑</span>}
                        <button onClick={() => navigate('project', p.id)}
                          style={{ background: 'none', border: 'none', color: stale ? '#ef4444' : 'var(--text-primary)', cursor: 'pointer', fontWeight: 600, fontSize: 13, padding: 0, textAlign: 'left' }}>
                          {p.name}
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{p.customer || '—'}</td>
                    <td style={{ padding: '14px 16px' }} onClick={e => e.stopPropagation()}>
                      <StatusSelect projectId={p.id} value={p.status} onChange={s => updateStatus(p.id, s)} />
                    </td>
                    <td style={{ padding: '14px 16px', minWidth: 140 }}><ProgressBar value={p.progress} /></td>
                    <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>{p.owner}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontSize: 12, color: stale ? '#ef4444' : 'var(--text-muted)', fontWeight: stale ? 600 : 400 }}>
                        {fmtDate(p.last_updated)}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </Card>

      {/* Project Health Breakdown Modal — with prev/next navigation */}
      {projectHealthModal && (() => {
        const allProjects = health?.projects?.filter(p => p.customer !== 'Unknown' && p.customer !== 'Unknown Customer') || []
        const currentIdx = allProjects.findIndex(p => p.id === projectHealthModal.id)
        const found = currentIdx > -1
        const hasPrev = found && currentIdx > 0
        const hasNext = found && currentIdx < allProjects.length - 1
        const sc = projectHealthModal.score
        const c = sc >= 70 ? '#16a34a' : sc >= 40 ? '#d97706' : '#dc2626'
        return (
          <div onClick={() => setProjectHealthModal(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(10,5,69,0.55)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
            <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-card)', borderRadius: 16, padding: '28px 32px', width: '100%', maxWidth: 480, boxShadow: '0 20px 60px rgba(10,5,69,0.3)', border: '1px solid var(--border)' }}>

              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Back-to-list button */}
                  <button onClick={() => { setProjectHealthModal(null); setHealthModal(true) }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: '#731FE3', padding: '0 0 8px', display: 'flex', alignItems: 'center', gap: 4 }}>
                    ← Back to all projects
                  </button>
                  <h2 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-heading)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{projectHealthModal.name}</h2>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {projectHealthModal.customer} · Score {sc}/100
                    {projectHealthModal.last_updated && (
                      <span style={{ marginLeft: 6, color: 'rgba(115,31,227,0.6)' }}>
                        · as of {new Date(projectHealthModal.last_updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    )}
                  </p>
                </div>
                <button onClick={() => setProjectHealthModal(null)} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', color: 'var(--text-muted)', fontSize: 16, flexShrink: 0, marginLeft: 12 }}>✕</button>
              </div>

              {/* Reasons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
                {(projectHealthModal.reasons || []).map((r, i) => {
                  const color = r.type === 'ok' ? '#16a34a' : r.type === 'warn' ? '#d97706' : '#dc2626'
                  const icon = r.type === 'ok' ? '✓' : r.type === 'warn' ? '⚠' : '✗'
                  const impactStr = r.impact < 0 ? `${r.impact} pts` : r.impact === 0 ? 'no change' : `+${r.impact} pts`
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: `${color}08`, borderRadius: 10, border: `1px solid ${color}20` }}>
                      <span style={{ color, fontSize: 13, fontWeight: 700, width: 16, flexShrink: 0 }}>{icon}</span>
                      <span style={{ fontSize: 13, color: 'var(--text-primary)', flex: 1 }}>{r.factor}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color, flexShrink: 0, minWidth: 60, textAlign: 'right' }}>{impactStr}</span>
                    </div>
                  )
                })}
              </div>

              {/* Score summary */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'rgba(115,31,227,0.05)', borderRadius: 10, border: '1px solid rgba(115,31,227,0.1)', marginBottom: 20 }}>
                <div style={{ width: 44, height: 44, borderRadius: '50%', background: `${c}14`, border: `2px solid ${c}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: c }}>{sc}</span>
                </div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  Final score: <strong style={{ color: c }}>{sc}/100</strong> — {sc >= 70 ? 'In good standing.' : sc >= 40 ? 'Needs attention.' : 'Requires immediate attention.'}
                </p>
              </div>

              {/* Prev / Next navigation */}
              {allProjects.length > 1 && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                  <button onClick={() => hasPrev && setProjectHealthModal(allProjects[currentIdx - 1])}
                    disabled={!hasPrev}
                    style={{ padding: '7px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'none', color: hasPrev ? 'var(--text-secondary)' : 'var(--text-muted)', cursor: hasPrev ? 'pointer' : 'not-allowed', fontSize: 13, opacity: hasPrev ? 1 : 0.4, transition: 'all 0.15s' }}>
                    ← {hasPrev ? allProjects[currentIdx - 1].name : 'Previous'}
                  </button>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{found ? `${currentIdx + 1} of ${allProjects.length}` : '—'}</span>
                  <button onClick={() => hasNext && setProjectHealthModal(allProjects[currentIdx + 1])}
                    disabled={!hasNext}
                    style={{ padding: '7px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'none', color: hasNext ? 'var(--text-secondary)' : 'var(--text-muted)', cursor: hasNext ? 'pointer' : 'not-allowed', fontSize: 13, opacity: hasNext ? 1 : 0.4, transition: 'all 0.15s' }}>
                    {hasNext ? allProjects[currentIdx + 1].name : 'Next'} →
                  </button>
                </div>
              )}
            </div>
          </div>
        )
      })()}

      {/* Email Source Modal (from accomplishments / blockers) */}
      {emailModal && (
        <div onClick={() => setEmailModal(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(10,5,69,0.55)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-card)', borderRadius: 16, padding: '28px 32px', width: '100%', maxWidth: 560, maxHeight: '80vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(10,5,69,0.3)', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexShrink: 0 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>Source Email</h2>
              <button onClick={() => setEmailModal(null)} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, width: 32, height: 32, cursor: 'pointer', color: 'var(--text-muted)', fontSize: 16 }}>✕</button>
            </div>

            {emailModal.loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '20px 0' }}>
                <div style={{ width: 16, height: 16, border: '2px solid rgba(115,31,227,0.2)', borderTopColor: '#731FE3', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Loading source email...</span>
                <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
              </div>
            )}

            {emailModal.error && (
              <div style={{ padding: '14px 16px', background: 'rgba(220,38,38,0.06)', borderRadius: 10, border: '1px solid rgba(220,38,38,0.2)' }}>
                <p style={{ fontSize: 13, color: '#dc2626' }}>{emailModal.error}</p>
              </div>
            )}

            {emailModal.email && (
              <>
                {/* AI summary — 1-2 sentences */}
                {emailModal.email.ai_summary && (
                  <div style={{ padding: '14px 16px', background: 'rgba(115,31,227,0.06)', borderRadius: 10, border: '1px solid rgba(115,31,227,0.15)', marginBottom: 16, flexShrink: 0 }}>
                    <p style={{ fontSize: 11, fontWeight: 700, color: '#731FE3', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>AI Summary</p>
                    <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>{emailModal.email.ai_summary}</p>
                  </div>
                )}
                {/* Metadata */}
                <div style={{ display: 'grid', gap: 6, marginBottom: 16, flexShrink: 0 }}>
                  <MetaRow label="Subject" value={emailModal.email.subject || '(no subject)'} />
                  <MetaRow label="From" value={emailModal.email.sender} />
                  <MetaRow label="Date" value={emailModal.email.date ? new Date(emailModal.email.date).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }) : '—'} />
                </div>
                {/* Body — scrollable */}
                <div style={{ flex: 1, overflowY: 'auto', borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 10 }}>Full Email</p>
                  <pre style={{ fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'var(--font-body)', wordBreak: 'break-word' }}>
                    {emailModal.email.body || '(no body content)'}
                  </pre>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function MetaRow({ label, value }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', minWidth: 60, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{value}</span>
    </div>
  )
}

function Card({ title, accent, children, right, subtitle }) {
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {accent && <div style={{ width: 3, height: 14, borderRadius: 99, background: accent }} />}
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{title}</h2>
          {subtitle && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>— {subtitle}</span>}
        </div>
        {right}
      </div>
      <div style={{ padding: '4px 20px 12px' }}>{children}</div>
    </div>
  )
}

function Row({ children, last, onClick, clickable }) {
  return (
    <div onClick={onClick} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '10px 0', borderBottom: last ? 'none' : '1px solid var(--border)', cursor: clickable ? 'pointer' : 'default', borderRadius: 6, transition: 'background 0.1s', paddingLeft: 4, paddingRight: 4 }}
      onMouseEnter={e => { if (clickable) e.currentTarget.style.background = 'var(--bg-hover)' }}
      onMouseLeave={e => { if (clickable) e.currentTarget.style.background = 'transparent' }}
    >
      {children}
    </div>
  )
}

function Empty({ children }) {
  return <p style={{ color: 'var(--text-muted)', fontSize: 13, padding: '12px 0' }}>{children}</p>
}

function Loading() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 32, height: 32, border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    </div>
  )
}

function ErrorMsg({ msg }) {
  return (
    <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius)', padding: 20, color: '#ef4444', fontSize: 13 }}>
      {msg}
    </div>
  )
}
