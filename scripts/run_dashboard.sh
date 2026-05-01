#!/usr/bin/env bash
# Launch CurryCast Streamlit dashboard
set -euo pipefail
cd "$(dirname "$0")/.."
streamlit run dashboard/app.py "$@"
