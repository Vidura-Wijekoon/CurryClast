"""Load + clean POS data into the canonical model-ready feature table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PATHS
from src.data.data_cleaner import normalize_dataframe
from src.data.pos_connectors import get_connector
from src.utils.logger import get_logger

log = get_logger(__name__)


def load_pos_data(
    source: str | Path,
    connector: str = "generic_csv",
) -> pd.DataFrame:
    """Load raw POS data + normalize SKUs.

    Returns a DataFrame with canonical columns plus `item_canonical`.
    """
    log.info("Loading POS data from %s via %s", source, connector)
    conn = get_connector(connector)
    df = conn.load(source)

    df = normalize_dataframe(df, item_col="item_name")
    n_unmapped = df["item_canonical"].isna().sum()
    if n_unmapped:
        log.warning("%d rows had unmappable item names", n_unmapped)
    df = df.dropna(subset=["item_canonical"]).copy()

    # Ensure timezone-aware Asia/Colombo
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Colombo")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("Asia/Colombo")

    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["dow"] = df["timestamp"].dt.dayofweek
    return df


def aggregate_daily_covers(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (date) with total covers + revenue."""
    daily = (
        df.groupby("date")
        .agg(
            covers=("covers", "sum"),
            orders=("order_id", "nunique"),
            revenue_lkr=("total_lkr", "sum"),
        )
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date").reset_index(drop=True)


def aggregate_hourly_items(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, hour, item_canonical) with quantity sold."""
    hourly = (
        df.groupby(["date", "hour", "item_canonical"])
        .agg(
            quantity=("quantity", "sum"),
            revenue_lkr=("total_lkr", "sum"),
        )
        .reset_index()
    )
    hourly["date"] = pd.to_datetime(hourly["date"])
    return hourly.sort_values(["date", "hour", "item_canonical"]).reset_index(drop=True)


def save_processed(df: pd.DataFrame, name: str) -> Path:
    PATHS.ensure()
    out = PATHS.data_processed / f"{name}.parquet"
    df.to_parquet(out, index=False)
    log.info("Wrote %s (%d rows) → %s", name, len(df), out)
    return out
