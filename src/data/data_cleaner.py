"""SKU normalization for messy POS data.

Sri Lankan POS systems contain wildly inconsistent item names:
"Kottu", "kothu", "chk kottu R", "kotu chiken", "Chicken Kottu Roti".
We normalize them to a canonical key using a fuzzy lookup table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


CANONICAL_SKUS: dict[str, list[str]] = {
    "rice":              ["rice", "white rice", "basmati rice", "red rice", "kekulu rice"],
    "dhal_curry":        ["dhal", "dhal curry", "parippu", "dal", "lentil curry"],
    "pol_sambol":        ["pol sambol", "polsambol", "coconut sambol", "pol sambal"],
    "fish_ambul_thiyal": [
        "fish ambul thiyal", "ambul thiyal", "ambulthiyal",
        "fish ambul", "fish curry sour", "ambul fish",
    ],
    "chicken_curry":     ["chicken curry", "chk curry", "chicken kari"],
    "chicken_kottu": [
        "chicken kottu", "chk kottu", "chicken kothu",
        "chiken kottu", "kottu chicken", "chicken kottu roti",
        "kotu chiken", "chk kotu", "chicken kottu r",
    ],
    "cheese_kottu":      ["cheese kottu", "chse kottu", "cheese kothu"],
    "egg_kottu":         ["egg kottu", "egg kothu", "egg kotu"],
    "string_hoppers": [
        "string hoppers", "stringhoppers", "idiyappam",
        "string hopper", "indi appa",
    ],
    "egg_hopper":        ["egg hopper", "egg appa", "bittara appa", "appa egg"],
    "devilled_chicken": [
        "devilled chicken", "devil chicken", "deviled chicken",
        "chicken devil", "devilled chk",
    ],
    "cashew_curry":      ["cashew curry", "cadju curry", "cashew nut curry"],
    "brinjal_moju":      ["brinjal moju", "brinjol moju", "wambatu moju", "eggplant moju"],
    "seer_fish_curry":   ["seer fish curry", "thora curry", "seer curry"],
    # Kandy / heritage
    "polos_curry":       ["polos curry", "polos", "jackfruit curry", "young jackfruit curry"],
    "kandyan_beef_curry":["kandyan beef curry", "kandyan beef", "beef curry kandy",
                          "kandy beef", "kandy beef curry"],
    "lamprais":          ["lamprais", "lamprice", "lump rice", "lamprice burgher"],
    "milk_rice":         ["milk rice", "kiribath", "kiri bath", "kiribath plate"],
    "watalappan":        ["watalappan", "watalapan", "wattalappam", "wattalappan"],
    "love_cake":         ["love cake", "lovecake", "burgher love cake"],
    # Asian fusion
    "nasi_goreng":       ["nasi goreng", "nasi", "indonesian fried rice", "nasigoreng"],
    "pad_thai":          ["pad thai", "phad thai", "thai noodles", "padthai"],
    "thai_red_curry":    ["thai red curry", "red curry", "thai red"],
    "thai_green_curry":  ["thai green curry", "green curry", "thai green"],
    "chinese_fried_rice":["chinese fried rice", "cfr", "fried rice", "egg fried rice",
                          "chicken fried rice", "ch fried rice"],
    # Drinks
    "king_coconut":      ["king coconut", "thambili", "kingcoconut"],
    "ceylon_tea":        ["ceylon tea", "tea", "plain tea", "milk tea", "kandy tea",
                          "highgrown tea", "uva tea"],
    "lion_lager":        ["lion lager", "lion beer", "lion"],
    "faluda":            ["faluda", "falooda"],
}

_ALIAS_INDEX: dict[str, str] = {
    alias: canonical
    for canonical, aliases in CANONICAL_SKUS.items()
    for alias in aliases
}
_ALL_ALIASES: list[str] = list(_ALIAS_INDEX.keys())

_CLEAN_RE = re.compile(r"[^a-z0-9 ]+")


def _normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = _CLEAN_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\b(r|l|reg|regular|large|sm|small|md|medium)\b$", "", s).strip()
    return s


@dataclass
class SKUNormalizer:
    cutoff: int = 85
    unmapped_log: list[str] = field(default_factory=list)

    def normalize(self, item: str) -> str | None:
        cleaned = _normalize_text(item)
        if not cleaned:
            return None
        if cleaned in _ALIAS_INDEX:
            return _ALIAS_INDEX[cleaned]
        if HAS_RAPIDFUZZ:
            match = process.extractOne(
                cleaned, _ALL_ALIASES, scorer=fuzz.partial_ratio
            )
            if match and match[1] >= self.cutoff:
                return _ALIAS_INDEX[match[0]]
        else:
            for alias, canonical in _ALIAS_INDEX.items():
                if alias in cleaned or cleaned in alias:
                    return canonical
        self.unmapped_log.append(item)
        return None

    def normalize_series(self, items: pd.Series) -> pd.Series:
        return items.map(self.normalize)

    def write_unmapped(self, path: str | Path) -> None:
        if not self.unmapped_log:
            return
        s = pd.Series(self.unmapped_log)
        df = pd.DataFrame({"raw_item": s.value_counts().index,
                           "count": s.value_counts().values})
        df.to_csv(path, index=False)


def normalize_dataframe(df: pd.DataFrame, item_col: str = "item_name") -> pd.DataFrame:
    norm = SKUNormalizer()
    out = df.copy()
    out["item_canonical"] = norm.normalize_series(out[item_col])
    return out


def known_canonicals() -> Iterable[str]:
    return CANONICAL_SKUS.keys()
