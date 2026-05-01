"""FastAPI service for production deployments.

Endpoints:
- GET  /health                     liveness
- POST /predict                    7-day forecast + prep list
- POST /backtest                   replay last N days, return savings metric
- GET  /weather                    current 7-day weather forecast
- GET  /restaurant                 active restaurant profile
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.api.external_apis import WeatherClient
from src.config import SETTINGS
from src.models.back_tester import run_backtest
from src.pipeline.predict_pipeline import predict_next_n_days
from src.utils.logger import get_logger

log = get_logger(__name__)

app = FastAPI(
    title="CurryCast API",
    description="Demand & Buffet Forecasting Engine for Sri Lankan restaurants",
    version="0.2.0",
)

# Allow the React dev server (Vite default 5173) and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:4173", "http://127.0.0.1:4173",
        "*",  # tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    days: int = Field(7, ge=1, le=14, description="Forecast horizon in days")


class BacktestRequest(BaseModel):
    holdout_days: int = Field(30, ge=7, le=90)


@app.get("/health")
def health():
    return {"status": "ok", "restaurant": SETTINGS["restaurant"]["name"],
            "version": app.version}


@app.get("/restaurant")
def restaurant():
    r = SETTINGS["restaurant"]
    return {
        "name": r.get("name"),
        "city": r.get("city"),
        "type": r.get("type"),
        "open_hour": r.get("open_hour"),
        "close_hour": r.get("close_hour"),
        "avg_cover_value_lkr": r.get("avg_cover_value_lkr"),
    }


@app.post("/predict")
def predict(req: PredictRequest):
    try:
        out = predict_next_n_days(req.days)
        city = SETTINGS["restaurant"].get("city", "Colombo")
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "city": city,
            "daily_forecast": out["daily_forecast"].assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
            ).to_dict(orient="records"),
            "prep_list": out["prep_list"].assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
            ).to_dict(orient="records"),
            "weather": out["weather_future"].assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d"),
                is_rainy=lambda d: d["is_rainy"].astype(bool),
            ).to_dict(orient="records"),
            "hourly_forecast": out["hourly_forecast"].assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
            ).to_dict(orient="records"),
        }
    except Exception as e:
        log.exception("Predict failed")
        raise HTTPException(500, str(e)) from e


@app.post("/backtest")
def backtest(req: BacktestRequest):
    from src.config import PATHS
    daily = pd.read_parquet(PATHS.data_processed / "daily_features.parquet")
    hourly = pd.read_parquet(PATHS.data_processed / "hourly_features.parquet")
    res = run_backtest(daily, hourly, holdout_days=req.holdout_days)
    avp = res.actual_vs_pred.copy()
    avp["date"] = pd.to_datetime(avp["date"]).dt.strftime("%Y-%m-%d")
    per_item = (
        avp.groupby("item_canonical")
           .agg(actual=("actual", "sum"), predicted=("predicted", "sum"))
           .reset_index()
           .sort_values("actual", ascending=False)
           .head(20)
           .to_dict(orient="records")
    )
    return {
        "holdout_days": res.holdout_days,
        "metrics": res.metrics,
        "savings": res.savings,
        "per_item": per_item,
    }


@app.get("/weather")
def weather():
    city = SETTINGS["restaurant"].get("city", "Colombo")
    df = WeatherClient().fetch_forecast(city=city)
    return df.assign(
        date=lambda d: pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d"),
        is_rainy=lambda d: d["is_rainy"].astype(bool),
    ).to_dict(orient="records")
