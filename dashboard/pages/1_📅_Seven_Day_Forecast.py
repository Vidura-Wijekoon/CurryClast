"""7-day forecast view."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import PATHS
from src.pipeline.predict_pipeline import predict_next_n_days

st.set_page_config(page_title="Seven-Day Forecast · CurryCast", page_icon="📅", layout="wide")
st.title("📅 Seven-Day Forecast")

st.markdown("Daily covers expected at the restaurant. Shaded band = 80% confidence interval.")

@st.cache_data(ttl=300)
def _load():
    out = predict_next_n_days(7)
    return out


try:
    out = _load()
    daily = out["daily_forecast"].copy()
    daily["date"] = pd.to_datetime(daily["date"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg covers / day (next 7d)", f"{daily['yhat'].mean():.0f}")
    with col2:
        st.metric("Peak day", f"{daily.loc[daily['yhat'].idxmax(), 'date'].strftime('%a %d %b')}")
    with col3:
        st.metric("Lowest day", f"{daily.loc[daily['yhat'].idxmin(), 'date'].strftime('%a %d %b')}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["yhat_upper"],
        line=dict(color="rgba(255,122,24,0)"),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["yhat_lower"],
        line=dict(color="rgba(255,122,24,0)"),
        fill="tonexty", fillcolor="rgba(255,122,24,0.20)",
        name="80% interval",
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["yhat"],
        mode="lines+markers", name="Forecast covers",
        line=dict(color="#ea580c", width=3),
        marker=dict(size=10),
    ))
    fig.update_layout(
        height=420, margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title="", yaxis_title="Covers",
        plot_bgcolor="#fffaf3",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daily numbers")
    show = daily.copy()
    show["date"] = show["date"].dt.strftime("%a %d %b %Y")
    show["yhat"] = show["yhat"].round(0).astype(int)
    show["yhat_lower"] = show["yhat_lower"].round(0).astype(int)
    show["yhat_upper"] = show["yhat_upper"].round(0).astype(int)
    show.columns = ["Date", "Forecast", "Lower (80%)", "Upper (80%)"]
    st.dataframe(show, use_container_width=True, hide_index=True)
except FileNotFoundError:
    st.error("No trained model found. Please run `python scripts/train_model.py` first.")
except Exception as e:
    st.exception(e)
