const NAV = [
  { name: 'dashboard', label: 'Overview',  icon: GridIcon },
  { name: 'emails',    label: 'Emails',    icon: EmailIcon },
  { name: 'report',    label: 'Report',    icon: ReportIcon },
  { name: 'uploads',   label: 'Files',     icon: UploadIcon },
]

export default function Sidebar({ current, navigate }) {
  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0,
      width: 'var(--sidebar-width)',
      height: '100vh',
      background: '#111',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '28px 16px',
      zIndex: 100,
    }}>
      {/* Logo mark */}
      <div style={{ padding: '0 8px', marginBottom: 36 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
          boxShadow: '0 0 20px rgba(124,58,237,0.4)',
        }} />
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV.map(({ name, label, icon: Icon }) => {
          const active = current === name || (name === 'dashboard' && ['project','customer'].includes(current))
          return (
            <button key={name} onClick={() => navigate(name)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px', borderRadius: 8, border: 'none',
                background: active ? 'rgba(124,58,237,0.15)' : 'transparent',
                color: active ? 'var(--accent-light)' : 'var(--text-secondary)',
                fontSize: 14, fontWeight: active ? 600 : 400,
                cursor: 'pointer', width: '100%', textAlign: 'left',
                transition: 'var(--transition)',
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)' }}
              onMouseLeave={e => { e.currentTarget.style.background = active ? 'rgba(124,58,237,0.15)' : 'transparent'; e.currentTarget.style.color = active ? 'var(--accent-light)' : 'var(--text-secondary)' }}
            >
              <Icon size={16} />
              {label}
            </button>
          )
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '0 8px' }}>
        <div style={{ width: '100%', height: 1, background: 'var(--border)', marginBottom: 16 }} />
        <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
          Email Report<br />Automation
        </p>
      </div>
    </aside>
  )
}

function GridIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="9" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="1" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="9" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
    </svg>
  )
}

function ReportIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M9 1H3.5A1.5 1.5 0 002 2.5v11A1.5 1.5 0 003.5 15h9a1.5 1.5 0 001.5-1.5V6L9 1z" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M9 1v5h5M5 9h6M5 12h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function EmailIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M1.5 4L8 9.5L14.5 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function UploadIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 10V3M8 3L5.5 5.5M8 3L10.5 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M2 11v1.5A1.5 1.5 0 003.5 14h9a1.5 1.5 0 001.5-1.5V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  )
}
