import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createFarmer, createFarm, createCrop } from '../services/api'
import { Loading } from '../components/UI'

const CROP_TYPES = ['rice','wheat','maize','sorghum','cotton','sunflower','sugarcane','potato','tomato','onion','groundnut','soybean','chickpea','banana','other']
const GROWTH_STAGES = ['initial','development','mid','late']
const SOIL_TYPES = ['sandy','loam','clay','sandy loam','clay loam','silt loam','unknown']
const IRR_METHODS = ['drip','sprinkler','flood','furrow','unknown']

function Field({ label, hint, error, children }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      {children}
      {hint && <div className="form-hint">{hint}</div>}
      {error && <div className="form-error">{error}</div>}
    </div>
  )
}

export default function RegisterPage({ onSelectFarmer }) {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1=farmer, 2=farm, 3=crop
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [farmerId, setFarmerId] = useState(null)
  const [farmId, setFarmId] = useState(null)

  const [farmer, setFarmer] = useState({ name: '', phone: '', location_name: '' })
  const [farm, setFarm] = useState({
    name: '', latitude: '', longitude: '', area_hectares: '',
    soil_type: '', irrigation_method: '', water_storage_litres: '',
  })
  const [crop, setCrop] = useState({
    crop_type: '', growth_stage: '', soil_moisture_pct: '', notes: '',
  })

  const handleFarmerSubmit = async (e) => {
    e.preventDefault()
    if (!farmer.name.trim()) { setError('Farmer name is required'); return }
    setSubmitting(true); setError('')
    try {
      const res = await createFarmer({ name: farmer.name, phone: farmer.phone || null, location_name: farmer.location_name || null })
      setFarmerId(res.data.id)
      onSelectFarmer(res.data.id)
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally { setSubmitting(false) }
  }

  const handleFarmSubmit = async (e) => {
    e.preventDefault()
    if (!farm.name.trim()) { setError('Farm name is required'); return }
    setSubmitting(true); setError('')
    try {
      const payload = {
        farmer_id: farmerId,
        name: farm.name,
        latitude: farm.latitude ? parseFloat(farm.latitude) : null,
        longitude: farm.longitude ? parseFloat(farm.longitude) : null,
        area_hectares: farm.area_hectares ? parseFloat(farm.area_hectares) : null,
        soil_type: farm.soil_type || null,
        irrigation_method: farm.irrigation_method || null,
        water_storage_litres: farm.water_storage_litres ? parseFloat(farm.water_storage_litres) : null,
      }
      const res = await createFarm(payload)
      setFarmId(res.data.id)
      setStep(3)
    } catch (err) {
      setError(err.response?.data?.detail || 'Farm registration failed')
    } finally { setSubmitting(false) }
  }

  const handleCropSubmit = async (e) => {
    e.preventDefault()
    if (!crop.crop_type) { setError('Please select a crop type'); return }
    setSubmitting(true); setError('')
    try {
      await createCrop({
        farm_id: farmId,
        crop_type: crop.crop_type,
        growth_stage: crop.growth_stage || null,
        soil_moisture_pct: crop.soil_moisture_pct ? parseFloat(crop.soil_moisture_pct) : null,
        notes: crop.notes || null,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Crop registration failed')
    } finally { setSubmitting(false) }
  }

  const steps = ['1. Farmer Info', '2. Farm Details', '3. Crop Info']

  return (
    <div className="container" style={{ maxWidth: 680, padding: '32px 16px' }}>
      <h1 style={{ marginBottom: 8 }}>Register Farmer & Farm</h1>
      <p style={{ color: 'var(--neutral-500)', marginBottom: 24 }}>
        Fill in what you know. You can update details later. Missing information will be noted in the recommendation.
      </p>

      {/* Step indicator */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 28 }}>
        {steps.map((s, i) => (
          <div key={i} style={{
            flex: 1, textAlign: 'center', padding: '8px 4px', fontSize: 13, fontWeight: 600,
            borderBottom: `3px solid ${step === i + 1 ? 'var(--green)' : 'var(--neutral-300)'}`,
            color: step === i + 1 ? 'var(--green-dark)' : 'var(--neutral-500)',
          }}>{s}</div>
        ))}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {submitting && <Loading text="Saving…" />}

      {/* Step 1 */}
      {step === 1 && (
        <form onSubmit={handleFarmerSubmit} className="card">
          <h3 style={{ marginBottom: 16 }}>Farmer Information</h3>
          <Field label="Farmer Name *">
            <input className="form-input" value={farmer.name}
              onChange={e => setFarmer(p => ({ ...p, name: e.target.value }))} />
          </Field>
          <Field label="Phone Number" hint="Optional">
            <input className="form-input" value={farmer.phone}
              onChange={e => setFarmer(p => ({ ...p, phone: e.target.value }))} />
          </Field>
          <Field label="Location / Village" hint="e.g. Bangalore Rural, Karnataka">
            <input className="form-input" value={farmer.location_name}
              onChange={e => setFarmer(p => ({ ...p, location_name: e.target.value }))} />
          </Field>
          <button type="submit" className="btn btn-primary" disabled={submitting}>Continue →</button>
        </form>
      )}

      {/* Step 2 */}
      {step === 2 && (
        <form onSubmit={handleFarmSubmit} className="card">
          <h3 style={{ marginBottom: 16 }}>Farm Details</h3>
          <Field label="Farm Name *">
            <input className="form-input" value={farm.name}
              onChange={e => setFarm(p => ({ ...p, name: e.target.value }))} />
          </Field>
          <div className="grid-2">
            <Field label="Latitude" hint="e.g. 13.08 (for weather forecast)">
              <input className="form-input" type="number" step="any" value={farm.latitude}
                onChange={e => setFarm(p => ({ ...p, latitude: e.target.value }))} />
            </Field>
            <Field label="Longitude" hint="e.g. 77.59">
              <input className="form-input" type="number" step="any" value={farm.longitude}
                onChange={e => setFarm(p => ({ ...p, longitude: e.target.value }))} />
            </Field>
          </div>
          <Field label="Farm Area (hectares)" hint="1 hectare = 10,000 m². Enter 0.5 for half a hectare.">
            <input className="form-input" type="number" step="any" min="0" value={farm.area_hectares}
              onChange={e => setFarm(p => ({ ...p, area_hectares: e.target.value }))} />
          </Field>
          <div className="grid-2">
            <Field label="Soil Type">
              <select className="form-select" value={farm.soil_type}
                onChange={e => setFarm(p => ({ ...p, soil_type: e.target.value }))}>
                <option value="">Select…</option>
                {SOIL_TYPES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Irrigation Method">
              <select className="form-select" value={farm.irrigation_method}
                onChange={e => setFarm(p => ({ ...p, irrigation_method: e.target.value }))}>
                <option value="">Select…</option>
                {IRR_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Available Water Storage (litres)" hint="Current water in your tank, well, or pond. Enter 0 if unknown.">
            <input className="form-input" type="number" min="0" value={farm.water_storage_litres}
              onChange={e => setFarm(p => ({ ...p, water_storage_litres: e.target.value }))} />
          </Field>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn btn-outline" onClick={() => setStep(1)}>← Back</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>Continue →</button>
          </div>
        </form>
      )}

      {/* Step 3 */}
      {step === 3 && (
        <form onSubmit={handleCropSubmit} className="card">
          <h3 style={{ marginBottom: 16 }}>Crop Information</h3>
          <Field label="Crop Type *">
            <select className="form-select" value={crop.crop_type}
              onChange={e => setCrop(p => ({ ...p, crop_type: e.target.value }))}>
              <option value="">Select…</option>
              {CROP_TYPES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Growth Stage" hint="initial = just planted, mid = flowering, late = near harvest">
            <select className="form-select" value={crop.growth_stage}
              onChange={e => setCrop(p => ({ ...p, growth_stage: e.target.value }))}>
              <option value="">Unknown / Not sure</option>
              {GROWTH_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Current Soil Moisture (%)" hint="Optional. Skip if you don't have a sensor.">
            <input className="form-input" type="number" min="0" max="100" value={crop.soil_moisture_pct}
              onChange={e => setCrop(p => ({ ...p, soil_moisture_pct: e.target.value }))} />
          </Field>
          <Field label="Notes" hint="Any additional information about the crop or field.">
            <textarea className="form-textarea" rows={3} value={crop.notes}
              onChange={e => setCrop(p => ({ ...p, notes: e.target.value }))} />
          </Field>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn btn-outline" onClick={() => setStep(2)}>← Back</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>✅ Complete Registration</button>
          </div>
        </form>
      )}
    </div>
  )
}
