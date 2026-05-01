"""CurryCast — Streamlit dashboard entry point.

Run with:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `src` importable when running streamlit from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.config import SETTINGS

st.set_page_config(
    page_title="CurryCast",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
      .big-title { font-size: 36px; font-weight: 800; margin-bottom: 0; }
      .sub-title { color: #777; margin-top: 0; }
      .metric-card {
        background: #fff8f0; border: 1px solid #ffd9a8;
        border-radius: 10px; padding: 16px; text-align: center;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="big-title">🍛 CurryCast</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="sub-title">Demand &amp; Buffet Forecasting Engine · '
    f'<b>{SETTINGS["restaurant"]["name"]}</b> · {SETTINGS["restaurant"]["city"]}</p>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Welcome page content
# ---------------------------------------------------------------------------

st.markdown(
    """
    ### Welcome 🌴

    CurryCast turns your messy POS data, the weather, the poya calendar, and
    Sri Lanka's tourist season into a **kitchen prep list you can hand to the chef**.

    Use the navigation on the left:

    - **📅 Seven-Day Forecast** — covers per day with confidence band.
    - **🍛 Tomorrow's Prep List** — exactly how many kg of dhal, how many portions of fish ambul thiyal.
    - **🌧️ Weather Impact** — "Rain on Friday → shift 8 kg of grilled to soups."
    - **📊 Backtest Savings** — *"If you'd used CurryCast last month, you'd have saved LKR 312,400."*

    ---

    #### Quick start
    ```bash
    python scripts/generate_synthetic_data.py
    python scripts/train_model.py
    streamlit run dashboard/app.py
    ```
    """
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        '<div class="metric-card"><b>Cost reduction</b><br><span style="font-size:24px;color:#ea580c;">3–6%</span><br>of food spend</div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="metric-card"><b>Monthly savings</b><br><span style="font-size:24px;color:#ea580c;">LKR 180–360k</span><br>typical mid-size</div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="metric-card"><b>Payback</b><br><span style="font-size:24px;color:#ea580c;">3–4 months</span><br>after deployment</div>',
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        '<div class="metric-card"><b>Waste cut</b><br><span style="font-size:24px;color:#ea580c;">20–40%</span><br>buffet operators</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption(
    "Built for Sri Lankan restaurants. Knows about poya · perahera · payday · "
    "monsoon · cricket fixtures · tourist arrivals."
)
