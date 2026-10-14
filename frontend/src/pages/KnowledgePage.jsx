import React, { useState } from 'react'
import { searchKnowledge } from '../services/api'
import { Loading, SectionTitle, AIUnavailableBanner } from '../components/UI'

const DEMO_QUERIES = [
  'drip irrigation water efficiency',
  'crop water requirement rice wheat',
  'soil moisture when to irrigate',
  'effective rainfall calculation',
  'deficit irrigation yield',
]

export default function KnowledgePage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (q) => {
    const searchQuery = q || query
    if (!searchQuery.trim()) return
    setLoading(true); setError('')
    try {
      const r = await searchKnowledge(searchQuery, 5)
      setResults(r.data)
      setQuery(searchQuery)
    } catch (e) {
      setError(e.response?.data?.detail || 'Search failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <SectionTitle sub="Search FAO-56 crop science, irrigation guidance, and agricultural knowledge">
        📚 Agricultural Knowledge Base
      </SectionTitle>

      <div className="card" style={{ marginBottom: 20 }}>
        <p style={{ marginBottom: 12, fontSize: 14, color: 'var(--neutral-700)' }}>
          Search curated agricultural guidance from FAO-56, ICRISAT, ICAR, and India Meteorological Department.
          Sources are shown for every result so you can verify the information.
        </p>

        <div style={{ display: 'flex', gap: 8 }}>
          <input className="form-input" style={{ flex: 1 }}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="e.g. rice water requirement mid season…" />
          <button className="btn btn-primary" onClick={() => handleSearch()} disabled={loading || !query.trim()}>
            {loading ? '⏳' : '🔍 Search'}
          </button>
        </div>

        <div style={{ marginTop: 10 }}>
          <span style={{ fontSize: 12, color: 'var(--neutral-500)' }}>Try: </span>
          {DEMO_QUERIES.map(q => (
            <button key={q} className="tag" style={{ cursor: 'pointer', fontSize: 12 }}
              onClick={() => handleSearch(q)}>{q}</button>
          ))}
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <Loading text="Searching knowledge base…" />}

      {results && !loading && (
        <>
          {!results.ai_available && <AIUnavailableBanner />}

          {/* AI summary */}
          {results.ai_summary && (
            <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid var(--green)' }}>
              <h4 style={{ marginBottom: 8 }}>🤖 AI Summary</h4>
              <p style={{ fontSize: 14, lineHeight: 1.7 }}>{results.ai_summary}</p>
              <p style={{ fontSize: 12, color: 'var(--neutral-500)', marginTop: 6 }}>
                Answer grounded in retrieved passages below. Verify with the source documents.
              </p>
            </div>
          )}

          {/* Results */}
          <h3 style={{ marginBottom: 12 }}>📄 Retrieved Passages ({results.results.length})</h3>
          {results.results.length === 0 ? (
            <div className="alert alert-info">No relevant passages found for this query. Try different keywords.</div>
          ) : (
            results.results.map((r, i) => (
              <div key={i} className="card" style={{ marginBottom: 12, borderLeft: '4px solid var(--blue)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
                  <h4 style={{ fontSize: 14 }}>{r.title}</h4>
                  {r.relevance_score != null && (
                    <span className="badge badge-blue">relevance: {(r.relevance_score * 100).toFixed(0)}%</span>
                  )}
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--neutral-900)' }}>{r.passage}</p>
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  {r.publisher && <span style={{ fontSize: 12, color: 'var(--neutral-500)' }}>📖 {r.publisher}</span>}
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                      🔗 Source document
                    </a>
                  )}
                </div>
              </div>
            ))
          )}

          <div className="alert alert-warning" style={{ fontSize: 13, marginTop: 8 }}>
            ⚠️ Retrieved passages are from curated sources but should be verified for your local conditions.
            Retrieved facts do not override real measurements or deterministic calculations.
          </div>
        </>
      )}
    </div>
  )
}
