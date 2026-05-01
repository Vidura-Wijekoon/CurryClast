"""Synthetic data generator smoke tests."""

from datetime import date

from src.data.data_generator import CafeMahaweliGenerator


def test_generator_produces_data():
    gen = CafeMahaweliGenerator(start_date=date(2025, 4, 1), months=2, seed=1)
    out = gen.generate()
    assert "transactions" in out
    assert "weather" in out
    assert "daily_meta" in out
    assert len(out["transactions"]) > 100
    assert len(out["weather"]) > 50


def test_generator_marks_poya():
    gen = CafeMahaweliGenerator(start_date=date(2025, 4, 1), months=12, seed=1)
    out = gen.generate()
    meta = out["daily_meta"]
    assert meta["is_poya"].sum() >= 8  # at least 8 poya days in the year
