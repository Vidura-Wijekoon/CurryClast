"""CLI: Generate synthetic Café Mahaweli data."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.data_generator import generate_and_save


def main():
    p = argparse.ArgumentParser(description="Generate synthetic POS data.")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--start-date", default="2025-04-01")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    paths = generate_and_save(months=args.months, start_date=start, seed=args.seed)
    print("\nGenerated synthetic dataset:")
    for k, v in paths.items():
        print(f"  {k:<14} → {v}")


if __name__ == "__main__":
    main()
