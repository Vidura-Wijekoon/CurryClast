"""SKU normalization tests."""

import pandas as pd

from src.data.data_cleaner import SKUNormalizer, normalize_dataframe


def test_exact_alias_match():
    n = SKUNormalizer()
    assert n.normalize("Chicken Kottu") == "chicken_kottu"
    assert n.normalize("Pol Sambol") == "pol_sambol"


def test_misspellings_resolve():
    n = SKUNormalizer()
    assert n.normalize("kotu chiken") == "chicken_kottu"
    assert n.normalize("Chk Kottu R") == "chicken_kottu"
    assert n.normalize("Ambul Thiyal") == "fish_ambul_thiyal"


def test_unknown_returns_none():
    n = SKUNormalizer()
    assert n.normalize("XYZNOTAFOOD") is None
    assert "XYZNOTAFOOD" in n.unmapped_log


def test_normalize_dataframe_adds_column():
    df = pd.DataFrame({"item_name": ["Chicken Kottu", "Pol Sambol", "asdf"]})
    out = normalize_dataframe(df)
    assert "item_canonical" in out.columns
    assert out.loc[0, "item_canonical"] == "chicken_kottu"
    assert out.loc[1, "item_canonical"] == "pol_sambol"
