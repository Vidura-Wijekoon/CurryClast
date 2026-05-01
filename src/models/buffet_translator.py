"""Convert daily covers into kg/portion prep quantities for the kitchen.

Two strategies, picked automatically:
1. **Learned ratios** — if historical (covers, item_qty) data is available,
   we fit a per-item ratio = E[qty / covers] using a simple ridge.
2. **Configured ratios** — fall back to YAML-configured `consumption_ratios`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import SETTINGS, PATHS
from src.utils.logger import get_logger

log = get_logger(__name__)


# kg per portion conversion (used to display rice in portions and curries in kg)
PORTION_OR_KG: dict[str, str] = {
    "rice": "kg",
    "dhal_curry": "kg",
    "pol_sambol": "kg",
    "fish_ambul_thiyal": "portions",
    "chicken_curry": "kg",
    "chicken_kottu": "portions",
    "cheese_kottu": "portions",
    "egg_kottu": "portions",
    "string_hoppers": "portions",
    "egg_hopper": "portions",
    "devilled_chicken": "portions",
    "cashew_curry": "kg",
    "brinjal_moju": "kg",
    "seer_fish_curry": "kg",
    "king_coconut": "units",
    "lion_lager": "bottles",
    "faluda": "glasses",
}


@dataclass
class BuffetTranslator:
    consumption_ratios: dict[str, float] = field(default_factory=dict)
    shrinkage_factor: float = 1.05
    min_prep: float = 0.5

    def __post_init__(self):
        if not self.consumption_ratios:
            buf = SETTINGS.get("buffet", {})
            self.consumption_ratios = dict(buf.get("consumption_ratios", {}))
            self.shrinkage_factor = buf.get("shrinkage_factor", 1.05)
            self.min_prep = buf.get("min_prep_kg", 0.5)

    def fit(self, daily_covers: pd.DataFrame, hourly: pd.DataFrame) -> None:
        """Learn ratios from history. Updates `self.consumption_ratios`.

        Args:
            daily_covers: [date, covers]
            hourly: [date, hour, item_canonical, quantity]
        """
        if hourly.empty:
            log.warning("No hourly data — keeping configured ratios")
            return
        item_daily = (
            hourly.groupby([pd.to_datetime(hourly["date"]).dt.date, "item_canonical"])["quantity"]
            .sum().reset_index()
        )
        item_daily.columns = ["date", "item_canonical", "qty"]
        merged = item_daily.merge(
            daily_covers.assign(date=pd.to_datetime(daily_covers["date"]).dt.date),
            on="date", how="left",
        )
        merged = merged[merged["covers"] > 0]
        learned: dict[str, float] = {}
        for item, sub in merged.groupby("item_canonical"):
            ratio = float((sub["qty"] / sub["covers"]).median())
            learned[item] = ratio
        log.info("Learned %d consumption ratios", len(learned))
        self.consumption_ratios.update(learned)

    def translate(self, daily_forecast: pd.DataFrame) -> pd.DataFrame:
        """Daily forecast → prep list per (date, item).

        Args:
            daily_forecast: [date, yhat (covers)]
        Returns:
            DataFrame columns: date, item_canonical, prep_qty, unit
        """
        rows = []
        for _, r in daily_forecast.iterrows():
            covers = float(r["yhat"])
            for item, ratio in self.consumption_ratios.items():
                qty = covers * ratio * self.shrinkage_factor
                qty = max(qty, self.min_prep)
                rows.append({
                    "date": r["date"],
                    "item_canonical": item,
                    "prep_qty": round(qty, 2),
                    "unit": PORTION_OR_KG.get(item, "kg"),
                })
        return pd.DataFrame(rows)

    def adjust_for_weather(
        self, prep: pd.DataFrame, weather: pd.DataFrame,
    ) -> pd.DataFrame:
        """Re-balance prep list given weather forecast.

        Heuristics:
          - heavy rain → +12% kottu/string hoppers (comfort food)
          - heavy rain → -40% king_coconut (cold drinks)
          - high heat (>33°C) → +10% king_coconut, -8% rice
        """
        if weather is None or weather.empty:
            return prep
        out = prep.copy()
        out["date"] = pd.to_datetime(out["date"])
        weather = weather.copy()
        weather["date"] = pd.to_datetime(weather["date"])
        out = out.merge(
            weather[["date", "rain_mm", "temp_c", "is_rainy"]],
            on="date", how="left",
        )
        comfort = {"chicken_kottu", "string_hoppers", "egg_kottu", "cheese_kottu"}
        cold_drinks = {"king_coconut", "faluda"}

        def _adjust(row):
            qty = row["prep_qty"]
            if row["rain_mm"] and row["rain_mm"] > 5:
                if row["item_canonical"] in comfort:
                    qty *= 1.12
                if row["item_canonical"] in cold_drinks:
                    qty *= 0.6
            if row["temp_c"] and row["temp_c"] > 33:
                if row["item_canonical"] == "king_coconut":
                    qty *= 1.10
                if row["item_canonical"] == "rice":
                    qty *= 0.92
            return round(qty, 2)

        out["prep_qty"] = out.apply(_adjust, axis=1)
        return out.drop(columns=["rain_mm", "temp_c", "is_rainy"], errors="ignore")
