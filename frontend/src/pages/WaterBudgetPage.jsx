import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFarms, listWaterHistory, recordWater } from '../services/api'
import { Loading, EmptyState, StatCard, SectionTitle } from '../components/UI'

export default function WaterBudgetPage({ farmerId }) {
  const [farms, setFarms] = useState([])
  const [selectedFarm, setSelectedFarm] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ storage_litres: '', source: '', notes: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (!farmerId) return
    listFarms(farmerId).then(r => {
      setFarms(r.data)
      if (r.data.length) setSelectedFarm(r.data[0])
    }).catch(() => {})
  }, [farmerId])

  useEffect(() => {
    if (!selectedFarm) return
    setLoading(true)
    listWaterHistory(selectedFarm.id)
      .then(r => setHistory(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [selectedFarm])

  const handleRecord = async (e) => {
    e.preventDefault()
    if (!form.storage_litres) { setError('Enter water volume'); return }
    setSaving(true); setError(''); setSuccess('')
    try {
      await recordWater({ farm_id: selectedFarm.id, storage_litres: parseFloat(form.storage_litres),
        source: form.source || null, notes: form.notes || null })
      setSuccess('Water storage recorded successfully.')
      setForm({ storage_litres: '', source: '', notes: '' })
      const r = await listWaterHistory(selectedFarm.id)
      setHistory(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to record')
    } finally { setSaving(false) }
  }

  // Budget estimate
  const latest = history[0]
  const avgDailyUse = history.length > 1
    ? Math.abs((history[history.length - 1].storage_litres - history[0].storage_litres) /
      Math.max(1, history.length - 1))
    : null

  const daysRemaining = latest && avgDailyUse ? latest.storage_litres / avgDailyUse : null
  const alert = daysRemaining != null && daysRemaining < 3

  if (!farmerId) return (
    <div className="container" style={{ padding: 40 }}>
      <EmptyState icon="👤" title="No farmer selected" message="Select or register a farmer first." />
      <div style={{ textAlign: 'center', marginTop: 16 }}><Link to="/register" className="btn btn-primary">Register</Link></div>
    </div>
  )

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub="Track stored water and estimate days remaining">💧 Water Budget Guardian</SectionTitle>

      <div className="alert alert-info" style={{ marginBottom: 20, fontSize: 13 }}>
        ℹ️ Water demand is estimated from recorded storage changes. These are estimates — not sensor measurements.
      </div>

      {/* Farm selector */}
      {farms.length > 1 && (
        <div className="form-group" style={{ maxWidth: 300 }}>
          <label className="form-label">Farm</label>
          <select className="form-select" value={selectedFarm?.id || ''}
            onChange={e => setSelectedFarm(farms.find(f => f.id === parseInt(e.target.value)))}>
            {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
      )}

      {/* Stats */}
      {latest && (
        <div className="grid-4" style={{ marginBottom: 24 }}>
          <StatCard icon="💧" value={`${(latest.storage_litres / 1000).toFixed(1)} kL`}
            label="Current Storage" sub={new Date(latest.recorded_at).toLocaleDateString()} />
          <StatCard icon="📉" value={avgDailyUse ? `${avgDailyUse.toFixed(0)} L` : '—'}
            label="Est. Daily Use" sub="from storage history" />
          <StatCard icon="⏳" value={daysRemaining ? `${daysRemaining.toFixed(1)} days` : '—'}
            label="Days Remaining" alert={alert} />
          <StatCard icon="🚰" value={history.length}
            label="Records" sub="storage readings" />
        </div>
      )}

      {alert && (
        <div className="alert alert-danger" style={{ marginBottom: 16 }}>
          🚨 <strong>Critical Water Alert!</strong> Estimated {daysRemaining?.toFixed(1)} days of water remaining at current usage.
          Consider reducing irrigation, seeking alternative water sources, or applying deficit irrigation.
        </div>
      )}

      {/* Record new reading */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 12 }}>📝 Record Water Storage</h3>
        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <form onSubmit={handleRecord}>
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label">Current Storage (litres) *</label>
              <input className="form-input" type="number" min="0" value={form.storage_litres}
                onChange={e => setForm(p => ({ ...p, storage_litres: e.target.value }))} placeholder="e.g. 35000" />
            </div>
            <div className="form-group">
              <label className="form-label">Source</label>
              <input className="form-input" value={form.source}
                onChange={e => setForm(p => ({ ...p, source: e.target.value }))} placeholder="well / pond / tank" />
            </div>
            <div className="form-group">
              <label className="form-label">Notes</label>
              <input className="form-input" value={form.notes}
                onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? '⏳ Saving…' : '💾 Record Storage'}
          </button>
        </form>
      </div>

      {/* History */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>📊 Storage History</h3>
        {loading ? <Loading /> : history.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Storage (L)</th><th>Source</th><th>Notes</th></tr></thead>
              <tbody>
                {history.map(h => (
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
        ) : <EmptyState icon="📋" title="No storage records" message="Record your current water storage above." />}
      </div>
    </div>
  )
}
