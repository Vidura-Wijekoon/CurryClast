"""Tourist arrival features driven by SLTDA monthly data.

We expose a *city-aware* tourist signal:
  - arrivals_k        : country-level monthly arrivals (thousands)
  - kandy_arrivals_k  : Kandy's share of arrivals on that day
  - city_arrivals_k   : the active city's share (Kandy or Colombo)
  - is_high_season    : country-level arrivals > 200k
  - is_kandy_peak     : kandy_arrivals_k in the top quartile
  - tourist_lift_pct  : multiplicative lift vs the calendar median (0–1 = no lift)

Real deployment fetches via ``src.api.external_apis.SLTDAClient``;
demo uses baked-in monthly baselines that follow SLTDA's published patterns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd

from src.config import SETTINGS

# Approximate monthly arrivals (thousands) — SLTDA historical patterns.
# 2025 Aug is bumped because Esala Perahera draws international cultural tourism.
MONTHLY_ARRIVALS_K: dict[tuple[int, int], float] = {
    (2025, 4): 168, (2025, 5): 130, (2025, 6): 110, (2025, 7): 145,
    (2025, 8): 195, (2025, 9): 130, (2025, 10): 145, (2025, 11): 195,
    (2025, 12): 245, (2026, 1): 240, (2026, 2): 230, (2026, 3): 200,
    (2026, 4): 175, (2026, 5): 135, (2026, 6): 115, (2026, 7): 150,
    (2026, 8): 200, (2026, 9): 135, (2026, 10): 150, (2026, 11): 200,
    (2026, 12): 250,
}

# Approx. share of inbound tourists who pass through each region within a 7-day
# Sri Lanka itinerary. Kandy is a near-mandatory cultural triangle stop.
# Sources: SLTDA quarterly bulletin, hotel occupancy reports, peer review.
BASE_KANDY_SHARE = 0.28          # ~28% of arrivals visit Kandy at any time
BASE_COLOMBO_SHARE = 0.42        # ~42% pass through Colombo

# Perahera-month bump: Kandy share rises sharply, Colombo dips slightly.
PERAHERA_KANDY_SHARE = 0.46
PERAHERA_COLOMBO_SHARE = 0.38

# Tourist-peak (Dec–Feb) — Kandy gets a moderate lift, Colombo a smaller one.
PEAK_KANDY_SHARE = 0.32
PEAK_COLOMBO_SHARE = 0.44


def _is_perahera_month(year: int, month: int) -> bool:
    # Esala Perahera typically concludes in late July or August.
    return month in (7, 8)


def _is_peak_month(year: int, month: int) -> bool:
    return month in (12, 1, 2)


def _kandy_share(year: int, month: int) -> float:
    if _is_perahera_month(year, month):
        return PERAHERA_KANDY_SHARE
    if _is_peak_month(year, month):
        return PEAK_KANDY_SHARE
    return BASE_KANDY_SHARE


def _colombo_share(year: int, month: int) -> float:
    if _is_perahera_month(year, month):
        return PERAHERA_COLOMBO_SHARE
    if _is_peak_month(year, month):
        return PEAK_COLOMBO_SHARE
    return BASE_COLOMBO_SHARE


def _city_share(city: str, year: int, month: int) -> float:
    if city == "Kandy":
        return _kandy_share(year, month)
    return _colombo_share(year, month)


def fetch_monthly_series(months: Iterable[tuple[int, int]] | None = None) -> pd.DataFrame:
    """Return monthly SLTDA series with derived city shares."""
    keys = list(months) if months else sorted(MONTHLY_ARRIVALS_K.keys())
    rows = []
    for y, m in keys:
        arr = MONTHLY_ARRIVALS_K.get((y, m), 150.0)
        rows.append({
            "year": y,
            "month": m,
            "arrivals_k": arr,
            "kandy_arrivals_k": round(arr * _kandy_share(y, m), 1),
            "colombo_arrivals_k": round(arr * _colombo_share(y, m), 1),
            "kandy_share": _kandy_share(y, m),
            "colombo_share": _colombo_share(y, m),
            "is_perahera_month": int(_is_perahera_month(y, m)),
            "is_peak_month": int(_is_peak_month(y, m)),
        })
    return pd.DataFrame(rows)


def add_tourist_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add country-level + city-specific tourist features.

    Reads the active restaurant city from ``SETTINGS["restaurant"]["city"]``
    so that the LightGBM head sees the demand signal that actually applies
    to the venue.
    """
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    city = SETTINGS.get("restaurant", {}).get("city", "Colombo")

    def _arr(d):
        return MONTHLY_ARRIVALS_K.get((d.year, d.month), 150.0)

    out["arrivals_k"] = out[date_col].apply(_arr)
    out["kandy_arrivals_k"] = out[date_col].apply(
        lambda d: _arr(d) * _kandy_share(d.year, d.month)
    )
    out["colombo_arrivals_k"] = out[date_col].apply(
        lambda d: _arr(d) * _colombo_share(d.year, d.month)
    )
    # The "active city" arrivals — what the model should pay most attention to.
    if city == "Kandy":
        out["city_arrivals_k"] = out["kandy_arrivals_k"]
        out["city_share"] = out[date_col].apply(lambda d: _kandy_share(d.year, d.month))
    else:
        out["city_arrivals_k"] = out["colombo_arrivals_k"]
        out["city_share"] = out[date_col].apply(lambda d: _colombo_share(d.year, d.month))

    # Calendar binaries
    out["is_high_season"] = (out["arrivals_k"] > 200).astype(int)
    out["is_perahera_month"] = out[date_col].dt.month.isin([7, 8]).astype(int)
    out["is_peak_month"] = out[date_col].dt.month.isin([12, 1, 2]).astype(int)

    # Top-quartile lift flag for the active city
    if len(out) > 4:
        q75 = out["city_arrivals_k"].quantile(0.75)
        out["is_city_peak"] = (out["city_arrivals_k"] >= q75).astype(int)
    else:
        out["is_city_peak"] = 0

    # Multiplicative lift vs the city's median monthly arrivals
    median_city = out["city_arrivals_k"].median() if len(out) else 1.0
    if median_city <= 0:
        median_city = 1.0
    out["tourist_lift_pct"] = (out["city_arrivals_k"] / median_city) - 1.0
    return out
