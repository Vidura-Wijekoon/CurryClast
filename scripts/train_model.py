"""CLI: Train CurryCast end-to-end."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.train_pipeline import run_training


def main():
    p = argparse.ArgumentParser(description="Train the CurryCast forecaster.")
    p.add_argument("--profile", default="cafe_mahaweli")
    args = p.parse_args()
    metadata = run_training(args.profile)
    print("\nTraining complete:")
    for k, v in metadata.items():
        print(f"  {k:<18} {v}")


if __name__ == "__main__":
    main()
