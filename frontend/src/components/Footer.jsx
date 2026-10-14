import React from 'react'

export default function Footer() {
  return (
    <footer style={styles.footer}>
      <div className="container" style={styles.inner}>
        <p style={styles.text}>
          💧 <strong>Smart Water Guardian</strong> — AI-powered irrigation for small farmers
        </p>
        <p style={styles.sub}>
          Built with Groq AI · Open-Meteo Weather · FAO-56 Agronomy · React + FastAPI
        </p>
        <p style={styles.disclaimer}>
          ⚠️ All irrigation estimates are indicative only. Always verify with local agronomic advice.
        </p>
      </div>
    </footer>
  )
}

const styles = {
  footer: { background: 'var(--neutral-900)', color: '#ccc', padding: '20px 0', marginTop: 40 },
  inner:  { textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 4 },
  text:   { color: '#fff', fontSize: 15 },
  sub:    { fontSize: 13, color: '#aaa' },
  disclaimer: { fontSize: 12, color: '#888', fontStyle: 'italic' },
}
