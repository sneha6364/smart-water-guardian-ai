import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFarms, listRecommendations, listWaterHistory } from '../services/api'
import { Loading, EmptyState, SectionTitle } from '../components/UI'

export default function HistoryPage({ farmerId }) {
  const [farms, setFarms] = useState([])
  const [selectedFarm, setSelectedFarm] = useState(null)
  const [recs, setRecs] = useState([])
  const [waterHistory, setWaterHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('recommendations')

  useEffect(() => {
    if (!farmerId) return
    listFarms(farmerId).then(r => { setFarms(r.data); if (r.data.length) setSelectedFarm(r.data[0]) }).catch(() => {})
  }, [farmerId])

  useEffect(() => {
    if (!selectedFarm) return
    setLoading(true)
    Promise.all([
      listRecommendations(selectedFarm.id),
      listWaterHistory(selectedFarm.id),
    ]).then(([r1, r2]) => { setRecs(r1.data); setWaterHistory(r2.data) })
    .catch(() => {}).finally(() => setLoading(false))
  }, [selectedFarm])

  if (!farmerId) return (
    <div className="container" style={{ padding: 40 }}>
      <EmptyState icon="👤" title="No farmer selected" />
      <div style={{ textAlign: 'center', marginTop: 16 }}><Link to="/register" className="btn btn-primary">Register</Link></div>
    </div>
  )

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub="Previous recommendations, water records, and trends">📅 History & Reports</SectionTitle>

      {farms.length > 1 && (
        <div className="form-group" style={{ maxWidth: 300, marginBottom: 16 }}>
          <label className="form-label">Farm</label>
          <select className="form-select" value={selectedFarm?.id || ''}
            onChange={e => setSelectedFarm(farms.find(f => f.id === parseInt(e.target.value)))}>
            {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid var(--neutral-300)' }}>
        {['recommendations', 'water'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ padding: '8px 20px', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 14,
              background: 'none', borderBottom: tab === t ? '3px solid var(--green)' : '3px solid transparent',
              color: tab === t ? 'var(--green-dark)' : 'var(--neutral-500)', marginBottom: -2 }}>
            {t === 'recommendations' ? '🤖 Recommendations' : '💧 Water Storage'}
          </button>
        ))}
      </div>

      {loading ? <Loading /> : (
        <>
          {tab === 'recommendations' && (
            recs.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>Date</th><th>Action</th><th>Est. Volume (L)</th><th>AI</th>
                  </tr></thead>
                  <tbody>
                    {recs.map(r => (
                      <tr key={r.created_at}>
                        <td>{new Date(r.created_at).toLocaleString()}</td>
                        <td>
                          <details>
                            <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
                              {r.recommended_action}
                            </summary>
                            <div style={{ padding: '6px 0', fontSize: 12, color: 'var(--neutral-700)' }}>
                              <p>{r.reason}</p>
                              {r.uncertainty && <p><em>Uncertainty: {r.uncertainty}</em></p>}
                            </div>
                          </details>
                        </td>
                        <td>{r.estimated_water_requirement_litres?.toLocaleString() ?? '—'}</td>
                        <td><span className={`badge ${r.ai_available ? 'badge-green' : 'badge-gray'}`}>{r.ai_available ? 'AI' : 'Calc'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState icon="📋" title="No recommendations yet" message="Generate a recommendation from the Planner." />
          )}

          {tab === 'water' && (
            waterHistory.length > 0 ? (
              <>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Date</th><th>Storage (L)</th><th>Source</th><th>Notes</th></tr></thead>
                    <tbody>
                      {waterHistory.map(h => (
                        <tr key={h.id}>
                          <td>{new Date(h.recorded_at).toLocaleString()}</td>
                          <td>{h.storage_litres.toLocaleString()}</td>
                          <td>{h.source ?? '—'}</td>
                          <td>{h.notes ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p style={{ fontSize: 12, color: 'var(--neutral-500)', marginTop: 8 }}>
                  Showing last 50 records. {waterHistory.length} total.
                </p>
              </>
            ) : <EmptyState icon="💧" title="No water storage records" message="Record water storage from the Water Budget page." />
          )}
        </>
      )}
    </div>
  )
}
