import React from 'react'
import { Link } from 'react-router-dom'

const features = [
  { icon: '💧', title: 'Water Budget Guardian', desc: 'Know exactly how many days your stored water will last. Get warnings before you run out.' },
  { icon: '🌧️', title: 'Rain-Aware Planner', desc: 'Checks the 7-day weather forecast before recommending irrigation. Never waste water when rain is coming.' },
  { icon: '🤖', title: 'Groq AI Explanations', desc: 'Every recommendation comes with a plain-language explanation powered by Groq AI — not just numbers.' },
  { icon: '🔬', title: 'What-If Scenarios', desc: 'Compare "irrigate now" vs "wait for rain" vs "conserve water" — see the impact of each choice.' },
  { icon: '📚', title: 'FAO-56 Science', desc: 'Calculations use FAO-56 crop coefficients and proven irrigation science — not guesswork.' },
  { icon: '📱', title: 'Mobile-Friendly', desc: 'Works on any smartphone. Simple language. Designed for small farmers in India.' },
]

const steps = [
  { n: '1', title: 'Register your farm', desc: 'Enter location, crop, soil type, irrigation method, and available water storage.' },
  { n: '2', title: 'Fetch weather & calculate', desc: 'Open-Meteo provides the 7-day forecast. The engine calculates crop water demand using ETc = ET₀ × Kc.' },
  { n: '3', title: 'Get your recommendation', desc: 'Groq AI explains the recommendation in simple language with all assumptions stated.' },
  { n: '4', title: 'Run what-if scenarios', desc: 'Compare alternatives and make an informed decision for your farm.' },
]

const stack = ['React + Vite', 'FastAPI (Python)', 'SQLite', 'Groq API (llama3)', 'Open-Meteo', 'FAO-56 Agronomy']

export default function HomePage({ onSelectFarmer }) {
  return (
    <div>
      {/* Hero */}
      <div style={styles.hero}>
        <div className="container" style={styles.heroInner}>
          <div style={styles.heroBadge}>🌱 Hackathon Project</div>
          <h1 style={styles.heroTitle}>AI-Powered Smart Water Guardian</h1>
          <p style={styles.heroSub}>for Small Farmers</p>
          <p style={styles.heroDesc}>
            Helping farmers decide <em>when to irrigate</em>, <em>how much water to use</em>,
            and <em>whether to wait for rain</em> — combining weather forecasts, crop science,
            and Groq AI explanations.
          </p>
          <div style={styles.heroBtns}>
            <Link to="/register" className="btn btn-primary" style={{ fontSize: 16, padding: '12px 28px' }}>
              🚀 Get Started
            </Link>
            <Link to="/dashboard" className="btn btn-outline" style={{ fontSize: 16, padding: '12px 28px', borderColor: '#fff', color: '#fff' }}>
              View Demo Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="container" style={{ padding: '32px 16px' }}>

        {/* Problem statement */}
        <div className="card alert-warning" style={{ borderLeft: '4px solid var(--orange)', marginBottom: 32 }}>
          <h3 style={{ marginBottom: 8, color: 'var(--neutral-900)' }}>🌾 The Problem</h3>
          <p style={{ fontSize: 15, lineHeight: 1.7 }}>
            Small farmers in India often lack access to real-time irrigation guidance. They face
            <strong> unpredictable rainfall</strong>, <strong>limited stored water</strong>,
            different crop water needs at each growth stage, and inefficient irrigation methods
            that waste water. A wrong decision — irrigating when rain is coming, or not irrigating
            when the crop is stressed — can cost yield and income.
          </p>
        </div>

        {/* Features grid */}
        <h2 className="section-title">Key Features</h2>
        <div className="grid-3" style={{ marginBottom: 32 }}>
          {features.map(f => (
            <div key={f.title} className="card" style={{ borderTop: '3px solid var(--green)' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>{f.icon}</div>
              <h4 style={{ marginBottom: 6 }}>{f.title}</h4>
              <p style={{ fontSize: 14, color: 'var(--neutral-700)' }}>{f.desc}</p>
            </div>
          ))}
        </div>

        {/* How it works */}
        <h2 className="section-title">How It Works</h2>
        <div className="grid-4" style={{ marginBottom: 32 }}>
          {steps.map(s => (
            <div key={s.n} className="card" style={{ textAlign: 'center' }}>
              <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--green)', color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 18,
                margin: '0 auto 12px' }}>{s.n}</div>
              <h4 style={{ marginBottom: 6 }}>{s.title}</h4>
              <p style={{ fontSize: 13, color: 'var(--neutral-700)' }}>{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Architecture */}
        <h2 className="section-title">System Architecture</h2>
        <div className="card" style={{ marginBottom: 32 }}>
          <div style={{ overflowX: 'auto', textAlign: 'center', fontFamily: 'monospace', fontSize: 14, lineHeight: 2 }}>
            <pre style={{ display: 'inline-block', textAlign: 'left', color: 'var(--neutral-700)' }}>{`
  React Frontend (Vite)
        │
        ▼  HTTP / JSON
  FastAPI Backend (Python)
   ├── Irrigation Calculation Engine (FAO-56 ETc = ET₀ × Kc)
   ├── Weather Service    → Open-Meteo API
   ├── Groq AI Service    → Groq Cloud (llama3-8b-8192)
   ├── RAG Knowledge Base → FAO-56, ICRISAT, IMD sources
   └── SQLite Database    → Farmers, Farms, Crops, Water, History
`}</pre>
          </div>
          <p style={{ fontSize: 13, color: 'var(--neutral-500)', marginTop: 8, textAlign: 'center' }}>
            All AI calls are made from the backend only. The Groq API key is never exposed to the browser.
          </p>
        </div>

        {/* Technology stack */}
        <h2 className="section-title">Technology Stack</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 32 }}>
          {stack.map(t => (
            <span key={t} className="badge badge-green" style={{ fontSize: 13, padding: '5px 14px' }}>{t}</span>
          ))}
        </div>

        {/* CTA */}
        <div className="card" style={{ textAlign: 'center', background: 'var(--green-light)', border: '1px solid var(--green)' }}>
          <h3 style={{ marginBottom: 8 }}>Ready to try it?</h3>
          <p style={{ marginBottom: 16, color: 'var(--neutral-700)' }}>
            Register your farm and get your first irrigation recommendation in under 2 minutes.
          </p>
          <Link to="/register" className="btn btn-primary" style={{ fontSize: 15, padding: '10px 24px' }}>
            Register Your Farm →
          </Link>
        </div>
      </div>
    </div>
  )
}

const styles = {
  hero: { background: 'linear-gradient(135deg, var(--green-dark) 0%, var(--blue-dark) 100%)', color: '#fff', padding: '60px 0 50px' },
  heroInner: { textAlign: 'center' },
  heroBadge: { display: 'inline-block', background: 'rgba(255,255,255,0.2)', borderRadius: 20, padding: '4px 16px', fontSize: 13, marginBottom: 12 },
  heroTitle: { fontSize: 'clamp(26px, 5vw, 46px)', fontWeight: 900, margin: '8px 0 4px' },
  heroSub: { fontSize: 20, fontWeight: 400, opacity: 0.85, marginBottom: 16 },
  heroDesc: { maxWidth: 600, margin: '0 auto 28px', fontSize: 16, lineHeight: 1.7, opacity: 0.92 },
  heroBtns: { display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' },
}
