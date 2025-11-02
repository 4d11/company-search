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
        <nav style={{
          padding: '1rem 2rem',
          background: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <Link to="/" style={{ textDecoration: 'none', color: '#1976d2', fontWeight: 500 }}>
            Search
          </Link>
          <Link to="/admin" style={{
            textDecoration: 'none',
            color: '#9ca3af',
            fontSize: '0.875rem',
            fontWeight: 400,
          }}>
            Admin
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
