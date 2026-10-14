# 💧 AI-Powered Smart Water Guardian

> Helping small farmers decide **when to irrigate**, **how much water to use**, and **whether to wait for rain** — combining weather forecasts, FAO-56 crop science, and Groq AI explanations.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Prerequisites](#prerequisites)
5. [Quick Start (Windows)](#quick-start-windows)
6. [Environment Configuration](#environment-configuration)
7. [Running Tests](#running-tests)
8. [Demo Mode](#demo-mode)
9. [Hackathon Presentation Script](#hackathon-presentation-script)
10. [API Reference](#api-reference)
11. [Knowledge Base](#knowledge-base)
12. [Important Disclaimers](#important-disclaimers)

---

## Project Overview

Small farmers in India often lack access to real-time irrigation guidance. They face unpredictable rainfall, limited stored water, different crop water needs at each growth stage, and inefficient irrigation methods that waste water.

**Smart Water Guardian** provides:

- **Water Budget Guardian** — estimates days of water remaining and triggers shortage warnings.
- **Rain-Aware Planner** — uses a 7-day weather forecast to advise on irrigation timing.
- **What-If Simulator** — compares "irrigate now" vs. "wait for rain" vs. "conserve water".
- **Explainable AI** — every recommendation includes calculations, assumptions, and evidence.
- **FAO-56 Science** — calculations use published crop coefficients (ETc = ET₀ × Kc).

---

## Architecture

```text
React Frontend (Vite · port 5173)
       │
       ▼ HTTP / JSON (proxy → port 8000)
FastAPI Backend (Python)
├── Irrigation Calculation Engine (FAO-56 ETc = ET₀ × Kc)
├── Weather Service → Open-Meteo API (free, no key)
├── Groq AI Service → Groq Cloud
├── RAG Knowledge Base → FAO-56, ICRISAT, IMD, ICAR passages
└── SQLite Database → Farmers, Farms, Crops, Water, History
```

**Security:** The Groq API key is never sent to the browser. All AI calls are made server-side.

---

## Features

| Feature | Description |
|---|---|
| Farmer & Farm Registration | 3-step wizard, validates inputs, supports unknown values |
| Weather Forecast | 7-day forecast — rain, probability, ET₀, temperature |
| Irrigation Recommendation | ETc = ET₀ × Kc, FAO-56 coefficients, AI explanation |
| Water Budget Guardian | Estimates days of water remaining and shortage alerts |
| What-If Simulator | Compares four irrigation scenarios |
| Agricultural Knowledge | Searches FAO-56, ICRISAT, ICAR and IMD resources |
| History & Reports | Past recommendations, water storage records and trends |
| Demo Mode | Works without a Groq API key using deterministic calculations |

---

## Prerequisites

- **Python 3.10+** — https://www.python.org/downloads/
- **Node.js 18+** — https://nodejs.org/
- **Git** — https://git-scm.com/

Verify installations:

```powershell
python --version
node --version
npm --version
git --version
```

---

## Quick Start (Windows)

### 1. Open the project

```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water"
```

### 2. Create a Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables

Return to the project root if necessary, then copy the example environment file:

```powershell
cd ..
Copy-Item .env.example .env
notepad .env
```

Set `GROQ_API_KEY` to your own API key from https://console.groq.com. Keep this key private and never upload `.env` to GitHub.

Without a Groq key, the application can run in demo mode if configured for it.

### 5. Initialise demo data

```powershell
cd backend
python seed_demo.py
```

### 6. Start the backend

Open a new PowerShell terminal:

```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water"
.\start_backend.ps1
```

Backend: http://localhost:8000

Health check: http://localhost:8000/health

API documentation: http://localhost:8000/docs

### 7. Start the frontend

Open another PowerShell terminal:

```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water"
cd frontend
npm run dev
```

Open the frontend at **http://localhost:5173**.

If dependencies are not installed, run `npm install` inside the `frontend` folder first.

---

## Environment Configuration

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your private Groq API key |
| `GROQ_MODEL` | AI model used by the backend |
| `APP_ENV` | Application environment, such as demo or development |
| `DATABASE_URL` | Database connection string |
| `FRONTEND_ORIGIN` | Frontend origin allowed by CORS |
| `WEATHER_API_BASE_URL` | Open-Meteo weather API endpoint |

Use the values specified in `.env.example` as the starting point.

---

## Running Tests

From the project root:

```powershell
cd backend
pytest -v
```

Tests may cover irrigation calculations, water budgets, API endpoints, missing inputs, and scenario simulations, depending on the tests included in the project.

---

## Demo Mode

In demo mode:

- Irrigation calculations use the deterministic calculation engine.
- Weather data can be fetched from Open-Meteo without an API key.
- AI explanations may display a fallback message if Groq is not configured.
- The application should indicate when demo mode is active.

---

## Hackathon Presentation Script (3 minutes)

1. **Problem:** Explain how poor irrigation decisions waste water or stress crops.
2. **Demo farm:** Select a demo farmer and open the dashboard.
3. **Crop and weather:** Show crop information and the weather forecast.
4. **Recommendation:** Generate an irrigation recommendation and explain the calculations.
5. **AI explanation:** Show ETc = ET₀ × Kc, assumptions, and sources.
6. **What-If simulation:** Compare irrigation scenarios.
7. **Water shortage:** Demonstrate the water budget and shortage warnings.
8. **Knowledge base:** Search for crop water requirements and show relevant sources.
9. **Architecture:** Explain how the frontend, backend, weather service, database, and AI service work together.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/farmers/` | Create farmer |
| GET | `/api/v1/farmers/` | List farmers |
| POST | `/api/v1/farms/` | Create farm |
| GET | `/api/v1/farms/` | List farms |
| POST | `/api/v1/crops/` | Register crop |
| POST | `/api/v1/water/` | Record water storage |
| GET | `/api/v1/weather/forecast` | Get weather forecast |
| POST | `/api/v1/recommendations/` | Generate recommendation |
| GET | `/api/v1/recommendations/farm/{id}` | Recommendation history |
| POST | `/api/v1/scenarios/` | Run what-if scenarios |
| POST | `/api/v1/knowledge/search` | Search knowledge base |
| GET | `/api/v1/dashboard/{farmer_id}` | Dashboard summary |

For interactive API documentation, open http://localhost:8000/docs while the backend is running.

---

## Knowledge Base

The knowledge corpus is intended to include agricultural guidance from:

- **FAO Irrigation and Drainage Paper 56** — crop coefficients and crop evapotranspiration.
- **FAO effective rainfall guidelines** — estimating usable rainfall.
- **FAO drip irrigation guidance** — water-use efficiency.
- **ICRISAT** — crop water management in semi-arid regions.
- **ICAR** — Indian agricultural water management.
- **India Meteorological Department (IMD)** — weather forecast guidance.

To add documents, follow the project's existing knowledge-base implementation and supported file formats.

---

## Important Disclaimers

- Irrigation volumes are estimates based on the available data. Verify recommendations locally before applying them.
- The system uses the FAO-56 single crop coefficient method (ETc = ET₀ × Kc). Local calibration can improve accuracy.
- Weather forecasts are probabilistic; forecast rain is not guaranteed.
- Water storage figures rely on recorded readings unless sensors are integrated.
- Do not claim guaranteed water savings without validated baseline data.
- AI explanations describe the available calculations and inputs; they should not replace expert agricultural advice.