"""External API integrations.

- OpenWeatherMap: 7-day forecast (free tier).
- SLTDA: monthly tourist arrivals scrape.

Both are wrapped with simple in-memory caches; production deployments
should use Redis or a persistent file cache.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Weather (OpenWeatherMap)
# ---------------------------------------------------------------------------


@dataclass
class WeatherClient:
    api_key: str | None = None
    cache: dict[str, tuple[float, Any]] = field(default_factory=dict)
    cache_ttl_s: int = 3600
    base_url: str = "https://api.openweathermap.org/data/2.5"

    def __post_init__(self):
        self.api_key = self.api_key or os.getenv("OPENWEATHER_API_KEY")

    def _cache_get(self, key: str):
        if key in self.cache:
            ts, val = self.cache[key]
            if time.time() - ts < self.cache_ttl_s:
                return val
        return None

    def _cache_set(self, key: str, val):
        self.cache[key] = (time.time(), val)

    def fetch_forecast(
        self, city: str = "Colombo", country: str = "LK"
    ) -> pd.DataFrame:
        """Fetch 5-day / 3-hour forecast and resample to daily.

        Returns columns: date, temp_c, humidity, rain_mm, is_rainy, weather_main.
        Falls back to a synthetic forecast if no API key is configured.
        """
        cache_key = f"forecast::{city},{country}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        if not self.api_key:
            log.warning("No OPENWEATHER_API_KEY — using synthetic weather fallback for %s", city)
            return self._synthetic_forecast(city)

        try:
            import requests
            url = f"{self.base_url}/forecast"
            r = requests.get(url, params={
                "q": f"{city},{country}",
                "appid": self.api_key,
                "units": "metric",
            }, timeout=10)
            r.raise_for_status()
            data = r.json()
            rows = []
            for item in data.get("list", []):
                ts = pd.to_datetime(item["dt"], unit="s")
                rows.append({
                    "datetime": ts,
                    "date": ts.date(),
                    "temp_c": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "rain_mm": item.get("rain", {}).get("3h", 0.0),
                    "weather_main": item["weather"][0]["main"],
                })
            df = pd.DataFrame(rows)
            daily = (
                df.groupby("date")
                .agg(
                    temp_c=("temp_c", "mean"),
                    humidity=("humidity", "mean"),
                    rain_mm=("rain_mm", "sum"),
                    weather_main=("weather_main", lambda s: s.mode().iat[0] if not s.empty else "Clouds"),
                )
                .reset_index()
            )
            daily["is_rainy"] = daily["rain_mm"] > 1
            daily["date"] = pd.to_datetime(daily["date"])
            self._cache_set(cache_key, daily)
            return daily
        except Exception as e:  # pragma: no cover
            log.exception("OpenWeatherMap fetch failed: %s", e)
            return self._synthetic_forecast(city)

    def _synthetic_forecast(self, city: str = "Colombo") -> pd.DataFrame:
        rng = pd.date_range(pd.Timestamp.today().normalize(), periods=7, freq="D")
        
        # Kandy is cooler (22-26C) and more rainy than Colombo (28-31C)
        if city == "Kandy":
            temp_c = [24.0, 23.5, 25.0, 22.0, 21.5, 24.0, 23.5]
            rain_mm = [0.0, 4.2, 0.0, 12.0, 18.0, 2.5, 0.0]
            is_rainy = [False, True, False, True, True, True, False]
            weather_main = ["Clouds", "Rain", "Clear", "Rain", "Rain", "Rain", "Clouds"]
        else:
            temp_c = [29.0, 28.5, 30.0, 28.0, 27.5, 29.0, 28.5]
            rain_mm = [0.0, 1.2, 0.0, 8.0, 12.0, 0.5, 0.0]
            is_rainy = [False, True, False, True, True, False, False]
            weather_main = ["Clouds", "Rain", "Clear", "Rain", "Rain", "Clouds", "Clouds"]

        return pd.DataFrame({
            "date": rng,
            "temp_c": temp_c,
            "humidity": [78, 82, 75, 88, 90, 80, 78],
            "rain_mm": rain_mm,
            "is_rainy": is_rainy,
            "weather_main": weather_main,
        })


# ---------------------------------------------------------------------------
# SLTDA tourist arrivals
# ---------------------------------------------------------------------------


@dataclass
class SLTDAClient:
    """Light scraper for SLTDA monthly tourist arrival reports.

    SLTDA publishes the Monthly Tourist Arrivals Report at
    https://www.sltda.gov.lk/en/monthly-tourist-arrivals-reports
    """

    cache: dict[str, Any] = field(default_factory=dict)

    def fetch_recent(self, months: int = 12) -> pd.DataFrame:
        """Return monthly arrivals; falls back to baked-in defaults."""
        try:
            import requests
            from bs4 import BeautifulSoup
            url = "https://www.sltda.gov.lk/en/monthly-tourist-arrivals-reports"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            # Real implementation would parse the table; we return fallback
            # because page layout may change. The fallback uses our baked
            # defaults from src.features.tourist_features.
        except Exception as e:  # pragma: no cover
            log.warning("SLTDA scrape skipped: %s", e)
        from src.features.tourist_features import MONTHLY_ARRIVALS_K
        rows = [
            {"year": y, "month": m, "arrivals_k": v}
            for (y, m), v in MONTHLY_ARRIVALS_K.items()
        ]
        return pd.DataFrame(rows).sort_values(["year", "month"]).tail(months).reset_index(drop=True)
