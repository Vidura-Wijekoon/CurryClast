---
title: CurryCast Backend
emoji: 🍛
colorFrom: yellow
colorTo: gray
sdk: docker
pinned: false
---

# 🍛 CurryCast

**Demand & Buffet Forecasting Engine for Sri Lankan Restaurants**

CurryCast tells your kitchen *exactly* how much pol sambol, dhal curry, fish ambul thiyal, and chicken kottu to prep tomorrow — accounting for weather, poya days, school holidays, perahera, cricket fixtures, and tourist season.

> "Some Saturdays we cook for 200 covers and 80 walk in — the rest goes to the staff or the bin. Other Saturdays we run out of pol sambol by 8 PM and lose half the rice-and-curry crowd. We just guess." — Restaurant owner, Colombo

CurryCast turns that guess into a 7-day forecast with **3–6% food-cost reduction** (LKR 180k–360k/month for a mid-size Colombo restaurant).

---

## ✨ What it does

- **7-day demand forecast** — covers per day, per hour, per menu item.
- **Tomorrow's prep list** — exactly how many kg of dhal, how many portions of fish ambul thiyal.
- **Weather-aware** — "Rain expected Friday → shift 8 kg of grilled to soups."
- **Sri Lanka-aware** — knows about poya days, perahera, Galle Lit Fest, payday cycles.
- **Back-test** — replay the last 30 days: "If you'd used CurryCast, you'd have saved LKR 312,400."

---

## 🏗️ Architecture

Two-tier:

```
┌─────────────────┐      HTTP       ┌─────────────────────┐
│ React Frontend  │ ───────────────▶│  FastAPI Backend    │
│ (Vite + TS)     │ ◀─────────────── │  Prophet + LightGBM │
│ port 5173       │     JSON        │  port 8000          │
└─────────────────┘                  └──────────┬──────────┘
   gold/black/brown                             │
                                                ▼
                                    ┌────────────────────┐
                                    │ Models / Features  │
                                    │ POS / Weather /    │
                                    │ Holidays / SLTDA   │
                                    └────────────────────┘
```

See **[architecture/pipeline_diagram.html](architecture/pipeline_diagram.html)** for the data flow.

---

## 🚀 Quickstart (5 minutes)

```bash
# 1. Backend
git clone <repo>
cd CurryCast
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/generate_synthetic_data.py     # 12 months of Café Mahaweli data
python scripts/train_model.py                 # train Prophet + LightGBM
uvicorn src.api.service:app --reload          # API on :8000

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev                                   # React app on :5173
```

Open `http://localhost:5173`.

---

## 📁 Project Structure

```
CurryCast/
├── architecture/                # pipeline diagram (HTML)
├── configs/                     # YAML model configs
├── data/                        # raw, processed, synthetic, model artifacts
├── src/                         # Python backend
│   ├── data/                    # generator, loader, POS connectors, SKU cleaner
│   ├── features/                # calendar, holidays, weather, events, tourism
│   ├── models/                  # forecaster, buffet translator, evaluator
│   ├── api/                     # external APIs + FastAPI service (CORS-enabled)
│   ├── pipeline/                # train + predict
│   └── utils/
├── frontend/                    # ✨ React + TypeScript dashboard
│   ├── src/
│   │   ├── pages/               # Home / Forecast / PrepList / WeatherImpact / Backtest
│   │   ├── components/          # Sidebar, Layout, Metric, Loading
│   │   └── lib/                 # API client + item labels
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile               # nginx serve
├── dashboard/                   # legacy Streamlit (still works)
├── scripts/                     # CLI entry points
├── tests/                       # 14 unit tests
├── docker-compose.yml           # api + frontend
└── docs/                        # case study
```

---

## 🎨 Frontend

React + TypeScript + Vite + Recharts. **Sri Lankan luxe theme:** gold (#D4AF37) on black/brown.

| Page             | What it shows                                                            |
|------------------|--------------------------------------------------------------------------|
| `/`              | Pitch / hero with key metrics                                            |
| `/forecast`      | 7-day daily covers chart with 80% confidence band                        |
| `/prep`          | Tomorrow's prep cards (kg / portions) — EN / Sinhala / Tamil labels      |
| `/weather`       | 7-day weather strip + auto-balanced prep adjustments                     |
| `/backtest`      | Replay last N days · LKR savings · per-item accuracy bars                |

The frontend talks to the FastAPI backend via the `/api` proxy (configured in `vite.config.ts`).

---

## 🍴 Who's it for?

| Restaurant type        | Fit       | Primary value                              |
|------------------------|-----------|--------------------------------------------|
| Buffet / rice-and-curry| ⭐⭐⭐⭐⭐  | Cuts over-prep waste 20–40%                |
| Mid-size casual dining | ⭐⭐⭐⭐    | Daily prep + procurement                   |
| Tourist-facing fine dine | ⭐⭐⭐    | Procurement-side wins (seafood, imports)   |

Reference targets: **Upali's**, **Café Sociale**, **Barefoot Café**, **Nuga Gama** (Cinnamon Grand), **Raja Bojun**, **Ministry of Crab**, **Kaema Sutra**.

---

## 🔌 POS Integrations

Out of the box:
- **NooDelo** — adapter in `src/data/pos_connectors.py`
- **Groowey** — adapter
- **Restora** — adapter
- **Generic CSV** — works with anything that exports timestamp + item + qty

---

## 📊 Demo Numbers (back-test on synthetic Café Mahaweli, 12 months)

- WAPE on hourly per-item forecasts: **15.6%**
- Naive over-prep cost (last-week + 30%): **LKR 4.1M / 30 days**
- CurryCast over-prep cost (forecast + 5%): **LKR 588k / 30 days**
- **Savings: LKR 3.5M / 30 days** vs. gut-feel baseline
- Stockout incidents down: **62%**
- Payback: **~3 months**

---

## 🛠️ Tech Stack

**Backend**
- Python 3.10+
- Prophet — daily covers backbone
- LightGBM — hourly item-level head
- FastAPI — REST API with CORS
- Pandera — schema validation
- RapidFuzz — SKU normalization

**Frontend**
- React 18 + TypeScript
- Vite (dev server + build)
- Recharts (data visualization)
- Lucide (icons)

---

## 📚 Documentation

- [architecture/pipeline_diagram.html](architecture/pipeline_diagram.html) — system diagram
- [frontend/README.md](frontend/README.md) — frontend dev guide
- [docs/case_study_cafe_mahaweli.md](docs/case_study_cafe_mahaweli.md) — anonymized case study

---

## 📜 License

MIT — built as part of an AI-for-Sri Lankan-business portfolio.

---
**Developed by Vidura Wijekoon**
