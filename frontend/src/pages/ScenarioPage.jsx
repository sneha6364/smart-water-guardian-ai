import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFarms, runScenarios } from '../services/api'
import { Loading, EmptyState, SectionTitle, AIUnavailableBanner } from '../components/UI'

const SCENARIO_COLORS = {
  'Irrigate Now': '#2d9d5c',
  'Wait for Forecast Rain': '#2176ae',
  '50% Water Budget (Conservation)': '#e07b1a',
  'Skip This Irrigation Cycle': '#c62828',
}

export default function ScenarioPage({ farmerId }) {
  const [farms, setFarms] = useState([])
  const [selectedFarm, setSelectedFarm] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!farmerId) return
    listFarms(farmerId).then(r => { setFarms(r.data); if (r.data.length) setSelectedFarm(r.data[0]) }).catch(() => {})
  }, [farmerId])

  const handleRun = async () => {
    if (!selectedFarm) return
    setLoading(true); setError('')
    try {
      const r = await runScenarios(selectedFarm.id)
      setResult(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to run scenarios')
    } finally { setLoading(false) }
  }

  if (!farmerId) return (
    <div className="container" style={{ padding: 40 }}>
      <EmptyState icon="👤" title="No farmer selected" />
      <div style={{ textAlign: 'center', marginTop: 16 }}><Link to="/register" className="btn btn-primary">Register</Link></div>
    </div>
  )

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub="Compare irrigation decisions and their impact on water storage">🔬 What-If Scenario Simulator</SectionTitle>

      {farms.length > 1 && (
        <div className="form-group" style={{ maxWidth: 300 }}>
          <label className="form-label">Farm</label>
          <select className="form-select" value={selectedFarm?.id || ''}
            onChange={e => setSelectedFarm(farms.find(f => f.id === parseInt(e.target.value)))}>
            {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
      )}

      <button className="btn btn-secondary" onClick={handleRun} disabled={loading || !selectedFarm}
        style={{ fontSize: 15, padding: '10px 24px', marginBottom: 20 }}>
        {loading ? '⏳ Running scenarios…' : '▶ Run What-If Simulation'}
      </button>

      {error && <div className="alert alert-danger">{error}</div>}

      {result && (
        <>
          {!result.ai_available && <AIUnavailableBanner />}

          {/* Comparison table */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 12 }}>📊 Scenario Comparison</h3>
            <div className="table-wrap">
              <table>
                <thead><tr>
                  <th>Scenario</th>
                  <th>Est. Water Use (L)</th>
                  <th>Remaining Storage (L)</th>
                  <th>Days Remaining</th>
                  <th>Recommendation</th>
                </tr></thead>
                <tbody>
                  {result.scenarios.map(s => (
                    <tr key={s.scenario_name}>
                      <td>
                        <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
                          background: SCENARIO_COLORS[s.scenario_name] || '#aaa', marginRight: 6 }} />
                        <strong>{s.scenario_name}</strong>
                      </td>
                      <td>{s.estimated_water_use_litres?.toLocaleString() ?? '—'}</td>
                      <td>{s.remaining_storage_litres?.toLocaleString() ?? '—'}</td>
                      <td style={{ color: (s.days_remaining ?? 99) < 3 ? 'var(--red)' : 'inherit' }}>
                        {s.days_remaining?.toFixed(1) ?? '—'}
                      </td>
                      <td style={{ fontSize: 13 }}>{s.recommendation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI comparison */}
          {result.ai_comparison && (
            <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid var(--blue)' }}>
              <h4 style={{ marginBottom: 8 }}>🤖 AI Comparison</h4>
              <p style={{ fontSize: 14, lineHeight: 1.7 }}>{result.ai_comparison}</p>
            </div>
          )}

          {/* Scenario detail cards */}
          <div className="grid-2">
            {result.scenarios.map(s => (
              <div key={s.scenario_name} className="card"
                style={{ borderTop: `4px solid ${SCENARIO_COLORS[s.scenario_name] || '#aaa'}` }}>
                <h4 style={{ marginBottom: 8 }}>{s.scenario_name}</h4>
                <p style={{ fontSize: 13, color: 'var(--neutral-700)', marginBottom: 8 }}>{s.description}</p>
                {s.assumptions?.length > 0 && (
                  <details>
                    <summary style={{ fontSize: 12, cursor: 'pointer', color: 'var(--blue)' }}>Assumptions ({s.assumptions.length})</summary>
                    <ul style={{ marginTop: 4, paddingLeft: 16 }}>
                      {s.assumptions.map((a, i) => <li key={i} style={{ fontSize: 12, marginBottom: 2 }}>{a}</li>)}
                    </ul>
                  </details>
                )}
                {s.limitations?.length > 0 && (
                  <details style={{ marginTop: 4 }}>
                    <summary style={{ fontSize: 12, cursor: 'pointer', color: 'var(--orange)' }}>Limitations ({s.limitations.length})</summary>
                    <ul style={{ marginTop: 4, paddingLeft: 16 }}>
                      {s.limitations.map((l, i) => <li key={i} style={{ fontSize: 12, marginBottom: 2 }}>{l}</li>)}
                    </ul>
                  </details>
                )}
              </div>
            ))}
          </div>

          <div className="alert alert-warning" style={{ marginTop: 16, fontSize: 13 }}>
            ⚠️ All scenario values are estimates based on deterministic calculations. Actual water use
            may vary depending on weather, soil conditions, and irrigation efficiency.
          </div>
        </>
      )}
    </div>
  )
}
