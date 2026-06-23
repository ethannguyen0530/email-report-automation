import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import CustomerDetail from './pages/CustomerDetail'
import Uploads from './pages/Uploads'
import './App.css'

export default function App() {
  const [page, setPage] = useState({ name: 'dashboard' })
  const navigate = (name, id) => setPage({ name, id })

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      <Sidebar current={page.name} navigate={navigate} />
      <main style={{
        flex: 1,
        marginLeft: 'var(--sidebar-width)',
        padding: '40px 48px',
        minHeight: '100vh',
        overflowY: 'auto',
      }}>
        {page.name === 'dashboard'  && <Dashboard navigate={navigate} />}
        {page.name === 'project'    && <ProjectDetail id={page.id} navigate={navigate} />}
        {page.name === 'customer'   && <CustomerDetail id={page.id} navigate={navigate} />}
        {page.name === 'uploads'    && <Uploads />}
      </main>
    </div>
  )
}
