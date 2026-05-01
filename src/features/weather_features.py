"""Weather feature joins and derivations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_weather_features(
    df: pd.DataFrame,
    weather: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """Left-join weather and add derived features.

    `weather` must have columns: date, temp_c, humidity, rain_mm, is_rainy.
    """
    weather = weather.copy()
    weather[date_col] = pd.to_datetime(weather[date_col])
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])

    out = out.merge(
        weather[[date_col, "temp_c", "humidity", "rain_mm", "is_rainy"]],
        on=date_col,
        how="left",
    )
    # Derivatives
    out["heat_index"] = (
        out["temp_c"] + 0.05 * out["humidity"].fillna(70)
    )
    out["is_heavy_rain"] = (out["rain_mm"].fillna(0) > 5).astype(int)
    out["is_rainy"] = out["is_rainy"].fillna(False).astype(int)
    return out
