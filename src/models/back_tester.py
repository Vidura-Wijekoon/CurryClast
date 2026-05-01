"""Back-test runner for the pitch slide.

Replays the last N days: trains on everything earlier, predicts the holdout,
compares against actuals, and reports LKR waste savings.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.models.demand_forecaster import DemandForecaster
from src.models.model_evaluator import evaluate, waste_savings_lkr
from src.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class BackTestResult:
    holdout_days: int
    metrics: dict
    savings: dict
    actual_vs_pred: pd.DataFrame


def run_backtest(
    daily_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    holdout_days: int = 30,
) -> BackTestResult:
    """Train on history, predict holdout, return metrics + savings."""
    daily_df = daily_df.sort_values("date").copy()
    hourly_df = hourly_df.sort_values(["date", "hour"]).copy()

    cutoff = daily_df["date"].max() - pd.Timedelta(days=holdout_days)
    train_daily = daily_df[daily_df["date"] <= cutoff]
    test_daily = daily_df[daily_df["date"] > cutoff]
    train_hourly = hourly_df[hourly_df["date"] <= cutoff]
    test_hourly = hourly_df[hourly_df["date"] > cutoff]

    log.info("Backtest: train %d days, test %d days",
             len(train_daily), len(test_daily))

    fc = DemandForecaster()
    fc.fit(train_daily, train_hourly)

    # Predict
    pred_hourly = fc.predict_hourly(test_hourly)
    metrics = evaluate(pred_hourly["quantity"], pred_hourly["yhat"])
    savings = waste_savings_lkr(
        actual=test_hourly[["date", "hour", "item_canonical", "quantity"]],
        forecast=pred_hourly[["date", "hour", "item_canonical", "yhat"]],
    )

    avp = pred_hourly[["date", "hour", "item_canonical", "quantity", "yhat"]].copy()
    avp.columns = ["date", "hour", "item_canonical", "actual", "predicted"]

    return BackTestResult(
        holdout_days=holdout_days,
        metrics=metrics,
        savings=savings,
        actual_vs_pred=avp,
    )
