"""Weather Impact panel — show how rain/heat shifts tomorrow's prep."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.models.buffet_translator import BuffetTranslator
from src.pipeline.predict_pipeline import predict_next_n_days

st.set_page_config(page_title="Weather Impact · CurryCast", page_icon="🌧️", layout="wide")
st.title("🌧️ Weather Impact")
st.markdown("How tomorrow's weather is reshaping the prep list.")


@st.cache_data(ttl=300)
def _load():
    return predict_next_n_days(7)


try:
    out = _load()
    weather = out["weather_future"].copy()
    weather["date"] = pd.to_datetime(weather["date"])

    # Display weather strip
    st.subheader("7-day weather outlook (Colombo)")
    cols = st.columns(len(weather))
    for i, (_, w) in enumerate(weather.iterrows()):
        emoji = "🌧️" if w["rain_mm"] > 5 else ("🌦️" if w["rain_mm"] > 1 else "☀️")
        with cols[i]:
            st.markdown(
                f"""<div style="text-align:center; padding:8px;
                                background:#f0f9ff; border-radius:8px;">
                <b>{w['date'].strftime('%a')}</b><br>
                <span style="font-size:32px">{emoji}</span><br>
                {w['temp_c']:.1f}°C<br>
                <small>Rain: {w['rain_mm']:.1f} mm</small>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Compare baseline prep (no weather adjust) vs weather-adjusted
    base_prep = out["prep_list"].copy()
    bt = BuffetTranslator()
    daily_fc = out["daily_forecast"].copy()
    naive_prep = bt.translate(daily_fc)

    base = naive_prep.copy()
    base["date"] = pd.to_datetime(base["date"])
    adj = base_prep.copy()
    adj["date"] = pd.to_datetime(adj["date"])
    merged = base.merge(
        adj,
        on=["date", "item_canonical", "unit"],
        suffixes=("_base", "_adj"),
    )
    merged["delta"] = merged["prep_qty_adj"] - merged["prep_qty_base"]
    merged["pct"] = (merged["delta"] / merged["prep_qty_base"]) * 100

    # Build a few headline insights
    st.subheader("📣 Today's adjustments")
    big_changes = merged[merged["pct"].abs() > 4].sort_values("pct", ascending=False)
    if big_changes.empty:
        st.info("Mild weather ahead — no major prep changes recommended.")
    else:
        for _, row in big_changes.head(8).iterrows():
            day = row["date"].strftime("%A")
            sign = "↑" if row["delta"] > 0 else "↓"
            color = "#16a34a" if row["delta"] > 0 else "#dc2626"
            st.markdown(
                f"<div style='padding:8px 12px;margin:4px 0;border-left:4px solid {color};background:#fafafa;'>"
                f"<b>{day}</b> · <i>{row['item_canonical']}</i>: "
                f"<span style='color:{color};font-weight:700'>{sign} {abs(row['delta']):.1f} {row['unit']}</span> "
                f"({row['pct']:+.0f}%)"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("Full comparison")
    show = merged[["date", "item_canonical", "prep_qty_base", "prep_qty_adj", "unit", "delta", "pct"]].copy()
    show["date"] = show["date"].dt.strftime("%a %d %b")
    show.columns = ["Date", "Item", "Baseline", "Weather-adjusted", "Unit", "Δ", "Δ %"]
    st.dataframe(show, use_container_width=True, hide_index=True)
except FileNotFoundError:
    st.error("No trained model found. Please run `python scripts/train_model.py` first.")
except Exception as e:
    st.exception(e)
