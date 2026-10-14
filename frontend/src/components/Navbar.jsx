import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { listFarmers } from '../services/api'

const navLinks = [
  { path: '/',          label: 'Home' },
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/planner',   label: 'Planner' },
  { path: '/budget',    label: 'Water Budget' },
  { path: '/scenarios', label: 'What-If' },
  { path: '/history',   label: 'History' },
  { path: '/knowledge', label: 'Knowledge' },
]

export default function Navbar({ activeFarmerId, onSelectFarmer }) {
  const location = useLocation()
  const [farmers, setFarmers] = useState([])
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    listFarmers().then(r => setFarmers(r.data)).catch(() => {})
  }, [])

  return (
    <nav style={styles.nav}>
      <div className="container" style={styles.inner}>
        <Link to="/" style={styles.brand}>
          <span style={styles.dropIcon}>💧</span>
          <span>Smart Water Guardian</span>
        </Link>

        {/* Desktop links */}
        <div style={styles.links} className="hide-mobile">
          {navLinks.map(l => (
            <Link
              key={l.path}
              to={l.path}
              style={{
                ...styles.link,
                ...(location.pathname === l.path ? styles.linkActive : {}),
              }}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Farmer selector */}
        <div style={styles.farmerSel}>
          {farmers.length > 0 && (
            <select
              value={activeFarmerId || ''}
              onChange={e => onSelectFarmer(parseInt(e.target.value))}
              style={styles.select}
            >
              <option value="">Select farmer…</option>
              {farmers.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          )}
          <Link to="/register" className="btn btn-primary btn-sm">+ Register</Link>
        </div>

        {/* Mobile hamburger */}
        <button
          style={styles.hamburger}
          onClick={() => setMenuOpen(o => !o)}
          aria-label="Menu"
        >☰</button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div style={styles.mobileMenu}>
          {navLinks.map(l => (
            <Link key={l.path} to={l.path} style={styles.mobileLink}
              onClick={() => setMenuOpen(false)}>{l.label}</Link>
          ))}
        </div>
      )}
    </nav>
  )
}

const styles = {
  nav:        { background: 'var(--green-dark)', color: '#fff', position: 'sticky', top: 0, zIndex: 100, boxShadow: '0 2px 8px rgba(0,0,0,0.2)' },
  inner:      { display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', flexWrap: 'wrap' },
  brand:      { display: 'flex', alignItems: 'center', gap: 8, color: '#fff', fontWeight: 800, fontSize: 18, textDecoration: 'none' },
  dropIcon:   { fontSize: 22 },
  links:      { display: 'flex', gap: 4, flex: 1, justifyContent: 'center', flexWrap: 'wrap' },
  link:       { color: 'rgba(255,255,255,0.85)', padding: '6px 10px', borderRadius: 6, fontSize: 14, textDecoration: 'none', transition: 'background 0.2s' },
  linkActive: { background: 'rgba(255,255,255,0.2)', color: '#fff' },
  farmerSel:  { display: 'flex', gap: 8, alignItems: 'center' },
  select:     { padding: '5px 8px', borderRadius: 6, border: 'none', fontSize: 13, background: 'rgba(255,255,255,0.15)', color: '#fff', cursor: 'pointer' },
  hamburger:  { background: 'none', border: 'none', color: '#fff', fontSize: 22, cursor: 'pointer', display: 'none' },
  mobileMenu: { background: 'var(--green)', padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 2 },
  mobileLink: { color: '#fff', padding: '8px 4px', fontSize: 15, textDecoration: 'none', borderBottom: '1px solid rgba(255,255,255,0.15)' },
}
