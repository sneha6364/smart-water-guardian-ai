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
7. [Running the Application](#running-the-application)
8. [Running Tests](#running-tests)
9. [Demo Mode](#demo-mode)
10. [Hackathon Presentation Script](#hackathon-presentation-script)
11. [API Reference](#api-reference)
12. [Knowledge Base](#knowledge-base)
13. [Important Disclaimers](#important-disclaimers)

---

## Project Overview

Small farmers in India often lack access to real-time irrigation guidance. They face unpredictable rainfall, limited stored water, different crop water needs at each growth stage, and inefficient irrigation methods that waste water.

**Smart Water Guardian** provides:
- **Water Budget Guardian** — estimates days of water remaining, triggers shortage warnings
- **Rain-Aware Planner** — uses 7-day weather forecast to advise on irrigation timing
- **What-If Simulator** — compare "irrigate now" vs "wait for rain" vs "conserve water"
- **Explainable AI** — every recommendation includes the calculation, assumptions, and evidence
- **FAO-56 Science** — all calculations use published crop coefficients (ETc = ET₀ × Kc)

---

## Architecture

```
React Frontend (Vite · port 5173)
        │
        ▼  HTTP / JSON  (proxy → port 8000)
FastAPI Backend (Python)
 ├── Irrigation Calculation Engine  (FAO-56 ETc = ET₀ × Kc, deterministic)
 ├── Weather Service                → Open-Meteo API (free, no key)
 ├── Groq AI Service                → Groq Cloud (llama3-8b-8192)
 ├── RAG Knowledge Base             → FAO-56, ICRISAT, IMD, ICAR passages
 └── SQLite Database                → Farmers, Farms, Crops, Water, History
```

**Security:** The Groq API key is **never** sent to the browser. All AI calls are made server-side only.

---

## Features

| Feature | Description |
|---|---|
| Farmer & Farm Registration | 3-step wizard, validates inputs, supports unknown values |
| Weather Forecast | 7-day Open-Meteo forecast — rain, probability, ET₀, temperature |
| Irrigation Recommendation | ETc = ET₀ × Kc · FAO-56 crop coefficients · Groq AI explanation |
| Water Budget Guardian | Estimates days of water remaining, shortage alerts |
| What-If Simulator | 4 scenarios: irrigate now / wait for rain / 50% budget / skip |
| Agricultural Knowledge | RAG search across FAO-56, ICRISAT, ICAR, IMD — with source links |
| History & Reports | Past recommendations, water storage records, trends |
| Demo Mode | Works without Groq API key — shows deterministic results only |

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
```

---

## Quick Start (Windows)

### 1. Clone / open the project
```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water"
```

### 2. Create Python virtual environment
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install backend dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### 4. Configure environment
```powershell
# Still in the backend directory
copy ..\\.env.example .env
notepad .env
```
Edit `.env`:
- Set `GROQ_API_KEY=your_actual_key` (get free key at https://console.groq.com)
- Optionally change `GROQ_MODEL` (default: `llama3-8b-8192`)
- Leave other values as-is for local development

> **Without a Groq key:** the app runs in **demo mode** — all calculations work, AI explanations show a placeholder.

### 5. Initialise database and seed demo data
```powershell
# From the backend directory, with .venv active
python seed_demo.py
```

### 6. Start the backend
Open a **new terminal** and run:
```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water\backend"
..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Or use the helper script from the project root:
```powershell
# From the "smart water" folder — right-click → Run with PowerShell
powershell -ExecutionPolicy Bypass -File start_backend.ps1
```
Verify: http://localhost:8000/health → `{"status":"ok","app_env":"demo"}`
API docs: http://localhost:8000/docs

### 7. Install and start the frontend (another new terminal)
```powershell
cd "C:\Users\jaggu\OneDrive\Desktop\smart water\frontend"
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install --legacy-peer-deps
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" run dev
```
Or use the helper script:
```powershell
powershell -ExecutionPolicy Bypass -File start_frontend.ps1
```
Open: **http://localhost:5173**

> **Node.js note:** If you have Node v24+, use `--legacy-peer-deps` on install. The app builds with Vite 5.4 which is compatible.

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(empty)* | Get at https://console.groq.com/keys |
| `GROQ_MODEL` | `llama3-8b-8192` | Supported: `llama3-8b-8192`, `llama3-70b-8192`, `mixtral-8x7b-32768`, `gemma2-9b-it` |
| `APP_ENV` | `demo` | `demo` / `development` / `production` |
| `DATABASE_URL` | `sqlite+aiosqlite:///./smart_water.db` | SQLite file path |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allowed origin |
| `WEATHER_API_BASE_URL` | `https://api.open-meteo.com/v1/forecast` | Open-Meteo endpoint |

---

## Running Tests

```powershell
# From the backend directory, with .venv active
pytest -v
```

Tests cover:
- Deterministic irrigation calculations (crop coefficients, ETc, volumes, unit conversions)
- Water budget calculations and shortage alerts
- API endpoints (farmers, farms, crops, water storage, recommendations, scenarios, knowledge)
- Missing input handling and fallback behaviour
- Scenario simulation outputs

---

## Demo Mode

The app works without a Groq API key. In demo mode:
- All calculations run normally using the deterministic engine
- Weather data is fetched from Open-Meteo (no API key needed)
- AI explanations show: `"[AI explanation unavailable — Groq not configured. Running in demo mode.]"`
- A visible banner indicates demo mode on each page

---

## Hackathon Presentation Script (3 minutes)

1. **Problem** (20s): "Small farmers lack water guidance. Wrong irrigation wastes water or stresses crops."
2. **Demo farm** (20s): Select "Ravi Kumar — Rice Farm" from the navigation bar → Dashboard
3. **Crop & weather** (30s): Show crop info, 7-day forecast, rain probability vs actual amount
4. **Generate recommendation** (30s): Click "Generate Recommendation" → show action, explanation, calculations
5. **Groq explanation** (20s): Expand calculation details → show ETc = ET₀ × Kc, assumptions, sources
6. **What-If** (30s): Open "What-If" → run simulation → compare 4 scenarios
7. **Shortage** (20s): Select "Lakshmi Devi" → Water Budget shows < 3 days remaining → alert fires
8. **Knowledge** (20s): Open Knowledge → search "rice water requirement" → show FAO-56 passage + AI summary
9. **Architecture** (30s): Show architecture diagram on Home page → explain security (no key in browser)

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
| GET | `/api/v1/weather/forecast` | Get weather (lat/lon) |
| POST | `/api/v1/recommendations/` | Generate recommendation |
| GET | `/api/v1/recommendations/farm/{id}` | Recommendation history |
| POST | `/api/v1/scenarios/` | Run what-if scenarios |
| POST | `/api/v1/knowledge/search` | Search knowledge base |
| GET | `/api/v1/dashboard/{farmer_id}` | Full dashboard summary |

Full interactive docs: http://localhost:8000/docs

---

## Knowledge Base

The built-in knowledge corpus contains passages from:
- **FAO Irrigation and Drainage Paper 56** (Allen et al. 1998) — crop coefficients, ETc
- **FAO Effective Rainfall** guidelines
- **FAO Drip Irrigation** water efficiency
- **ICRISAT** — semi-arid India crop water requirements
- **ICAR** — Indian farm pond and water management
- **India Meteorological Department** — forecast reliability guidance

To add documents: place PDF or `.txt` files in `data/knowledge/` and extend `backend/app/services/knowledge_rag.py` to ingest them.

---

## Important Disclaimers

- All irrigation volumes are **estimates** based on available data. Verify locally before applying.
- The system uses the FAO-56 single crop coefficient method (ETc = ET₀ × Kc). Local calibration improves accuracy.
- Weather forecasts are probabilistic. The system does not treat forecast rain as guaranteed.
- Water storage figures rely on manually recorded readings, not sensors.
- Do not claim guaranteed water savings without a validated baseline and recorded data.
- AI explanations are generated by Groq AI using verified inputs. They are explanations, not new calculations.
