"""CurryCast demand forecaster — Prophet daily backbone + LightGBM hourly head."""

from __future__ import annotations

import json
import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import PATHS, SETTINGS
from src.utils.logger import get_logger

log = get_logger(__name__)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    log.warning("lightgbm not installed — falling back to GradientBoostingRegressor")

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    log.warning("prophet not installed — falling back to seasonal-naive daily backbone")


@dataclass
class DailyCoversModel:
    """Predicts daily covers."""

    model: Any = None
    fallback_means: dict | None = None
    holidays_df: pd.DataFrame | None = None

    def fit(self, daily, holidays_df=None) -> None:
        if HAS_PROPHET:
            df = daily[["date", "covers"]].rename(columns={"date": "ds", "covers": "y"}).copy()
            df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)
            cfg = SETTINGS["model"]["daily_backbone"]
            self.model = Prophet(
                yearly_seasonality=cfg.get("yearly_seasonality", True),
                weekly_seasonality=cfg.get("weekly_seasonality", True),
                daily_seasonality=cfg.get("daily_seasonality", False),
                changepoint_prior_scale=cfg.get("changepoint_prior_scale", 0.05),
                holidays_prior_scale=cfg.get("holidays_prior_scale", 10.0),
                interval_width=cfg.get("interval_width", 0.8),
                holidays=holidays_df,
            )
            self.model.fit(df)
            log.info("Prophet daily model fit on %d days", len(df))
        else:
            tmp = daily.copy()
            tmp["dow"] = pd.to_datetime(tmp["date"]).dt.dayofweek
            self.fallback_means = tmp.groupby("dow")["covers"].mean().to_dict()
            log.info("Seasonal-naive daily fallback fit (dow means: %s)", self.fallback_means)

    def predict(self, dates) -> pd.DataFrame:
        idx = pd.DatetimeIndex(pd.to_datetime(list(dates)))
        if idx.tz is not None:
            idx = idx.tz_localize(None)
        if HAS_PROPHET and self.model is not None:
            future = pd.DataFrame({"ds": idx})
            fc = self.model.predict(future)
            return pd.DataFrame({
                "date": pd.to_datetime(fc["ds"]),
                "yhat": fc["yhat"].clip(lower=0),
                "yhat_lower": fc["yhat_lower"].clip(lower=0),
                "yhat_upper": fc["yhat_upper"].clip(lower=0),
            })
        rows = []
        for d in idx:
            base = self.fallback_means.get(d.dayofweek, 100.0)
            rows.append({
                "date": d, "yhat": base,
                "yhat_lower": base * 0.85, "yhat_upper": base * 1.15,
            })
        return pd.DataFrame(rows)


@dataclass
class HourlyItemModel:
    """Predicts hourly quantity per item."""

    model: Any = None
    feature_cols: list = None
    item_categories: list = None

    DEFAULT_FEATURES = [
        "hour", "item_id",
        "hour_sin", "hour_cos", "is_lunch", "is_dinner",
        "dow", "month", "is_weekend", "is_payday", "is_school_term",
        "dow_sin", "dow_cos", "month_sin", "month_cos",
        "is_poya", "is_public_holiday", "is_holiday_tomorrow",
        "days_to_perahera", "days_to_holiday", "is_perahera_window",
        "is_event_day", "event_multiplier",
        "is_perahera", "is_kandy_event",
        # Tourism — country-level + city-specific
        "arrivals_k", "kandy_arrivals_k", "colombo_arrivals_k",
        "city_arrivals_k", "city_share", "tourist_lift_pct",
        "is_high_season", "is_city_peak",
        "is_perahera_month", "is_peak_month",
        # Weather
        "temp_c", "humidity", "rain_mm", "is_rainy", "heat_index", "is_heavy_rain",
        # Lags
        "quantity_lag_1", "quantity_lag_7", "quantity_lag_14", "quantity_lag_28",
        "quantity_roll_7", "quantity_roll_28",
    ]

    def fit(self, df, target="quantity") -> dict:
        cfg = SETTINGS["model"]["hourly_head"]
        feats = [c for c in self.DEFAULT_FEATURES if c in df.columns]
        self.feature_cols = feats
        self.item_categories = sorted(df["item_canonical"].dropna().unique().tolist())
        train = df.dropna(subset=feats + [target]).copy()
        if len(train) < 100:
            log.warning("Very small training set: %d rows", len(train))
        X = train[feats]
        y = train[target]
        if HAS_LGB:
            self.model = lgb.LGBMRegressor(
                objective=cfg.get("objective", "regression"),
                metric=cfg.get("metric", "mae"),
                learning_rate=cfg.get("learning_rate", 0.05),
                num_leaves=cfg.get("num_leaves", 31),
                max_depth=cfg.get("max_depth", 7),
                min_child_samples=cfg.get("min_child_samples", 20),
                n_estimators=cfg.get("n_estimators", 400),
                random_state=cfg.get("random_state", 42),
                verbosity=-1,
            )
            self.model.fit(X, y)
        else:
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor(
                n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42
            )
            self.model.fit(X, y)
        preds = self.model.predict(X).clip(min=0)
        train_mae = float(np.abs(preds - y).mean())
        log.info("Hourly head trained: %d rows | %d features | train MAE=%.2f",
                 len(train), len(feats), train_mae)
        return {"train_mae": train_mae, "n_train": len(train), "n_features": len(feats)}

    def predict(self, df) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model not fit yet")
        X = df[self.feature_cols]
        return self.model.predict(X).clip(min=0)


@dataclass
class DemandForecaster:
    daily: DailyCoversModel = None
    hourly: HourlyItemModel = None
    metadata: dict = None

    def __post_init__(self):
        self.daily = self.daily or DailyCoversModel()
        self.hourly = self.hourly or HourlyItemModel()
        self.metadata = self.metadata or {}

    def fit(self, daily_df, hourly_df, holidays_df=None):
        log.info("Training CurryCast demand forecaster")
        self.daily.fit(daily_df, holidays_df=holidays_df)
        metrics = self.hourly.fit(hourly_df)
        self.metadata = {
            "trained_at": pd.Timestamp.utcnow().isoformat(),
            "n_daily_rows": len(daily_df),
            "n_hourly_rows": len(hourly_df),
            **metrics,
        }
        return self.metadata

    def predict_daily(self, dates):
        return self.daily.predict(dates)

    def predict_hourly(self, hourly_features):
        out = hourly_features.copy()
        out["yhat"] = self.hourly.predict(hourly_features)
        return out

    def save(self, name="currycast_model"):
        PATHS.ensure()
        path = PATHS.data_models / f"{name}.pkl"
        with path.open("wb") as f:
            pickle.dump(self, f)
        meta_path = PATHS.data_models / f"{name}.meta.json"
        meta_path.write_text(json.dumps(self.metadata, indent=2, default=str))
        log.info("Saved model -> %s", path)
        return path

    @classmethod
    def load(cls, name="currycast_model"):
        path = PATHS.data_models / f"{name}.pkl"
        with path.open("rb") as f:
            return pickle.load(f)
