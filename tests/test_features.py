"""Feature engineering tests."""

import pandas as pd

from src.features.calendar_features import add_calendar_features, add_hour_features
from src.features.holiday_features import add_holiday_features
from src.features.weather_features import add_weather_features


def _daily_skeleton():
    dates = pd.date_range("2025-04-01", periods=30, freq="D")
    return pd.DataFrame({"date": dates, "covers": range(30)})


def test_calendar_features_present():
    df = add_calendar_features(_daily_skeleton())
    for col in ("dow", "month", "is_weekend", "dow_sin", "dow_cos", "month_sin"):
        assert col in df.columns


def test_holiday_features_flag_known_dates():
    df = pd.DataFrame({"date": pd.to_datetime(["2025-04-14", "2025-05-01", "2025-04-02"])})
    out = add_holiday_features(df)
    assert out.loc[0, "is_public_holiday"] == 1
    assert out.loc[1, "is_public_holiday"] == 1
    assert out.loc[2, "is_public_holiday"] == 0


def test_hour_features():
    df = pd.DataFrame({"hour": [12, 19, 22]})
    out = add_hour_features(df)
    assert (out["is_lunch"] == [1, 0, 0]).all()
    assert (out["is_dinner"] == [0, 1, 1]).all()


def test_weather_join():
    df = _daily_skeleton()
    weather = pd.DataFrame({
        "date": df["date"],
        "temp_c": 28.0, "humidity": 75.0, "rain_mm": 0.0, "is_rainy": False,
    })
    out = add_weather_features(df, weather)
    assert "temp_c" in out.columns
    assert "heat_index" in out.columns
