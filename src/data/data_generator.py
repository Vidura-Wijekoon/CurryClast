"""Synthetic POS data generator for CurryCast.

Two preset profiles:
- "cafe_mahaweli" — Colombo casual diner / lunch buffet (legacy default).
- "kulture32"     — Kandy heritage Asian + Sri Lankan restaurant.

Embeds realistic Sri Lanka demand drivers:
- Weekly + yearly seasonality
- Sri Lanka public holidays + poya days
- Esala Perahera 10-day spike (massive for Kandy)
- Galle Lit Fest / Tooth Relic devotee flow
- Tourist arrivals (SLTDA pattern)
- Weather (rain dampens dine-in, lifts delivery)
- Payday cycles
- Item-level mix shifts (kottu evening, rice & curry lunch, tea Kandy-heavy)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from src.config import PATHS, SETTINGS
from src.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Sri Lanka calendar
# ---------------------------------------------------------------------------

POYA_DAYS_2025 = [
    "2025-01-13", "2025-02-12", "2025-03-13", "2025-04-12",
    "2025-05-11", "2025-06-10", "2025-07-10", "2025-08-08",
    "2025-09-07", "2025-10-06", "2025-11-05", "2025-12-04",
]
POYA_DAYS_2026 = [
    "2026-01-03", "2026-02-01", "2026-03-03", "2026-04-01",
    "2026-04-30", "2026-05-30", "2026-06-29", "2026-07-28",
    "2026-08-27", "2026-09-25", "2026-10-25", "2026-11-23", "2026-12-23",
]

PUBLIC_HOLIDAYS_LK: dict[str, str] = {
    "2025-01-14": "Tamil Thai Pongal Day",
    "2025-02-04": "Independence Day",
    "2025-04-13": "Sinhala & Tamil New Year Eve",
    "2025-04-14": "Sinhala & Tamil New Year",
    "2025-05-01": "May Day",
    "2025-12-25": "Christmas",
    "2026-01-14": "Tamil Thai Pongal Day",
    "2026-02-04": "Independence Day",
    "2026-04-13": "Sinhala & Tamil New Year Eve",
    "2026-04-14": "Sinhala & Tamil New Year",
    "2026-05-01": "May Day",
    "2026-12-25": "Christmas",
}

# Events: (start, end, name, dine_in_multiplier, kandy_only)
EVENTS: list[tuple[str, str, str, float, bool]] = [
    ("2025-07-31", "2025-08-09", "Esala Perahera (Kandy)",  1.45, True),
    ("2026-08-19", "2026-08-28", "Esala Perahera (Kandy)",  1.45, True),
    ("2026-01-22", "2026-01-25", "Galle Literary Festival", 1.05, False),
    ("2025-12-15", "2026-01-05", "Tourist Peak",            1.18, False),
    ("2026-12-15", "2026-12-31", "Tourist Peak",            1.18, False),
    ("2025-09-06", "2025-09-07", "Cricket Test SSC",        1.06, False),
    ("2026-03-14", "2026-03-15", "Cricket ODI Premadasa",   1.05, False),
    ("2025-08-15", "2025-08-16", "Cricket Asgiriya Kandy",  1.10, True),
    ("2026-02-12", "2026-02-13", "Kandy Tea Festival",      1.12, True),
]


# ---------------------------------------------------------------------------
# Item profiles — superset for both restaurants
# ---------------------------------------------------------------------------

ITEM_PROFILES: dict[str, dict[str, Any]] = {
    # Sri Lankan core
    "rice":              {"daily_qty": 95, "price": 250,  "lunch_share": 0.7},
    "dhal_curry":        {"daily_qty": 90, "price": 350,  "lunch_share": 0.7},
    "pol_sambol":        {"daily_qty": 80, "price": 200,  "lunch_share": 0.65},
    "fish_ambul_thiyal": {"daily_qty": 35, "price": 950,  "lunch_share": 0.55},
    "chicken_curry":     {"daily_qty": 55, "price": 850,  "lunch_share": 0.55},
    "cashew_curry":      {"daily_qty": 25, "price": 700,  "lunch_share": 0.65},
    "brinjal_moju":      {"daily_qty": 30, "price": 450,  "lunch_share": 0.65},
    "seer_fish_curry":   {"daily_qty": 22, "price": 1450, "lunch_share": 0.55},
    "polos_curry":       {"daily_qty": 30, "price": 600,  "lunch_share": 0.65},
    "kandyan_beef_curry":{"daily_qty": 28, "price": 1100, "lunch_share": 0.45},
    # Heritage / Burgher
    "lamprais":          {"daily_qty": 32, "price": 1450, "lunch_share": 0.60},
    "milk_rice":         {"daily_qty": 22, "price": 350,  "lunch_share": 0.85},
    "watalappan":        {"daily_qty": 28, "price": 550,  "lunch_share": 0.40},
    "love_cake":         {"daily_qty": 18, "price": 450,  "lunch_share": 0.40},
    # Short eats
    "string_hoppers":    {"daily_qty": 45, "price": 600,  "lunch_share": 0.30},
    "egg_hopper":        {"daily_qty": 30, "price": 250,  "lunch_share": 0.20},
    "devilled_chicken":  {"daily_qty": 30, "price": 1300, "lunch_share": 0.30},
    # Kottu
    "chicken_kottu":     {"daily_qty": 70, "price": 1200, "lunch_share": 0.20},
    "cheese_kottu":      {"daily_qty": 25, "price": 1450, "lunch_share": 0.15},
    "egg_kottu":         {"daily_qty": 20, "price": 1100, "lunch_share": 0.20},
    # Asian fusion
    "nasi_goreng":       {"daily_qty": 26, "price": 1250, "lunch_share": 0.45},
    "pad_thai":          {"daily_qty": 24, "price": 1350, "lunch_share": 0.40},
    "thai_red_curry":    {"daily_qty": 22, "price": 1450, "lunch_share": 0.40},
    "thai_green_curry":  {"daily_qty": 22, "price": 1450, "lunch_share": 0.40},
    "chinese_fried_rice":{"daily_qty": 30, "price": 1100, "lunch_share": 0.50},
    # Drinks
    "king_coconut":      {"daily_qty": 60, "price": 350,  "lunch_share": 0.5},
    "ceylon_tea":        {"daily_qty": 70, "price": 250,  "lunch_share": 0.55},
    "lion_lager":        {"daily_qty": 45, "price": 600,  "lunch_share": 0.15},
    "faluda":            {"daily_qty": 30, "price": 600,  "lunch_share": 0.45},
}

RAW_ALIASES: dict[str, list[str]] = {
    "rice":              ["Rice", "White Rice", "rice"],
    "dhal_curry":        ["Dhal Curry", "Parippu", "Dhal", "dal curry"],
    "pol_sambol":        ["Pol Sambol", "Pol Sambal", "polsambol"],
    "fish_ambul_thiyal": ["Fish Ambul Thiyal", "Ambul Thiyal", "Fish Ambul"],
    "chicken_curry":     ["Chicken Curry", "Chk Curry"],
    "cashew_curry":      ["Cashew Curry", "Cadju Curry"],
    "brinjal_moju":      ["Brinjal Moju", "Wambatu Moju"],
    "seer_fish_curry":   ["Seer Fish Curry", "Thora Curry"],
    "polos_curry":       ["Polos Curry", "Jackfruit Curry", "Polos"],
    "kandyan_beef_curry":["Kandyan Beef", "Beef Curry Kandy", "Kandy Beef"],
    "lamprais":          ["Lamprais", "Lamprice", "Lump Rice"],
    "milk_rice":         ["Milk Rice", "Kiribath", "kiri bath"],
    "watalappan":        ["Watalappan", "Watalapan", "Wattalappam"],
    "love_cake":         ["Love Cake", "Lovecake"],
    "string_hoppers":    ["String Hoppers", "Idiyappam", "Stringhoppers"],
    "egg_hopper":        ["Egg Hopper", "Egg Appa"],
    "devilled_chicken":  ["Devilled Chicken", "Devil Chicken", "Deviled Chicken"],
    "chicken_kottu":     ["Chicken Kottu", "Chk Kottu", "Kottu Chicken",
                          "Chicken Kothu", "kotu chiken", "Chicken Kottu R"],
    "cheese_kottu":      ["Cheese Kottu", "Chse Kottu"],
    "egg_kottu":         ["Egg Kottu", "egg kothu"],
    "nasi_goreng":       ["Nasi Goreng", "Nasi", "Indonesian Fried Rice"],
    "pad_thai":          ["Pad Thai", "Phad Thai", "Thai Noodles"],
    "thai_red_curry":    ["Thai Red Curry", "Red Curry"],
    "thai_green_curry":  ["Thai Green Curry", "Green Curry"],
    "chinese_fried_rice":["Chinese Fried Rice", "CFR", "Fried Rice"],
    "king_coconut":      ["King Coconut", "Thambili"],
    "ceylon_tea":        ["Ceylon Tea", "Tea", "Plain Tea", "Milk Tea"],
    "lion_lager":        ["Lion Lager", "Lion Beer"],
    "faluda":            ["Faluda", "Falooda"],
}

ITEM_TO_CATEGORY: dict[str, str] = {
    "rice": "rice_curry", "dhal_curry": "rice_curry", "pol_sambol": "rice_curry",
    "fish_ambul_thiyal": "rice_curry", "chicken_curry": "rice_curry",
    "cashew_curry": "rice_curry", "brinjal_moju": "rice_curry",
    "seer_fish_curry": "rice_curry", "polos_curry": "rice_curry",
    "kandyan_beef_curry": "rice_curry",
    "lamprais": "heritage", "milk_rice": "heritage",
    "watalappan": "heritage", "love_cake": "heritage",
    "string_hoppers": "short_eats", "egg_hopper": "short_eats",
    "devilled_chicken": "short_eats",
    "chicken_kottu": "kottu", "cheese_kottu": "kottu", "egg_kottu": "kottu",
    "nasi_goreng": "asian_fusion", "pad_thai": "asian_fusion",
    "thai_red_curry": "asian_fusion", "thai_green_curry": "asian_fusion",
    "chinese_fried_rice": "asian_fusion",
    "king_coconut": "drinks", "ceylon_tea": "drinks",
    "lion_lager": "drinks", "faluda": "drinks",
}


# ---------------------------------------------------------------------------
# Restaurant profiles — drive base demand + which items are on the menu
# ---------------------------------------------------------------------------

PROFILE_MENUS: dict[str, list[str]] = {
    "cafe_mahaweli": [
        "rice", "dhal_curry", "pol_sambol", "fish_ambul_thiyal", "chicken_curry",
        "cashew_curry", "brinjal_moju", "seer_fish_curry",
        "string_hoppers", "egg_hopper", "devilled_chicken",
        "chicken_kottu", "cheese_kottu", "egg_kottu",
        "king_coconut", "lion_lager", "faluda",
    ],
    "kulture32": [
        # Sri Lankan core
        "rice", "dhal_curry", "pol_sambol", "fish_ambul_thiyal", "chicken_curry",
        "cashew_curry", "brinjal_moju", "seer_fish_curry",
        "polos_curry", "kandyan_beef_curry",
        # Heritage
        "lamprais", "milk_rice", "watalappan", "love_cake",
        # Short eats + kottu
        "string_hoppers", "egg_hopper",
        "chicken_kottu", "cheese_kottu", "egg_kottu",
        # Asian fusion
        "nasi_goreng", "pad_thai", "thai_red_curry", "thai_green_curry",
        "chinese_fried_rice",
        # Drinks
        "king_coconut", "ceylon_tea", "lion_lager", "faluda",
    ],
}

# Per-profile demand drivers
PROFILE_PARAMS: dict[str, dict[str, Any]] = {
    "cafe_mahaweli": {
        "city": "Colombo",
        "base_covers": 120.0,
        "rain_drop": 0.82,        # how much covers fall in heavy rain
        "heat_drop_threshold_c": 33,
        "tea_uplift": 1.0,
        "perahera_lift": 1.10,    # Colombo gets minor lift only
        "tourist_lift_dec": 1.18,
    },
    "kulture32": {
        "city": "Kandy",
        "base_covers": 95.0,
        "rain_drop": 0.78,
        "heat_drop_threshold_c": 30,  # cooler hill country
        "tea_uplift": 1.4,            # Kandy = tea country
        "perahera_lift": 1.45,        # Kandy is the centre
        "tourist_lift_dec": 1.25,
    },
}


DOW_MULTIPLIER = {0: 0.85, 1: 0.92, 2: 0.95, 3: 1.00, 4: 1.20, 5: 1.30, 6: 1.10}
HOUR_DISTRIBUTION_LUNCH = {11: 0.04, 12: 0.20, 13: 0.30, 14: 0.16, 15: 0.04}
HOUR_DISTRIBUTION_DINNER = {18: 0.06, 19: 0.18, 20: 0.32, 21: 0.20, 22: 0.10, 23: 0.04}


def _parse_dates(strings: list[str]) -> set[date]:
    return {datetime.strptime(s, "%Y-%m-%d").date() for s in strings}


@dataclass
class RestaurantGenerator:
    """Synthetic POS generator parameterised by restaurant profile."""

    profile: str = "cafe_mahaweli"
    start_date: date = date(2025, 4, 1)
    months: int = 12
    seed: int = 7
    rng: np.random.Generator = field(init=False)

    def __post_init__(self):
        if self.profile not in PROFILE_MENUS:
            raise ValueError(
                f"Unknown profile '{self.profile}'. Available: {list(PROFILE_MENUS)}"
            )
        self.rng = np.random.default_rng(self.seed)
        self.poya_set = _parse_dates(POYA_DAYS_2025 + POYA_DAYS_2026)
        self.holiday_set = _parse_dates(list(PUBLIC_HOLIDAYS_LK.keys()))
        self.menu = PROFILE_MENUS[self.profile]
        self.params = PROFILE_PARAMS[self.profile]
        self.base_covers = self.params["base_covers"]
        self.is_kandy = self.params["city"] == "Kandy"

    # ---- Calendar / range -----------------------------------------------

    def _date_range(self) -> list[date]:
        end = self.start_date + timedelta(days=int(self.months * 30.5))
        return [self.start_date + timedelta(days=i) for i in range((end - self.start_date).days)]

    def _event_multiplier(self, d: date) -> tuple[float, str | None]:
        for start, end, name, mult, kandy_only in EVENTS:
            s = datetime.strptime(start, "%Y-%m-%d").date()
            e = datetime.strptime(end, "%Y-%m-%d").date()
            if not (s <= d <= e):
                continue
            if kandy_only and not self.is_kandy:
                # Colombo gets a small spillover effect from Perahera
                if "Perahera" in name:
                    return 1.08, name + " (spillover)"
                continue
            if name == "Tourist Peak":
                return self.params["tourist_lift_dec"], name
            if "Perahera" in name and self.is_kandy:
                return self.params["perahera_lift"], name
            return mult, name
        return 1.0, None

    # ---- Daily covers ---------------------------------------------------

    def _daily_covers(self, d: date, weather: dict) -> tuple[int, dict]:
        mult = 1.0
        flags: dict[str, Any] = {}
        # Day-of-week
        mult *= DOW_MULTIPLIER[d.weekday()]
        # Yearly
        month_seasonality = {
            1: 1.10, 2: 1.05, 3: 1.00, 4: 0.95, 5: 0.95, 6: 0.97,
            7: 1.00, 8: 1.02, 9: 0.98, 10: 1.00, 11: 1.05, 12: 1.20,
        }
        mult *= month_seasonality[d.month]
        # Payday
        last_day = (date(d.year, d.month + 1, 1) - timedelta(days=1)
                    if d.month < 12 else date(d.year, 12, 31))
        if 0 <= (last_day - d).days <= 2 and d.weekday() < 5:
            mult *= 1.25
            flags["is_payday"] = True
        # Poya — Kandy gets lift (devotees), Colombo gets dampening (no alcohol)
        if d in self.poya_set:
            if self.is_kandy:
                mult *= 1.18
                flags["is_poya"] = True
                flags["devotee_day"] = True
            else:
                mult *= 0.82
                flags["is_poya"] = True
        # Public holiday
        if d in self.holiday_set:
            mult *= 1.10
            flags["is_public_holiday"] = True
        # Event
        ev_mult, ev_name = self._event_multiplier(d)
        if d.weekday() >= 5 and ev_name and "Perahera" in ev_name:
            ev_mult *= 1.13  # weekend nights of Perahera even bigger
        mult *= ev_mult
        if ev_name:
            flags["event"] = ev_name
        # Weather
        if weather["rain_mm"] > 5:
            mult *= self.params["rain_drop"]
            flags["heavy_rain"] = True
        elif weather["rain_mm"] > 1:
            mult *= 0.93
        # Heat
        if weather["temp_c"] > self.params["heat_drop_threshold_c"]:
            mult *= 0.95
        # Cool weather in Kandy = mild lift (people seek hot food + tea)
        if self.is_kandy and weather["temp_c"] < 22:
            mult *= 1.04
            flags["cool_day"] = True
        # Noise
        mult *= self.rng.normal(1.0, 0.06)
        covers = int(max(0, self.base_covers * mult))
        flags["mult"] = float(mult)
        return covers, flags

    # ---- Weather generator ---------------------------------------------

    def _generate_weather(self, dates: list[date]) -> pd.DataFrame:
        rows = []
        for d in dates:
            month = d.month
            if self.is_kandy:
                # Kandy is cooler, more rainy than Colombo
                base_temp = {1: 23, 2: 24, 3: 25, 4: 26, 5: 25, 6: 24,
                             7: 23, 8: 23, 9: 24, 10: 24, 11: 23, 12: 23}[month]
                rain_prob = {1: 0.15, 2: 0.10, 3: 0.18, 4: 0.40, 5: 0.55, 6: 0.40,
                             7: 0.30, 8: 0.30, 9: 0.40, 10: 0.65, 11: 0.65, 12: 0.45}[month]
                rain_lambda = 8.0
            else:
                base_temp = {1: 27, 2: 27, 3: 28, 4: 29, 5: 29, 6: 28,
                             7: 28, 8: 28, 9: 28, 10: 28, 11: 27, 12: 27}[month]
                rain_prob = {1: 0.10, 2: 0.08, 3: 0.10, 4: 0.30, 5: 0.55, 6: 0.45,
                             7: 0.35, 8: 0.30, 9: 0.40, 10: 0.55, 11: 0.50, 12: 0.30}[month]
                rain_lambda = 6.0
            is_rainy = self.rng.random() < rain_prob
            rain_mm = float(self.rng.exponential(rain_lambda)) if is_rainy else 0.0
            humidity = float(75 + self.rng.normal(0, 8) + (5 if self.is_kandy else 0))
            temp = float(base_temp + self.rng.normal(0, 1.5))
            rows.append({
                "date": pd.Timestamp(d),
                "temp_c": round(temp, 1),
                "humidity": round(np.clip(humidity, 30, 100), 1),
                "rain_mm": round(rain_mm, 1),
                "is_rainy": rain_mm > 1,
                "weather_main": "Rain" if rain_mm > 1 else "Clouds",
            })
        return pd.DataFrame(rows)

    # ---- Hourly transactions -------------------------------------------

    def _hour_distribution(self, item: str) -> dict[int, float]:
        lunch_share = ITEM_PROFILES[item]["lunch_share"]
        dinner_share = 1 - lunch_share
        dist = {}
        lunch_total = sum(HOUR_DISTRIBUTION_LUNCH.values())
        dinner_total = sum(HOUR_DISTRIBUTION_DINNER.values())
        for h, p in HOUR_DISTRIBUTION_LUNCH.items():
            dist[h] = (p / lunch_total) * lunch_share
        for h, p in HOUR_DISTRIBUTION_DINNER.items():
            dist[h] = (p / dinner_total) * dinner_share
        return dist

    def _generate_day_transactions(self, d: date, covers: int, flags: dict, weather_row: dict) -> list[dict]:
        if covers == 0:
            return []
        cover_factor = covers / self.base_covers
        rows: list[dict] = []
        order_counter = self.rng.integers(1000, 9999)

        for item in self.menu:
            profile = ITEM_PROFILES[item]
            target_qty = profile["daily_qty"] * cover_factor

            # Item-specific perturbations
            if flags.get("is_poya") and item == "lion_lager":
                target_qty *= 0.10  # poya = no alcohol
            if flags.get("devotee_day") and item in ("milk_rice", "polos_curry", "pol_sambol"):
                target_qty *= 1.5
            if flags.get("heavy_rain") and item in ("chicken_kottu", "string_hoppers", "thai_red_curry"):
                target_qty *= 1.12
            if flags.get("heavy_rain") and item in ("king_coconut",):
                target_qty *= 0.6
            if flags.get("cool_day") and item in ("ceylon_tea", "thai_red_curry", "polos_curry"):
                target_qty *= 1.10
            if self.is_kandy and item == "ceylon_tea":
                target_qty *= self.params["tea_uplift"]
            if flags.get("event"):
                ev = flags["event"]
                if "Perahera" in ev:
                    if item in ("kandyan_beef_curry", "lamprais", "milk_rice", "watalappan", "rice"):
                        target_qty *= 1.30
                    if item == "lion_lager":
                        target_qty *= 0.7  # religious crowds
                if "Tourist Peak" in ev:
                    if item in ("fish_ambul_thiyal", "seer_fish_curry", "chicken_kottu",
                                "lamprais", "watalappan", "pad_thai", "thai_red_curry"):
                        target_qty *= 1.20
                if "Cricket" in ev and item in ("chicken_kottu", "lion_lager", "devilled_chicken"):
                    target_qty *= 1.25

            qty = int(max(0, self.rng.normal(target_qty, target_qty * 0.15)))
            if qty == 0:
                continue
            dist = self._hour_distribution(item)
            for hour, hp in dist.items():
                hr_qty = int(round(qty * hp))
                if hr_qty <= 0:
                    continue
                n_orders = max(1, hr_qty // self.rng.integers(2, 5))
                per_order = max(1, hr_qty // n_orders)
                remaining = hr_qty
                for _ in range(n_orders):
                    if remaining <= 0:
                        break
                    take = min(per_order, remaining)
                    remaining -= take
                    minute = int(self.rng.integers(0, 60))
                    ts = datetime(d.year, d.month, d.day, hour, minute)
                    raw_name = self.rng.choice(RAW_ALIASES[item])
                    channel = self._pick_channel(weather_row, item)
                    price = profile["price"]
                    rows.append({
                        "timestamp": ts,
                        "order_id": f"ORD{d.strftime('%y%m%d')}{order_counter:05d}",
                        "item_name": raw_name,
                        "category": ITEM_TO_CATEGORY[item],
                        "quantity": take,
                        "unit_price_lkr": price,
                        "total_lkr": price * take,
                        "covers": int(self.rng.integers(1, 4)),
                        "channel": channel,
                    })
                    order_counter += 1
        return rows

    def _pick_channel(self, weather_row: dict, item: str) -> str:
        delivery_p = 0.18
        if weather_row.get("is_rainy"):
            delivery_p = 0.30
        if item in ("chicken_kottu", "cheese_kottu", "egg_kottu",
                    "nasi_goreng", "chinese_fried_rice"):
            delivery_p += 0.05
        r = self.rng.random()
        if r < delivery_p:
            return "delivery"
        if r < delivery_p + 0.15:
            return "takeaway"
        return "dine_in"

    # ---- Public API ----------------------------------------------------

    def generate(self) -> dict[str, pd.DataFrame]:
        log.info("Generating synthetic data: profile=%s · %s · %d months",
                 self.profile, self.start_date, self.months)
        dates = self._date_range()
        weather_df = self._generate_weather(dates)
        weather_lookup = {row["date"].date(): row for _, row in weather_df.iterrows()}
        all_txns: list[dict] = []
        daily_meta: list[dict] = []
        for d in dates:
            wrow = weather_lookup[d]
            covers, flags = self._daily_covers(d, wrow.to_dict())
            daily_meta.append({
                "date": pd.Timestamp(d),
                "covers": covers,
                "is_poya": flags.get("is_poya", False),
                "is_public_holiday": flags.get("is_public_holiday", False),
                "is_payday": flags.get("is_payday", False),
                "event": flags.get("event"),
                "mult": flags["mult"],
            })
            txns = self._generate_day_transactions(d, covers, flags, wrow.to_dict())
            all_txns.extend(txns)
        txn_df = pd.DataFrame(all_txns)
        if not txn_df.empty:
            txn_df = txn_df.sort_values("timestamp").reset_index(drop=True)
        meta_df = pd.DataFrame(daily_meta)
        log.info("Generated %d transactions across %d days", len(txn_df), len(dates))
        return {"transactions": txn_df, "weather": weather_df, "daily_meta": meta_df}


# ---- Backward-compatible aliases ------------------------------------------

class CafeMahaweliGenerator(RestaurantGenerator):
    """Legacy alias — Café Mahaweli (Colombo)."""
    def __init__(self, **kwargs):
        kwargs.setdefault("profile", "cafe_mahaweli")
        super().__init__(**kwargs)


class Kulture32Generator(RestaurantGenerator):
    """Kulture32 (Kandy) heritage Asian + Sri Lankan."""
    def __init__(self, **kwargs):
        kwargs.setdefault("profile", "kulture32")
        super().__init__(**kwargs)


def generate_and_save(
    profile: str | None = None,
    months: int = 12,
    start_date: date = date(2025, 4, 1),
    seed: int = 7,
) -> dict[str, str]:
    """Generate + save synthetic data for the given profile.

    If profile is None, reads RESTAURANT_PROFILE from settings (defaults to legacy Café Mahaweli).
    """
    profile = profile or SETTINGS.get("restaurant", {}).get("name", "").lower().replace(" ", "_")
    if profile not in PROFILE_MENUS:
        # Best-effort mapping: derive from active config name
        active = SETTINGS.get("restaurant", {}).get("name", "").lower()
        if "kulture" in active:
            profile = "kulture32"
        elif "mahaweli" in active or "default" in active:
            profile = "cafe_mahaweli"
        else:
            profile = "cafe_mahaweli"
    PATHS.ensure()
    gen = RestaurantGenerator(profile=profile, start_date=start_date, months=months, seed=seed)
    out = gen.generate()
    paths = {}
    for name, df in out.items():
        p = PATHS.data_synthetic / f"{name}.parquet"
        df.to_parquet(p, index=False)
        df.to_csv(PATHS.data_synthetic / f"{name}.csv", index=False)
        paths[name] = str(p)
        log.info("Wrote %s: %d rows -> %s", name, len(df), p)
    return paths


if __name__ == "__main__":
    generate_and_save()
