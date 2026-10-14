import React from 'react'

export function Spinner() {
  return <span className="spinner" />
}

export function Loading({ text = 'Loading…' }) {
  return (
    <div className="loading-center">
      <Spinner /> <span>{text}</span>
    </div>
  )
}

export function EmptyState({ icon = '📭', title = 'No data', message = '' }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--neutral-500)' }}>
      <div style={{ fontSize: 40, marginBottom: 8 }}>{icon}</div>
      <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--neutral-700)' }}>{title}</div>
      {message && <div style={{ fontSize: 14, marginTop: 4 }}>{message}</div>}
    </div>
  )
}

export function DemoModeBanner() {
  return (
    <div className="alert alert-demo">
      🧪 <strong>Demo Mode:</strong> Groq AI is not configured. Showing deterministic calculations
      with sample weather data. Set <code>GROQ_API_KEY</code> in <code>.env</code> to enable AI explanations.
    </div>
  )
}

export function AIUnavailableBanner() {
  return (
    <div className="alert alert-info" style={{ fontSize: 13 }}>
      ℹ️ AI explanation unavailable. Showing verified deterministic calculation results.
    </div>
  )
}

export function StatCard({ value, label, sub, icon, alert }) {
  return (
    <div className={`card stat-card ${alert ? 'alert-danger' : ''}`} style={{ borderTop: alert ? '3px solid var(--red)' : '3px solid var(--green)' }}>
      {icon && <div style={{ fontSize: 28, marginBottom: 4 }}>{icon}</div>}
      <div className="stat-value" style={alert ? { color: 'var(--red)' } : {}}>{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export function SectionTitle({ children, sub }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h2 className="section-title">{children}</h2>
      {sub && <p className="section-subtitle">{sub}</p>}
    </div>
  )
}
