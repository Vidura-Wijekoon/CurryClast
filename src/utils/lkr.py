"""LKR currency formatting helpers."""

from __future__ import annotations


def format_lkr(amount: float, *, with_symbol: bool = True) -> str:
    """Format LKR amount with thousand separators.

    >>> format_lkr(312_400)
    'LKR 312,400'
    >>> format_lkr(312_400.5, with_symbol=False)
    '312,400.50'
    """
    if amount == int(amount):
        body = f"{int(amount):,}"
    else:
        body = f"{amount:,.2f}"
    return f"LKR {body}" if with_symbol else body


def lkr_short(amount: float) -> str:
    """Short form: 'LKR 312k', 'LKR 1.2M'."""
    if abs(amount) >= 1_000_000:
        return f"LKR {amount/1_000_000:.1f}M"
    if abs(amount) >= 1_000:
        return f"LKR {amount/1_000:.0f}k"
    return f"LKR {amount:.0f}"
