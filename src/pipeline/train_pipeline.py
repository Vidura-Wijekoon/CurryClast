"""End-to-end training pipeline.

Steps:
1. Load synthetic (or real POS) data + weather.
2. Aggregate to daily and hourly tables.
3. Build features.
4. Train Prophet daily backbone + LightGBM hourly head.
5. Save model artifact + metadata JSON.
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PATHS, SETTINGS
from src.data.data_generator import generate_and_save
from src.data.data_loader import (
    aggregate_daily_covers,
    aggregate_hourly_items,
)
from src.features.feature_engineering import (
    build_daily_features,
    build_hourly_features,
)
from src.models.demand_forecaster import DemandForecaster
from src.models.buffet_translator import BuffetTranslator
from src.utils.logger import get_logger

log = get_logger(__name__)


def _seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)


def _load_synthetic() -> tuple[pd.DataFrame, pd.DataFrame]:
    txn_path = PATHS.data_synthetic / "transactions.parquet"
    weather_path = PATHS.data_synthetic / "weather.parquet"
    
    needs_gen = not txn_path.exists()
    if not needs_gen:
        # Check if existing data covers up to today
        temp_txn = pd.read_parquet(txn_path)
        last_date = pd.to_datetime(temp_txn["timestamp"]).max().date()
        if last_date < pd.Timestamp.today().date():
            log.info("Synthetic data is stale (last date: %s) — regenerating", last_date)
            needs_gen = True

    if needs_gen:
        log.info("Generating synthetic data...")
        generate_and_save()
    
    txn = pd.read_parquet(txn_path)
    weather = pd.read_parquet(weather_path)

    # The synthetic generator already uses canonical names — but they go
    # through messy aliases. Re-normalize to ensure consistency.
    from src.data.data_cleaner import normalize_dataframe
    txn = normalize_dataframe(txn, item_col="item_name").dropna(subset=["item_canonical"])
    txn["timestamp"] = pd.to_datetime(txn["timestamp"])
    txn["date"] = txn["timestamp"].dt.date
    txn["hour"] = txn["timestamp"].dt.hour
    return txn, weather


def run_training(profile: str | None = None) -> dict:
    _seed(42)
    PATHS.ensure()
    log.info("=== CurryCast training pipeline (profile=%s) ===", profile or "default")

    txn, weather = _load_synthetic()

    daily = aggregate_daily_covers(txn)
    hourly = aggregate_hourly_items(txn)

    # Save intermediate processed tables
    daily.to_parquet(PATHS.data_processed / "daily_covers.parquet", index=False)
    hourly.to_parquet(PATHS.data_processed / "hourly_items.parquet", index=False)

    daily_feats = build_daily_features(daily, weather)
    hourly_feats = build_hourly_features(hourly, daily_feats)
    daily_feats.to_parquet(PATHS.data_processed / "daily_features.parquet", index=False)
    hourly_feats.to_parquet(PATHS.data_processed / "hourly_features.parquet", index=False)

    fc = DemandForecaster()
    metadata = fc.fit(daily_feats[["date", "covers"]], hourly_feats)
    fc.save("currycast_model")

    # Buffet translator — learn ratios from historical
    bt = BuffetTranslator()
    bt.fit(daily, hourly)
    import pickle
    (PATHS.data_models / "buffet_translator.pkl").write_bytes(pickle.dumps(bt))

    log.info("Training complete: %s", metadata)
    return metadata


if __name__ == "__main__":
    run_training()
