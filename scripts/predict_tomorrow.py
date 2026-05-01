"""CLI: Predict tomorrow's prep list and print it.

Run nightly via cron at 22:00 Asia/Colombo:

    0 22 * * * cd /opt/currycast && python scripts/predict_tomorrow.py >> logs/predict.log 2>&1
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.pipeline.predict_pipeline import predict_next_n_days


def main():
    out = predict_next_n_days(7)
    print("=" * 70)
    print("CurryCast — 7-day forecast")
    print("=" * 70)
    df = out["daily_forecast"].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%a %d %b")
    df["yhat"] = df["yhat"].round(0).astype(int)
    df["yhat_lower"] = df["yhat_lower"].round(0).astype(int)
    df["yhat_upper"] = df["yhat_upper"].round(0).astype(int)
    print(df.to_string(index=False))

    print("\n" + "=" * 70)
    print("Tomorrow's prep list")
    print("=" * 70)
    prep = out["prep_list"].copy()
    tomorrow = pd.to_datetime(prep["date"]).min()
    show = prep[pd.to_datetime(prep["date"]) == tomorrow][
        ["item_canonical", "prep_qty", "unit"]
    ].sort_values("prep_qty", ascending=False)
    print(show.to_string(index=False))


if __name__ == "__main__":
    main()
