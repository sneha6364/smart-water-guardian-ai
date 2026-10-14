import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, generateRecommendation } from '../services/api'
import { Loading, EmptyState, DemoModeBanner, StatCard, SectionTitle } from '../components/UI'

export default function DashboardPage({ farmerId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [genLoading, setGenLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!farmerId) return
    setLoading(true)
    getDashboard(farmerId)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load dashboard'))
      .finally(() => setLoading(false))
  }, [farmerId])

  const handleGenerate = async () => {
    if (!data?.farms?.[0]?.id) return
    setGenLoading(true)
    try {
      await generateRecommendation(data.farms[0].id)
      const r = await getDashboard(farmerId)
      setData(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate recommendation')
    } finally { setGenLoading(false) }
  }

  if (!farmerId) return (
    <div className="container" style={{ padding: '40px 16px' }}>
      <EmptyState icon="👤" title="No farmer selected"
        message="Register a farmer or select one from the navigation bar." />
      <div style={{ textAlign: 'center', marginTop: 16 }}>
        <Link to="/register" className="btn btn-primary">Register Farmer</Link>
      </div>
    </div>
  )

  if (loading) return <Loading text="Loading dashboard…" />
  if (error) return <div className="container"><div className="alert alert-danger">{error}</div></div>
  if (!data) return null

  const rec = data.latest_recommendation
  const water = data.latest_water_storage

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub={`Farmer: ${data.farmer?.name || '—'} · ${data.farms?.length || 0} farm(s) registered`}>
        📊 Farm Dashboard
      </SectionTitle>

      {!rec && <DemoModeBanner />}
      {data.water_shortage_alert && (
        <div className="alert alert-danger">
          ⚠️ <strong>Water Shortage Alert!</strong> Estimated {data.days_water_remaining?.toFixed(1)} days of water remaining.
          Consider emergency water sourcing and minimum irrigation.
        </div>
      )}

      {/* Stats row */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <StatCard icon="🌾" value={data.active_crops?.[0]?.crop_type ?? '—'}
          label="Active Crop" sub={data.active_crops?.[0]?.growth_stage ?? 'stage unknown'} />
        <StatCard icon="💧"
          value={water ? `${(water.storage_litres / 1000).toFixed(1)} kL` : '—'}
          label="Water Storage" sub={water ? `Recorded ${new Date(water.recorded_at).toLocaleDateString()}` : 'Not recorded'} />
        <StatCard icon="⏳"
          value={data.days_water_remaining != null ? `${data.days_water_remaining.toFixed(1)} days` : '—'}
          label="Water Remaining" alert={data.water_shortage_alert} />
        <StatCard icon="🚿"
          value={rec?.estimated_water_requirement_litres ? `${(rec.estimated_water_requirement_litres / 1000).toFixed(1)} kL` : '—'}
          label="Est. Irrigation Need" sub="next 3 days" />
      </div>

      {/* Recommendation card */}
      <div className="card" style={{ marginBottom: 16, borderTop: '4px solid var(--green)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
          <h3 style={{ marginBottom: 8 }}>🤖 Latest Recommendation</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            {rec && !rec.ai_available && <span className="badge badge-orange">Demo Mode</span>}
            {rec?.ai_available && <span className="badge badge-green">Groq AI ✓</span>}
          </div>
        </div>
        {rec ? (
          <>
            <div style={{ background: 'var(--green-light)', borderRadius: 6, padding: '10px 14px', marginBottom: 10 }}>
              <strong>{rec.recommended_action}</strong>
            </div>
            <p style={{ fontSize: 14, marginBottom: 8 }}>{rec.reason}</p>
            {rec.weather_summary && <p style={{ fontSize: 13, color: 'var(--neutral-700)' }}>🌤️ {rec.weather_summary}</p>}
            {rec.water_budget_summary && <p style={{ fontSize: 13, color: 'var(--neutral-700)' }}>💧 {rec.water_budget_summary}</p>}
            {rec.uncertainty && (
              <div className="alert alert-info" style={{ marginTop: 8, fontSize: 13 }}>
                ℹ️ <strong>Uncertainty:</strong> {rec.uncertainty}
              </div>
            )}
            {rec.missing_information && (
              <div className="alert alert-warning" style={{ fontSize: 13 }}>
                ⚠️ <strong>Missing data:</strong> {rec.missing_information}
              </div>
            )}
            {rec.evidence_sources?.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--neutral-500)' }}>📚 Sources: </span>
                {rec.evidence_sources.map((s, i) => (
                  <a key={i} href={s.url || '#'} target="_blank" rel="noreferrer"
                    className="tag" style={{ fontSize: 11 }}>{s.title}</a>
                ))}
              </div>
            )}
            <p style={{ fontSize: 11, color: 'var(--neutral-500)', marginTop: 8 }}>
              Generated: {new Date(rec.created_at).toLocaleString()}
            </p>
          </>
        ) : (
          <p style={{ color: 'var(--neutral-500)', fontSize: 14 }}>
            No recommendation yet. Click below to generate one.
          </p>
        )}

        <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={handleGenerate} disabled={genLoading || !data.farms?.length}>
            {genLoading ? '⏳ Generating…' : '🔄 Generate Recommendation'}
          </button>
          <Link to="/planner" className="btn btn-outline btn-sm">Open Planner →</Link>
        </div>
      </div>

      {/* Farms */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 12 }}>🌿 Registered Farms</h3>
        {data.farms?.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>Farm</th><th>Area (ha)</th><th>Soil</th><th>Irrigation</th><th>Storage (L)</th>
              </tr></thead>
              <tbody>
                {data.farms.map(f => (
                  <tr key={f.id}>
                    <td><strong>{f.name}</strong><br/><span style={{ fontSize: 11, color: 'var(--neutral-500)' }}>{f.latitude ? `${f.latitude.toFixed(4)}, ${f.longitude.toFixed(4)}` : 'No coordinates'}</span></td>
                    <td>{f.area_hectares ?? '—'}</td>
                    <td>{f.soil_type ?? '—'}</td>
                    <td>{f.irrigation_method ?? '—'}</td>
                    <td>{f.water_storage_litres?.toLocaleString() ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p style={{ color: 'var(--neutral-500)' }}>No farms registered yet.</p>}
      </div>

      {/* Recent events */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>📅 Recent Irrigation Events</h3>
        {data.recent_events?.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Water Used (L)</th><th>Method</th><th>Notes</th></tr></thead>
              <tbody>
                {data.recent_events.map(e => (
                  <tr key={e.id}>
                    <td>{new Date(e.irrigated_at).toLocaleDateString()}</td>
                    <td>{e.water_used_litres?.toLocaleString() ?? '—'}</td>
                    <td>{e.method ?? '—'}</td>
                    <td>{e.notes ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState icon="🚿" title="No events recorded" message="Record irrigation events after irrigating." />}
      </div>
    </div>
  )
}
