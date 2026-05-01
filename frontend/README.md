# CurryCast Frontend

React + TypeScript + Vite dashboard for the CurryCast forecasting engine.
Talks to the FastAPI backend (`src/api/service.py`) over HTTP.

**Theme:** Sri Lankan luxe — gold (`#D4AF37`) on deep brown (`#3E2723`) and black (`#0a0805`).

## Quickstart

```bash
# 1. Start the FastAPI backend (from project root)
uvicorn src.api.service:app --reload --port 8000

# 2. In another terminal, start the React dev server
cd frontend
npm install
npm run dev          # http://localhost:5173
```

## Production build

```bash
npm run build        # outputs to dist/
npm run preview      # serves the built bundle locally
```

## Pages

- **`/`** — Overview / pitch
- **`/forecast`** — 7-day daily covers chart + interval band
- **`/prep`** — Tomorrow's prep cards in kg / portions, with EN / Sinhala / Tamil labels
- **`/weather`** — Weather strip + auto-balanced prep adjustments
- **`/backtest`** — Replay last N days, savings in LKR

## API endpoints used

- `GET  /health`
- `GET  /restaurant`
- `POST /predict          { days }`
- `POST /backtest         { holdout_days }`
- `GET  /weather`

By default the dev server proxies `/api/*` to `http://localhost:8000`. Override with the
`VITE_API_BASE` env var.
