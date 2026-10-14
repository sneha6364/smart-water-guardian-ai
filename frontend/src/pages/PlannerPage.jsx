import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFarms, getWeather, generateRecommendation, listRecommendations } from '../services/api'
import { Loading, EmptyState, AIUnavailableBanner, SectionTitle } from '../components/UI'

export default function PlannerPage({ farmerId }) {
  const [farms, setFarms] = useState([])
  const [selectedFarm, setSelectedFarm] = useState(null)
  const [weather, setWeather] = useState(null)
  const [rec, setRec] = useState(null)
  const [loading, setLoading] = useState(false)
  const [genLoading, setGenLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!farmerId) return
    listFarms(farmerId).then(r => {
      setFarms(r.data)
      if (r.data.length) setSelectedFarm(r.data[0])
    }).catch(() => {})
  }, [farmerId])

  useEffect(() => {
    if (!selectedFarm?.latitude) return
    getWeather(selectedFarm.latitude, selectedFarm.longitude)
      .then(r => setWeather(r.data))
      .catch(() => {})
  }, [selectedFarm])

  const handleGenerate = async () => {
    if (!selectedFarm) return
    setGenLoading(true); setError('')
    try {
      const r = await generateRecommendation(selectedFarm.id)
      setRec(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate recommendation')
    } finally { setGenLoading(false) }
  }

  if (!farmerId) return (
    <div className="container" style={{ padding: 40 }}>
      <EmptyState icon="👤" title="No farmer selected" message="Select or register a farmer to use the planner." />
      <div style={{ textAlign: 'center', marginTop: 16 }}><Link to="/register" className="btn btn-primary">Register</Link></div>
    </div>
  )

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub="Weather · Crop water demand · AI recommendation">🌱 Irrigation Planner</SectionTitle>

      {/* Farm selector */}
      {farms.length > 1 && (
        <div className="form-group">
          <label className="form-label">Select Farm</label>
          <select className="form-select" style={{ maxWidth: 300 }}
            value={selectedFarm?.id || ''}
            onChange={e => setSelectedFarm(farms.find(f => f.id === parseInt(e.target.value)))}>
            {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
      )}

      {/* Weather card */}
      {selectedFarm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 10 }}>🌤️ 7-Day Weather Forecast</h3>
          {weather ? (
            <>
              {weather.error && <div className="alert alert-warning">{weather.error}</div>}
              <div className="grid-4">
                <div style={ws}><div style={wv}>{weather.summary?.total_rain_mm ?? '—'} mm</div><div style={wl}>Total Forecast Rain</div></div>
                <div style={ws}><div style={wv}>{weather.summary?.max_rain_probability_pct ?? '—'}%</div><div style={wl}>Max Rain Probability</div></div>
                <div style={ws}><div style={wv}>{weather.summary?.avg_et0_mm_day ?? '—'}</div><div style={wl}>Avg ET₀ (mm/day)</div></div>
                <div style={ws}><div style={wv}>{weather.summary?.next_rain_day ?? 'None'}</div><div style={wl}>Next Likely Rain Day</div></div>
              </div>
              <div style={{ overflowX: 'auto', marginTop: 12 }}>
                <table style={{ minWidth: 500 }}>
                  <thead><tr>
                    <th>Date</th><th>Rain (mm)</th><th>Prob (%)</th><th>ET₀ (mm)</th><th>Max Temp (°C)</th>
                  </tr></thead>
                  <tbody>
                    {(weather.daily?.time || []).map((d, i) => (
                      <tr key={d}>
                        <td>{d}</td>
                        <td>{weather.daily?.precipitation_sum?.[i] ?? '—'}</td>
                        <td>{weather.daily?.precipitation_probability_max?.[i] ?? '—'}</td>
                        <td>{weather.daily?.et0_fao_evapotranspiration?.[i] ?? '—'}</td>
                        <td>{weather.daily?.temperature_2m_max?.[i] ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p style={{ fontSize: 12, color: 'var(--neutral-500)', marginTop: 8 }}>
                Source: Open-Meteo · {weather.source === 'demo' ? '⚠️ Demo data' : `Fetched ${weather.fetched_at ? new Date(weather.fetched_at).toLocaleString() : ''}`}
                {' '}· ⚠️ Forecast probability ≠ guaranteed rainfall.
              </p>
            </>
          ) : <Loading text="Loading weather…" />}
        </div>
      )}

      {/* Generate button */}
      <div style={{ marginBottom: 16 }}>
        <button className="btn btn-primary" onClick={handleGenerate}
          disabled={genLoading || !selectedFarm} style={{ fontSize: 15, padding: '10px 24px' }}>
          {genLoading ? '⏳ Generating recommendation…' : '🤖 Generate Irrigation Recommendation'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Recommendation detail */}
      {rec && (
        <div className="card" style={{ borderTop: '4px solid var(--green)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
            <h3>🤖 Recommendation</h3>
            <span className={`badge ${rec.ai_available ? 'badge-green' : 'badge-orange'}`}>
              {rec.ai_available ? 'Groq AI ✓' : 'Demo Mode'}
            </span>
          </div>

          {!rec.ai_available && <AIUnavailableBanner />}

          <div style={{ background: 'var(--green-light)', borderRadius: 6, padding: '12px 16px', marginBottom: 12, fontSize: 15, fontWeight: 600 }}>
            {rec.recommended_action}
          </div>

          <div style={{ marginBottom: 8 }}>
            <strong>Explanation:</strong>
            <p style={{ fontSize: 14, marginTop: 4 }}>{rec.reason}</p>
          </div>

          {rec.estimated_water_requirement_litres != null && (
            <div style={{ marginBottom: 8 }}>
              <strong>Estimated Water Requirement:</strong>{' '}
              <span style={{ color: 'var(--blue-dark)', fontWeight: 700 }}>
                {rec.estimated_water_requirement_litres.toLocaleString()} litres
              </span>
              <span style={{ fontSize: 12, color: 'var(--neutral-500)' }}> (estimated, over 3 days)</span>
            </div>
          )}

          {rec.calculation_inputs?.calc && (
            <details style={{ marginBottom: 8 }}>
              <summary style={{ cursor: 'pointer', fontSize: 13, color: 'var(--blue)' }}>📐 Show calculation details</summary>
              <div style={{ background: 'var(--neutral-100)', borderRadius: 6, padding: 12, marginTop: 6, fontSize: 12, fontFamily: 'monospace' }}>
                {Object.entries(rec.calculation_inputs.calc).map(([k, v]) => (
                  <div key={k}><strong>{k}:</strong> {JSON.stringify(v)}</div>
                ))}
              </div>
            </details>
          )}

          {rec.uncertainty && (
            <div className="alert alert-info" style={{ fontSize: 13, marginBottom: 8 }}>
              ℹ️ <strong>Uncertainty:</strong> {rec.uncertainty}
            </div>
          )}
          {rec.missing_information && (
            <div className="alert alert-warning" style={{ fontSize: 13, marginBottom: 8 }}>
              ⚠️ <strong>Missing information:</strong> {rec.missing_information}
            </div>
          )}
          {rec.next_steps && (
            <div style={{ marginBottom: 8 }}>
              <strong>Next steps:</strong>
              <p style={{ fontSize: 14, marginTop: 4 }}>{rec.next_steps}</p>
            </div>
          )}

          {rec.evidence_sources?.length > 0 && (
            <div>
              <strong style={{ fontSize: 13 }}>📚 Evidence Sources:</strong>
              <ul style={{ marginTop: 4, paddingLeft: 18 }}>
                {rec.evidence_sources.map((s, i) => (
                  <li key={i} style={{ fontSize: 12, marginBottom: 2 }}>
                    <a href={s.url || '#'} target="_blank" rel="noreferrer">{s.title}</a>
                    {s.publisher && <span style={{ color: 'var(--neutral-500)' }}> — {s.publisher}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p style={{ fontSize: 11, color: 'var(--neutral-500)', marginTop: 10 }}>
            Generated: {new Date(rec.created_at).toLocaleString()} · All values are estimates. Verify locally.
          </p>
        </div>
      )}
    </div>
  )
}

const ws = { textAlign: 'center', padding: '10px 4px' }
const wv = { fontWeight: 700, fontSize: 22, color: 'var(--blue-dark)' }
const wl = { fontSize: 12, color: 'var(--neutral-500)' }
