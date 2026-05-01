"""Event-based features — perahera, festivals, cricket, conferences."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.data_generator import EVENTS


def add_event_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out["is_event_day"] = 0
    out["event_multiplier"] = 1.0
    out["event_name"] = None
    out["is_perahera"] = 0
    out["is_kandy_event"] = 0
    for ev in EVENTS:
        # Tuple: (start, end, name, multiplier, kandy_only)
        start, end, name, mult = ev[0], ev[1], ev[2], ev[3]
        kandy_only = ev[4] if len(ev) > 4 else False
        s = pd.Timestamp(datetime.strptime(start, "%Y-%m-%d"))
        e = pd.Timestamp(datetime.strptime(end, "%Y-%m-%d"))
        mask = (out[date_col] >= s) & (out[date_col] <= e)
        out.loc[mask, "is_event_day"] = 1
        out.loc[mask, "event_multiplier"] = mult
        out.loc[mask, "event_name"] = name
        if "Perahera" in name:
            out.loc[mask, "is_perahera"] = 1
        if kandy_only:
            out.loc[mask, "is_kandy_event"] = 1
    return out
