"""Quick smoke tests on the modeling layer."""

import numpy as np
import pandas as pd

from src.models.buffet_translator import BuffetTranslator
from src.models.model_evaluator import wape, mape, rmse, stockout_rate


def test_metrics_sanity():
    y = np.array([10, 20, 30, 40])
    yhat = y.copy()
    assert wape(y, yhat) == 0.0
    assert rmse(y, yhat) == 0.0
    assert mape(y, yhat) == 0.0
    assert stockout_rate(y, yhat) == 0.0


def test_metrics_with_error():
    y = np.array([10.0, 20.0, 30.0])
    yhat = np.array([12.0, 18.0, 33.0])
    assert wape(y, yhat) > 0
    assert mape(y, yhat) > 0


def test_buffet_translator_basic():
    bt = BuffetTranslator(
        consumption_ratios={"rice": 0.18, "dhal_curry": 0.10},
        shrinkage_factor=1.05,
        min_prep=0.5,
    )
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2026-05-02", "2026-05-03"]),
        "yhat": [120.0, 80.0],
    })
    prep = bt.translate(daily)
    assert set(prep["item_canonical"]) == {"rice", "dhal_curry"}
    rice_d1 = prep[(prep["item_canonical"] == "rice") &
                   (prep["date"] == pd.Timestamp("2026-05-02"))]["prep_qty"].iloc[0]
    assert abs(rice_d1 - round(120 * 0.18 * 1.05, 2)) < 0.05


def test_buffet_weather_adjust_increases_kottu_on_rain():
    bt = BuffetTranslator(
        consumption_ratios={"chicken_kottu": 0.25},
        shrinkage_factor=1.0, min_prep=0.0,
    )
    df = pd.DataFrame({
        "date": pd.to_datetime(["2026-05-02"]),
        "yhat": [100.0],
    })
    base = bt.translate(df)
    weather = pd.DataFrame({
        "date": pd.to_datetime(["2026-05-02"]),
        "rain_mm": [12.0], "temp_c": [27.0], "is_rainy": [True],
    })
    adj = bt.adjust_for_weather(base, weather)
    assert adj["prep_qty"].iloc[0] > base["prep_qty"].iloc[0]
