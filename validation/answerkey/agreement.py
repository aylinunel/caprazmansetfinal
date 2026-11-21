"""Inter-coder agreement: nominal Krippendorff's alpha and raw percent agreement."""
from collections import Counter
from typing import Optional, Sequence


def _coded(unit: Sequence[Optional[str]]) -> list[str]:
    return [v for v in unit if v is not None]


def krippendorff_alpha(units: Sequence[Sequence[Optional[str]]]) -> Optional[float]:
    """Nominal alpha over units (one item's values across coders, None = not coded).

    Units with fewer than 2 values are ignored. Returns None when there are fewer
    than 2 pairable values or no expected disagreement (only one value used).
    """
    o = Counter()  # coincidence matrix, ordered pairs of values
    for unit in units:
        vals = _coded(unit)
        m = len(vals)
        if m < 2:
            continue
        for i, a in enumerate(vals):
            for j, b in enumerate(vals):
                if i != j:
                    o[(a, b)] += 1 / (m - 1)
    n = sum(o.values())
    if n < 2:
        return None
    totals = Counter()
    for (a, _), w in o.items():
        totals[a] += w
    d_o = sum(w for (a, b), w in o.items() if a != b)
    d_e = sum(totals[a] * totals[b] for a in totals for b in totals if a != b) / (n - 1)
    if d_e == 0:
        return None
    return 1 - d_o / d_e


def percent_agreement(units: Sequence[Sequence[Optional[str]]]) -> Optional[float]:
    """Share of units with >= 2 values whose values are all equal; None if no such unit."""
    multi = [v for v in map(_coded, units) if len(v) >= 2]
    if not multi:
        return None
    return sum(len(set(v)) == 1 for v in multi) / len(multi)
