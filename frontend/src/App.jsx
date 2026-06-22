import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import CustomerDetail from './pages/CustomerDetail'
import './App.css'

export default function App() {
  const [page, setPage] = useState({ name: 'dashboard' })

  const navigate = (name, id) => setPage({ name, id })

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header navigate={navigate} />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 20px' }}>
        {page.name === 'dashboard' && <Dashboard navigate={navigate} />}
        {page.name === 'project' && <ProjectDetail id={page.id} navigate={navigate} />}
        {page.name === 'customer' && <CustomerDetail id={page.id} navigate={navigate} />}
      </main>
    </div>
  )
}

function Header({ navigate }) {
  return (
    <header style={{
      background: '#1e293b',
      color: 'white',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      height: 56,
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
    }}>
      <button
        onClick={() => navigate('dashboard')}
        style={{ background: 'none', border: 'none', color: 'white', fontSize: 18, fontWeight: 700, cursor: 'pointer', letterSpacing: '-0.3px' }}
      >
        Project Dashboard
      </button>
    </header>
  )
}
