"""Forecast evaluation metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def wape(y_true, y_pred) -> float:
    """Weighted Absolute Percentage Error — robust to zeros."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.abs(y_true).sum()
    if denom == 0:
        return float("nan")
    return float(np.abs(y_true - y_pred).sum() / denom)


def mape(y_true, y_pred, eps=1e-3) -> float:
    """Mean Absolute Percentage Error (zeros clipped)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), eps))))


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def stockout_rate(y_true, y_pred) -> float:
    """Fraction of slots where forecast underestimates demand."""
    return float(np.mean(np.asarray(y_pred) < np.asarray(y_true)))


def waste_savings_lkr(actual, forecast, cost_per_unit=None,
                     naive_buffer=1.30, smart_buffer=1.05):
    """Compare 'last week's gut feel' baseline vs CurryCast prep waste."""
    cost_per_unit = cost_per_unit or {}
    df = actual.merge(forecast, on=["date", "hour", "item_canonical"], how="inner")
    if df.empty:
        return {"naive_waste_lkr": 0.0, "smart_waste_lkr": 0.0, "savings_lkr": 0.0}
    df = df.sort_values(["item_canonical", "date", "hour"]).reset_index(drop=True)
    df["naive_prep"] = (
        df.groupby("item_canonical")["quantity"]
          .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
        * naive_buffer
    )
    df["smart_prep"] = df["yhat"] * smart_buffer
    df["unit_cost"] = df["item_canonical"].map(cost_per_unit).fillna(350.0)
    df["naive_waste"] = (df["naive_prep"] - df["quantity"]).clip(lower=0)
    df["smart_waste"] = (df["smart_prep"] - df["quantity"]).clip(lower=0)
    naive_total = float((df["naive_waste"] * df["unit_cost"]).sum())
    smart_total = float((df["smart_waste"] * df["unit_cost"]).sum())
    return {
        "naive_waste_lkr": naive_total,
        "smart_waste_lkr": smart_total,
        "savings_lkr": max(0.0, naive_total - smart_total),
    }


def evaluate(actual, predicted) -> dict:
    """Compute the standard metric bundle."""
    return {
        "wape": wape(actual.values, predicted.values),
        "mape": mape(actual.values, predicted.values),
        "rmse": rmse(actual.values, predicted.values),
        "stockout_rate": stockout_rate(actual.values, predicted.values),
    }
