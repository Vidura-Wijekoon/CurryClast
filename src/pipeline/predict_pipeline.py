"""Daily inference pipeline — produces tomorrow's prep list.

Run nightly at 22:00 Asia/Colombo via cron / Task Scheduler.
"""

from __future__ import annotations

import pickle
from datetime import date, timedelta

import pandas as pd

from src.config import PATHS, SETTINGS
from src.features.feature_engineering import build_daily_features, build_hourly_features
from src.models.demand_forecaster import DemandForecaster
from src.models.buffet_translator import BuffetTranslator
from src.utils.logger import get_logger

log = get_logger(__name__)


# Per-city historical-weather fallback. Used to seed lag features for
# rows that pre-date the future window in _build_future_hourly. The values
# only need to be plausible for the city — the rows themselves are dropped
# before the model sees them. But getting them wrong corrupts lag features.
CITY_FALLBACK_WEATHER = {
    "Kandy":   {"temp_c": 24.0, "humidity": 80.0, "rain_mm": 1.5,
                "is_rainy": False, "weather_main": "Clouds"},
    "Colombo": {"temp_c": 28.5, "humidity": 78.0, "rain_mm": 0.0,
                "is_rainy": False, "weather_main": "Clouds"},
}


def _city_fallback_weather() -> dict:
    city = SETTINGS.get("restaurant", {}).get("city", "Colombo")
    return CITY_FALLBACK_WEATHER.get(city, CITY_FALLBACK_WEATHER["Colombo"])


def _build_future_daily(start, days, weather_future):
    rng = pd.date_range(start=start, periods=days, freq="D")
    skeleton = pd.DataFrame({"date": rng, "covers": 0})
    return build_daily_features(skeleton, weather_future)


def _build_future_hourly(daily_feats, items, last_hourly):
    """Cartesian future hours x items, with lag values backfilled from history."""
    hours = list(range(11, 24))
    rows = []
    for _, drow in daily_feats.iterrows():
        for h in hours:
            for item in items:
                rows.append({
                    "date": drow["date"],
                    "hour": h,
                    "item_canonical": item,
                    "quantity": 0,
                })
    future = pd.DataFrame(rows)

    hist = last_hourly.copy()
    if "date" in hist.columns:
        hist["date"] = pd.to_datetime(hist["date"])
    combined = pd.concat(
        [hist[["date", "hour", "item_canonical", "quantity"]], future],
        ignore_index=True,
    )

    all_dates = pd.DataFrame({
        "date": pd.to_datetime(combined["date"].unique()),
        "covers": 0,
    })
    fb = _city_fallback_weather()
    weather_for_hist = pd.DataFrame({
        "date": all_dates["date"],
        "temp_c": fb["temp_c"],
        "humidity": fb["humidity"],
        "rain_mm": fb["rain_mm"],
        "is_rainy": fb["is_rainy"],
        "weather_main": fb["weather_main"],
    })
    full_daily = build_daily_features(all_dates, weather_for_hist)
    overlay = daily_feats.set_index("date")
    full_daily = full_daily.set_index("date")
    full_daily.update(overlay)
    full_daily = full_daily.reset_index()

    feats = build_hourly_features(combined, full_daily)
    cutoff = daily_feats["date"].min()
    return feats[feats["date"] >= cutoff].copy()


def predict_next_n_days(days: int = 7):
    """Produce both daily covers forecast and per-item hourly forecast."""
    PATHS.ensure()
    fc = DemandForecaster.load("currycast_model")

    weather = pd.read_parquet(PATHS.data_synthetic / "weather.parquet")
    weather["date"] = pd.to_datetime(weather["date"])

    last_daily = pd.read_parquet(PATHS.data_processed / "daily_features.parquet")
    last_hourly = pd.read_parquet(PATHS.data_processed / "hourly_items.parquet")
    last_hourly = last_hourly.dropna(subset=["item_canonical"])

    last_date = pd.to_datetime(last_daily["date"]).max().date()
    start = last_date + timedelta(days=1)
    log.info("Predicting %d days starting %s", days, start)

    future_weather = weather.tail(days).copy()
    future_weather["date"] = pd.date_range(start=start, periods=days, freq="D")

    daily_feats = _build_future_daily(start, days, future_weather)
    daily_pred = fc.predict_daily(daily_feats["date"])

    items = sorted(last_hourly["item_canonical"].dropna().unique().tolist())
    hourly_future = _build_future_hourly(daily_feats, items, last_hourly)
    hourly_pred = fc.predict_hourly(hourly_future)

    bt_path = PATHS.data_models / "buffet_translator.pkl"
    if bt_path.exists():
        bt = pickle.loads(bt_path.read_bytes())
    else:
        bt = BuffetTranslator()
    prep = bt.translate(daily_pred)
    prep = bt.adjust_for_weather(prep, future_weather)

    return {
        "daily_forecast": daily_pred,
        "hourly_forecast": hourly_pred[["date", "hour", "item_canonical", "yhat"]],
        "prep_list": prep,
        "weather_future": future_weather,
    }


if __name__ == "__main__":
    out = predict_next_n_days(7)
    print("\n=== Daily forecast (next 7 days) ===")
    print(out["daily_forecast"].to_string(index=False))
    print("\n=== Tomorrow's prep list ===")
    tomorrow = out["prep_list"]
    tomorrow_date = tomorrow["date"].min()
    print(tomorrow[tomorrow["date"] == tomorrow_date].to_string(index=False))
