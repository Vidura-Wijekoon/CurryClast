"""Backtest Savings — the pitch slide.

Replay the holdout period and compute "you would have saved LKR X".
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import PATHS
from src.models.back_tester import run_backtest
from src.utils.lkr import format_lkr, lkr_short

st.set_page_config(page_title="Backtest Savings · CurryCast", page_icon="📊", layout="wide")
st.title("📊 Backtest Savings")
st.markdown(
    "*If you'd been using CurryCast for the last N days, here's what you would have saved.*"
)

holdout = st.slider("Holdout period (days)", min_value=14, max_value=60, value=30, step=1)
run = st.button("Run backtest", type="primary")


@st.cache_data
def _load_features():
    daily = pd.read_parquet(PATHS.data_processed / "daily_features.parquet")
    hourly = pd.read_parquet(PATHS.data_processed / "hourly_features.parquet")
    return daily, hourly


if run:
    try:
        daily, hourly = _load_features()
        with st.spinner("Replaying history…"):
            result = run_backtest(daily, hourly, holdout_days=holdout)

        savings = result.savings
        metrics = result.metrics

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("LKR saved (last %d days)" % holdout, lkr_short(savings["savings_lkr"]))
            st.caption(format_lkr(savings["savings_lkr"]))
        with col2:
            st.metric("Naive over-prep (cost)", lkr_short(savings["naive_waste_lkr"]))
            st.caption("Your current 'last week + 30%' approach")
        with col3:
            st.metric("CurryCast over-prep (cost)", lkr_short(savings["smart_waste_lkr"]))
            st.caption("With CurryCast smart prep")

        st.markdown("---")

        st.subheader("Forecast accuracy")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("WAPE",  f"{metrics['wape']*100:.1f}%")
        m_col2.metric("MAPE",  f"{metrics['mape']*100:.1f}%")
        m_col3.metric("RMSE",  f"{metrics['rmse']:.1f}")
        m_col4.metric("Stockout rate", f"{metrics['stockout_rate']*100:.1f}%")

        st.markdown("---")
        st.subheader("Actual vs predicted (per item)")
        avp = result.actual_vs_pred.copy()
        per_item = (
            avp.groupby("item_canonical")
            .agg(actual=("actual", "sum"), predicted=("predicted", "sum"))
            .reset_index()
            .sort_values("actual", ascending=False)
            .head(15)
        )
        fig = px.bar(
            per_item.melt(id_vars="item_canonical",
                          value_vars=["actual", "predicted"],
                          var_name="kind", value_name="qty"),
            x="item_canonical", y="qty", color="kind", barmode="group",
            color_discrete_map={"actual": "#9ca3af", "predicted": "#ea580c"},
        )
        fig.update_layout(height=400, xaxis_title="", yaxis_title="Total qty (holdout)",
                          legend_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Daily cumulative savings")
        avp["date"] = pd.to_datetime(avp["date"])
        avp["over_prep_naive"] = (avp["actual"].rolling(7, min_periods=1).mean() * 1.30 - avp["actual"]).clip(lower=0)
        avp["over_prep_smart"] = (avp["predicted"] * 1.05 - avp["actual"]).clip(lower=0)
        daily_save = (
            avp.groupby("date")
            .agg(naive=("over_prep_naive", "sum"), smart=("over_prep_smart", "sum"))
            .assign(savings_units=lambda d: d["naive"] - d["smart"])
            .reset_index()
        )
        daily_save["savings_lkr"] = daily_save["savings_units"] * 350  # avg cost/unit
        daily_save["cumulative_lkr"] = daily_save["savings_lkr"].cumsum()
        fig2 = px.area(
            daily_save, x="date", y="cumulative_lkr",
            color_discrete_sequence=["#ea580c"],
        )
        fig2.update_layout(height=380, yaxis_title="Cumulative savings (LKR)",
                           xaxis_title="", plot_bgcolor="#fffaf3")
        st.plotly_chart(fig2, use_container_width=True)

        st.success(
            f"📣  **The Pitch:** Across the last {holdout} days, "
            f"CurryCast would have saved {format_lkr(savings['savings_lkr'])} "
            f"versus 'gut-feel' prep — at a forecast accuracy of WAPE {metrics['wape']*100:.1f}%."
        )
    except FileNotFoundError:
        st.error("No processed features found. Run `python scripts/train_model.py` first.")
    except Exception as e:
        st.exception(e)
else:
    st.info("Pick a holdout period and click **Run backtest**.")
