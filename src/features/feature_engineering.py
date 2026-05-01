"""Top-level feature engineering orchestrator."""

from __future__ import annotations

import pandas as pd

from src.features.calendar_features import add_calendar_features, add_hour_features
from src.features.event_features import add_event_features
from src.features.holiday_features import add_holiday_features
from src.features.tourist_features import add_tourist_features
from src.features.weather_features import add_weather_features
from src.utils.logger import get_logger

log = get_logger(__name__)


def build_daily_features(daily: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Per-day feature matrix. ``daily`` must have [date, covers]."""
    log.info("Building daily features (%d rows)", len(daily))
    df = daily.copy()
    df = add_calendar_features(df, "date")
    df = add_holiday_features(df, "date")
    df = add_event_features(df, "date")
    df = add_tourist_features(df, "date")
    df = add_weather_features(df, weather, "date")
    return df


def add_lag_features(df, target, group_cols, lags, rolling):
    """Lag + rolling-mean features (no leakage). Group-wise if group_cols set."""
    out = df.copy()
    if group_cols:
        for lag in lags:
            out[f"{target}_lag_{lag}"] = (
                out.groupby(group_cols, sort=False)[target].shift(lag)
            )
        for w in rolling:
            out[f"{target}_roll_{w}"] = (
                out.groupby(group_cols, sort=False)[target]
                .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            )
    else:
        for lag in lags:
            out[f"{target}_lag_{lag}"] = out[target].shift(lag)
        for w in rolling:
            out[f"{target}_roll_{w}"] = (
                out[target].shift(1).rolling(w, min_periods=1).mean()
            )
    return out


def build_hourly_features(hourly, daily_features, lags=(1, 7, 14, 28), rolling=(7, 28)):
    """Build per (date, hour, item) feature matrix."""
    log.info("Building hourly features (%d rows)", len(hourly))
    df = hourly.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["item_canonical", "date", "hour"]).reset_index(drop=True)
    df = add_hour_features(df, "hour")
    df = add_lag_features(
        df, target="quantity",
        group_cols=["item_canonical", "hour"],
        lags=list(lags), rolling=list(rolling),
    )
    daily_keys = [
        "date", "dow", "month", "is_weekend", "is_payday", "is_school_term",
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
    ]
    keep = [c for c in daily_keys if c in daily_features.columns]
    df = df.merge(daily_features[keep], on="date", how="left")
    df["item_id"] = pd.Categorical(df["item_canonical"]).codes
    return df
