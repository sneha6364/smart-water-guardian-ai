/**
 * Central API service — all backend calls go through this module.
 * The Groq API key is NEVER sent from the frontend.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Farmers ────────────────────────────────────────────────────────────────
export const createFarmer   = (data)       => api.post('/farmers/', data)
export const listFarmers    = ()           => api.get('/farmers/')
export const getFarmer      = (id)         => api.get(`/farmers/${id}`)

// ── Farms ──────────────────────────────────────────────────────────────────
export const createFarm     = (data)       => api.post('/farms/', data)
export const listFarms      = (farmer_id)  => api.get('/farms/', { params: { farmer_id } })
export const getFarm        = (id)         => api.get(`/farms/${id}`)
export const updateFarm     = (id, data)   => api.patch(`/farms/${id}`, data)

// ── Crops ──────────────────────────────────────────────────────────────────
export const createCrop     = (data)       => api.post('/crops/', data)
export const listCrops      = (farm_id)    => api.get(`/crops/farm/${farm_id}`)

// ── Water storage ──────────────────────────────────────────────────────────
export const recordWater    = (data)       => api.post('/water/', data)
export const listWaterHistory = (farm_id)  => api.get(`/water/farm/${farm_id}`)

// ── Weather ────────────────────────────────────────────────────────────────
export const getWeather     = (lat, lon)   => api.get('/weather/forecast', { params: { latitude: lat, longitude: lon } })

// ── Recommendations ────────────────────────────────────────────────────────
export const generateRecommendation = (farm_id) => api.post('/recommendations/', { farm_id })
export const listRecommendations    = (farm_id) => api.get(`/recommendations/farm/${farm_id}`)

// ── Scenarios ──────────────────────────────────────────────────────────────
export const runScenarios   = (farm_id)    => api.post('/scenarios/', { farm_id })

// ── Knowledge ──────────────────────────────────────────────────────────────
export const searchKnowledge = (query, top_k = 5) =>
  api.post('/knowledge/search', { query, top_k })

// ── Dashboard ──────────────────────────────────────────────────────────────
export const getDashboard   = (farmer_id)  => api.get(`/dashboard/${farmer_id}`)

// ── Health ─────────────────────────────────────────────────────────────────
export const healthCheck    = ()           => axios.get('/health')

export default api
