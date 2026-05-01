"""Centralized configuration loader for CurryCast.

Loads YAML configs (default + per-restaurant override) and exposes a singleton
`Settings` plus a `PATHS` namespace for canonical project paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT
    configs: Path = PROJECT_ROOT / "configs"
    profiles: Path = PROJECT_ROOT / "configs" / "restaurant_profiles"
    data_raw: Path = PROJECT_ROOT / "data" / "raw"
    data_processed: Path = PROJECT_ROOT / "data" / "processed"
    data_synthetic: Path = PROJECT_ROOT / "data" / "synthetic"
    data_models: Path = PROJECT_ROOT / "data" / "models"

    def ensure(self) -> None:
        for p in (
            self.data_raw,
            self.data_processed,
            self.data_synthetic,
            self.data_models,
        ):
            p.mkdir(parents=True, exist_ok=True)


PATHS = Paths()


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge `override` into `base` recursively (override wins)."""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(profile: str | None = None) -> dict[str, Any]:
    """Load the merged config for a given restaurant profile.

    Args:
        profile: Filename stem under ``configs/restaurant_profiles/``,
            e.g. ``"cafe_mahaweli"``. Falls back to the env var
            ``RESTAURANT_PROFILE`` and finally the default-only config.
    """
    default_path = PATHS.configs / "default.yaml"
    with default_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    profile = profile or os.getenv("RESTAURANT_PROFILE")
    if profile:
        prof_path = PATHS.profiles / f"{profile}.yaml"
        if prof_path.exists():
            with prof_path.open("r", encoding="utf-8") as f:
                cfg = _deep_merge(cfg, yaml.safe_load(f) or {})
        else:
            # Don't fail hard — log via print since logger may not be configured yet.
            print(f"[config] WARN: profile '{profile}' not found at {prof_path}")

    return cfg


# Convenience module-level singleton — defaults to kulture32 profile
SETTINGS: dict[str, Any] = load_config(os.getenv("RESTAURANT_PROFILE", "kulture32"))
