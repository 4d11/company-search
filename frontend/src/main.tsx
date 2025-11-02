import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import App from './App.tsx'
import { AdminDashboard } from './pages/AdminDashboard.tsx'
import './index.css'

function AppWithRoutes() {
  return (
    <BrowserRouter>
      <div>
        {/* Simple navigation */}
        <nav style={{
          padding: '1rem',
          background: '#f5f5f5',
          borderBottom: '1px solid #ddd',
          marginBottom: '1rem'
        }}>
          <Link to="/" style={{ marginRight: '1rem', textDecoration: 'none', color: '#1976d2', fontWeight: 500 }}>
            Search
          </Link>
          <Link to="/admin" style={{ textDecoration: 'none', color: '#1976d2', fontWeight: 500 }}>
            Admin Dashboard
          </Link>
        </nav>

        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppWithRoutes />
  </React.StrictMode>,
)
