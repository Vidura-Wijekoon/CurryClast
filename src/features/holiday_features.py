"""Sri Lanka holiday + poya day features."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from src.data.data_generator import (
    POYA_DAYS_2025,
    POYA_DAYS_2026,
    PUBLIC_HOLIDAYS_LK,
    EVENTS,
)


def _to_set(strings):
    return {datetime.strptime(s, "%Y-%m-%d").date() for s in strings}


POYA_SET = _to_set(POYA_DAYS_2025 + POYA_DAYS_2026)
HOLIDAY_SET = _to_set(list(PUBLIC_HOLIDAYS_LK.keys()))


def add_holiday_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add is_poya, is_public_holiday, days_to_perahera, etc."""
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    dates = out[date_col].dt.date
    out["is_poya"] = dates.isin(POYA_SET).astype(int)
    out["is_public_holiday"] = dates.isin(HOLIDAY_SET).astype(int)
    out["is_holiday_tomorrow"] = (
        (dates + pd.Timedelta(days=1)).isin(HOLIDAY_SET).astype(int)
    )
    out["days_to_perahera"] = out[date_col].apply(_days_to_perahera)
    out["is_perahera_window"] = (
        out["days_to_perahera"].between(-3, 14).astype(int)
    )
    out["days_to_holiday"] = out[date_col].apply(_days_to_next_holiday)
    return out


def _days_to_perahera(ts: pd.Timestamp) -> int:
    d = ts.date()
    candidates = []
    for ev in EVENTS:
        # (start, end, name, mult, kandy_only)
        start, _end, name = ev[0], ev[1], ev[2]
        if "Perahera" in name:
            sd = datetime.strptime(start, "%Y-%m-%d").date()
            candidates.append(sd)
    candidates = [c for c in candidates if c >= d - timedelta(days=14)]
    if not candidates:
        return 365
    target = min(candidates, key=lambda c: abs((c - d).days))
    return (target - d).days


def _days_to_next_holiday(ts: pd.Timestamp) -> int:
    d = ts.date()
    upcoming = sorted(h for h in HOLIDAY_SET if h >= d)
    if not upcoming:
        return 365
    return (upcoming[0] - d).days
