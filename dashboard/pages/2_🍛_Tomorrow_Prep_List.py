"""Tomorrow's prep list — printable kg/portion view."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.pipeline.predict_pipeline import predict_next_n_days

st.set_page_config(page_title="Tomorrow's Prep · CurryCast", page_icon="🍛", layout="wide")
st.title("🍛 Tomorrow's Prep List")
st.markdown("Hand this to the chef tonight at 10 PM. Quantities include a 5% buffer.")

# Display label overrides (English / Sinhala / Tamil)
ITEM_LABELS = {
    "rice":              ("Rice / බත් / சாதம்", "🍚"),
    "dhal_curry":        ("Dhal Curry / පරිප්පු", "🟡"),
    "pol_sambol":        ("Pol Sambol / පොල් සම්බෝල", "🥥"),
    "fish_ambul_thiyal": ("Fish Ambul Thiyal", "🐟"),
    "chicken_curry":     ("Chicken Curry / කුකුල් මස් කරිය", "🍗"),
    "chicken_kottu":     ("Chicken Kottu / කොත්තු රොටී", "🥘"),
    "cheese_kottu":      ("Cheese Kottu", "🧀"),
    "egg_kottu":         ("Egg Kottu", "🥚"),
    "string_hoppers":    ("String Hoppers / ඉඳිආප්ප", "🍜"),
    "egg_hopper":        ("Egg Hopper / බිත්තර ආප්ප", "🍳"),
    "devilled_chicken":  ("Devilled Chicken", "🌶️"),
    "cashew_curry":      ("Cashew Curry / කජු කරිය", "🥜"),
    "brinjal_moju":      ("Brinjal Moju / වම්බටු මෝජු", "🍆"),
    "seer_fish_curry":   ("Seer Fish Curry", "🐠"),
    "king_coconut":      ("King Coconut / තැඹිලි", "🥥"),
    "lion_lager":        ("Lion Lager", "🍺"),
    "faluda":            ("Faluda", "🥤"),
}


@st.cache_data(ttl=300)
def _load():
    return predict_next_n_days(7)


try:
    out = _load()
    prep = out["prep_list"].copy()
    prep["date"] = pd.to_datetime(prep["date"])

    dates = sorted(prep["date"].unique())
    options = [d.strftime("%A %d %b %Y") for d in dates]
    sel = st.selectbox("Pick a day:", options, index=0)
    sel_date = dates[options.index(sel)]
    today = prep[prep["date"] == sel_date].copy()

    daily_fc = out["daily_forecast"]
    daily_fc["date"] = pd.to_datetime(daily_fc["date"])
    expected_covers = daily_fc.loc[daily_fc["date"] == sel_date, "yhat"].iloc[0]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Expected covers", f"{expected_covers:.0f}")
        st.caption("Includes confidence buffer.")

    # Sort by qty for visual prominence
    today = today.sort_values("prep_qty", ascending=False).reset_index(drop=True)

    # Card grid
    cols_per_row = 3
    rows = [today.iloc[i:i + cols_per_row] for i in range(0, len(today), cols_per_row)]
    for chunk in rows:
        cols = st.columns(cols_per_row)
        for i, (_, row) in enumerate(chunk.iterrows()):
            label, icon = ITEM_LABELS.get(row["item_canonical"], (row["item_canonical"], "🍽️"))
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="background:#fff8f0;border:1px solid #ffd9a8;
                                border-radius:10px;padding:14px;text-align:center;">
                      <div style="font-size:28px">{icon}</div>
                      <div style="font-weight:700;margin-top:4px">{label}</div>
                      <div style="font-size:26px;color:#ea580c;margin-top:6px">
                        {row['prep_qty']:.1f} {row['unit']}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with st.expander("Print-friendly table"):
        printable = today[["item_canonical", "prep_qty", "unit"]].copy()
        printable["item"] = printable["item_canonical"].map(
            lambda k: ITEM_LABELS.get(k, (k,))[0]
        )
        printable = printable[["item", "prep_qty", "unit"]]
        printable.columns = ["Item", "Qty", "Unit"]
        st.dataframe(printable, use_container_width=True, hide_index=True)
        csv = printable.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv,
                           file_name=f"prep_{sel_date.strftime('%Y%m%d')}.csv",
                           mime="text/csv")
except FileNotFoundError:
    st.error("No trained model found. Please run `python scripts/train_model.py` first.")
except Exception as e:
    st.exception(e)
