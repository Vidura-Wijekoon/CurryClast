"""Calendar features — day-of-week, hour-of-day, payday, school terms."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add calendar columns. ``date_col`` should be datetime64."""
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out["dow"] = out[date_col].dt.dayofweek
    out["month"] = out[date_col].dt.month
    out["day"] = out[date_col].dt.day
    out["week_of_year"] = out[date_col].dt.isocalendar().week.astype(int)
    out["is_weekend"] = out["dow"].isin([5, 6]).astype(int)

    # Payday — last 2 working days of the month
    out["is_payday"] = out.apply(_is_payday, axis=1).astype(int)

    # School terms (rough Sri Lankan terms)
    out["is_school_term"] = out["month"].isin([1, 2, 3, 5, 6, 7, 9, 10, 11]).astype(int)

    # Cyclical encodings
    out["dow_sin"] = np.sin(2 * np.pi * out["dow"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["dow"] / 7)
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    return out


def add_hour_features(df: pd.DataFrame, hour_col: str = "hour") -> pd.DataFrame:
    out = df.copy()
    out[hour_col] = out[hour_col].astype(int)
    out["hour_sin"] = np.sin(2 * np.pi * out[hour_col] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out[hour_col] / 24)
    out["is_lunch"] = out[hour_col].between(11, 15).astype(int)
    out["is_dinner"] = out[hour_col].between(18, 23).astype(int)
    return out


def _is_payday(row) -> bool:
    d = row["date"]
    if d.month == 12:
        last = pd.Timestamp(year=d.year, month=12, day=31)
    else:
        last = pd.Timestamp(year=d.year, month=d.month + 1, day=1) - pd.Timedelta(days=1)
    days_to_last = (last - d).days
    return 0 <= days_to_last <= 2 and d.weekday() < 5
