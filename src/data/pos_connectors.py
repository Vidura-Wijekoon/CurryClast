"""POS adapters — pluggable readers that produce a canonical transactions DataFrame.

Canonical schema returned by every adapter:
    timestamp (datetime, Asia/Colombo) | order_id | item_name | category |
    quantity | unit_price_lkr | total_lkr | covers | channel
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

CANONICAL_COLUMNS = [
    "timestamp", "order_id", "item_name", "category",
    "quantity", "unit_price_lkr", "total_lkr", "covers", "channel",
]


class POSConnector(ABC):
    """Abstract base class for POS adapters."""

    name: str = "abstract"

    @abstractmethod
    def load(self, source: str | Path) -> pd.DataFrame:
        """Return a DataFrame with CANONICAL_COLUMNS."""


class GenericCSVConnector(POSConnector):
    """Default fallback — expects CSV already in canonical format."""

    name = "generic_csv"

    def load(self, source: str | Path) -> pd.DataFrame:
        df = pd.read_csv(source, parse_dates=["timestamp"])
        missing = set(CANONICAL_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(
                f"CSV missing columns {missing}. "
                f"Expected: {CANONICAL_COLUMNS}"
            )
        return df[CANONICAL_COLUMNS]


class NoodeloConnector(POSConnector):
    """Adapter for NooDelo POS exports.

    NooDelo CSV columns (observed):
        Date,Time,OrderNo,Item,Cat,Qty,UnitPrice,TotalPrice,Persons,Mode
    """

    name = "noodelo"

    def load(self, source: str | Path) -> pd.DataFrame:
        df = pd.read_csv(source)
        df["timestamp"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            errors="coerce",
        )
        out = pd.DataFrame({
            "timestamp": df["timestamp"],
            "order_id": df["OrderNo"].astype(str),
            "item_name": df["Item"],
            "category": df["Cat"].fillna("unknown"),
            "quantity": df["Qty"].astype(int),
            "unit_price_lkr": df["UnitPrice"].astype(float),
            "total_lkr": df["TotalPrice"].astype(float),
            "covers": df.get("Persons", 1).fillna(1).astype(int),
            "channel": df.get("Mode", "dine_in").str.lower().fillna("dine_in"),
        })
        return out[CANONICAL_COLUMNS]


class GrooweyConnector(POSConnector):
    """Adapter for Groowey POS exports."""

    name = "groowey"

    def load(self, source: str | Path) -> pd.DataFrame:
        df = pd.read_csv(source)
        out = pd.DataFrame({
            "timestamp": pd.to_datetime(df["txn_time"], errors="coerce"),
            "order_id": df["bill_no"].astype(str),
            "item_name": df["product_name"],
            "category": df.get("group", "unknown"),
            "quantity": df["qty"].astype(int),
            "unit_price_lkr": df["rate"].astype(float),
            "total_lkr": (df["qty"] * df["rate"]).astype(float),
            "covers": df.get("pax", 1).fillna(1).astype(int),
            "channel": df.get("order_type", "dine_in").str.lower(),
        })
        return out[CANONICAL_COLUMNS]


class RestoraConnector(POSConnector):
    """Adapter for Restora POS exports."""

    name = "restora"

    def load(self, source: str | Path) -> pd.DataFrame:
        df = pd.read_csv(source)
        out = pd.DataFrame({
            "timestamp": pd.to_datetime(df["timestamp"], errors="coerce"),
            "order_id": df["bill_id"].astype(str),
            "item_name": df["item"],
            "category": df.get("category", "unknown"),
            "quantity": df["qty"].astype(int),
            "unit_price_lkr": df["price"].astype(float),
            "total_lkr": df["amount"].astype(float),
            "covers": df.get("guests", 1).fillna(1).astype(int),
            "channel": df.get("source", "dine_in").str.lower(),
        })
        return out[CANONICAL_COLUMNS]


REGISTRY: dict[str, type[POSConnector]] = {
    "generic_csv": GenericCSVConnector,
    "noodelo": NoodeloConnector,
    "groowey": GrooweyConnector,
    "restora": RestoraConnector,
}


def get_connector(name: str) -> POSConnector:
    name = (name or "generic_csv").lower()
    if name not in REGISTRY:
        raise ValueError(
            f"Unknown POS connector '{name}'. Available: {list(REGISTRY)}"
        )
    return REGISTRY[name]()
