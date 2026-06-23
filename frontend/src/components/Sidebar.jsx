const NAV = [
  { name: 'dashboard',  label: 'Overview',   icon: GridIcon },
  { name: 'emails',     label: 'Emails',     icon: EmailIcon },
  { name: 'customers',  label: 'Customers',  icon: CustomerIcon },
  { name: 'report',     label: 'Report',     icon: ReportIcon },
  { name: 'uploads',    label: 'Files',      icon: UploadIcon },
  { name: 'settings',   label: 'Recipients', icon: SettingsIcon },
]

export default function Sidebar({ current, navigate }) {
  return (
    <aside style={{
      position: 'fixed', top: 0, left: 0,
      width: 'var(--sidebar-width)',
      height: '100vh',
      background: '#0A0545',
      borderRight: '1px solid rgba(115,31,227,0.25)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 14px 20px',
      zIndex: 100,
    }}>
      {/* Autonomize brand mark */}
      <div style={{ padding: '0 8px', marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10,
            background: 'linear-gradient(135deg, #731FE3, #9B51E0)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(115,31,227,0.45)',
            flexShrink: 0,
          }}>
            <span style={{ color: '#fff', fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 16, letterSpacing: '-0.5px' }}>A</span>
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-heading)', lineHeight: 1.2 }}>Autonomize</p>
            <p style={{ fontSize: 10, color: 'rgba(192,132,252,0.75)', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Project Intel</p>
          </div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV.map(({ name, label, icon: Icon }) => {
          const active = current === name
            || (name === 'dashboard' && ['project'].includes(current))
            || (name === 'customers' && current === 'customer')
          return (
            <button key={name} onClick={() => navigate(name)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 8, border: 'none',
                background: active ? 'rgba(115,31,227,0.18)' : 'transparent',
                color: active ? '#c084fc' : 'rgba(255,255,255,0.55)',
                fontSize: 13, fontWeight: active ? 600 : 400,
                cursor: 'pointer', width: '100%', textAlign: 'left',
                transition: 'var(--transition)',
                borderLeft: active ? '2px solid #731FE3' : '2px solid transparent',
              }}
              onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = '#ffffff' } }}
              onMouseLeave={e => { e.currentTarget.style.background = active ? 'rgba(115,31,227,0.18)' : 'transparent'; e.currentTarget.style.color = active ? '#c084fc' : 'rgba(255,255,255,0.55)' }}
            >
              <Icon size={15} />
              {label}
            </button>
          )
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '0 8px', borderTop: '1px solid rgba(115,31,227,0.12)', paddingTop: 16 }}>
        <p style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Intelligence Platform</p>
        <p style={{ fontSize: 10, color: 'rgba(115,31,227,0.5)', marginTop: 2 }}>autonomize.ai</p>
      </div>
    </aside>
  )
}

function GridIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="9" y="1" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="1" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
      <rect x="9" y="9" width="6" height="6" rx="1.5" fill="currentColor" opacity="0.9"/>
    </svg>
  )
}

function ReportIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M9 1H3.5A1.5 1.5 0 002 2.5v11A1.5 1.5 0 003.5 15h9a1.5 1.5 0 001.5-1.5V6L9 1z" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M9 1v5h5M5 9h6M5 12h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function EmailIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M1.5 4L8 9.5L14.5 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function UploadIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 10V3M8 3L5.5 5.5M8 3L10.5 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M2 11v1.5A1.5 1.5 0 003.5 14h9a1.5 1.5 0 001.5-1.5V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  )
}

function CustomerIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <circle cx="6" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M1 13c0-2.761 2.239-4 5-4s5 1.239 5 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <path d="M12 7v4M10 9h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}

function SettingsIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M2.93 2.93l1.41 1.41M11.66 11.66l1.41 1.41M2.93 13.07l1.41-1.41M11.66 4.34l1.41-1.41" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  )
}
