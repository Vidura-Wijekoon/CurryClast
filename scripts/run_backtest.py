"""CLI: Run a back-test and print savings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config import PATHS
from src.models.back_tester import run_backtest
from src.utils.lkr import format_lkr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--holdout-days", type=int, default=30)
    args = p.parse_args()

    daily = pd.read_parquet(PATHS.data_processed / "daily_features.parquet")
    hourly = pd.read_parquet(PATHS.data_processed / "hourly_features.parquet")
    res = run_backtest(daily, hourly, args.holdout_days)
    print(f"Holdout: {res.holdout_days} days")
    print("Metrics:", res.metrics)
    print(f"Naive over-prep cost:    {format_lkr(res.savings['naive_waste_lkr'])}")
    print(f"CurryCast over-prep cost: {format_lkr(res.savings['smart_waste_lkr'])}")
    print(f"--> Savings: {format_lkr(res.savings['savings_lkr'])}")


if __name__ == "__main__":
    main()
