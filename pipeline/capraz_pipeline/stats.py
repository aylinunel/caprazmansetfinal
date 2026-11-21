"""Shared rate statistics: Mantel-Haenszel risk ratio, Cochran-Mantel-Haenszel test, Benjamini-Hochberg q.

Strata are (a, n1, b, n0) = (outlet yes, outlet total, others yes, others total).
"""
from __future__ import annotations

import math

from scipy.stats import chi2


def bh_q(ps: list[float]) -> list[float]:
    """Benjamini-Hochberg q-values, in the order of the input."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    qs = [0.0] * m
    q_prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        q_prev = min(q_prev, ps[i] * m / rank)
        qs[i] = q_prev
    return qs


def mh_rr(strata):
    """Mantel-Haenszel common risk ratio with a Greenland-Robins 95% interval: (rr, lo, hi), None where undefined."""
    num = den = var_num = 0.0
    for a, n1, b, n0 in strata:
        if n1 == 0 or n0 == 0:
            continue
        n = n1 + n0
        num += a * n0 / n
        den += b * n1 / n
        var_num += (n1 * n0 * (a + b) - a * b * n) / (n * n)
    if num == 0:
        return (0.0, None, None)
    if den == 0:
        return (None, None, None)
    rr = num / den
    se = math.sqrt(max(var_num / (num * den), 0.0))
    return (rr, math.exp(math.log(rr) - 1.96 * se), math.exp(math.log(rr) + 1.96 * se))


def cmh_p(strata):
    """Cochran-Mantel-Haenszel p-value (continuity-corrected, 1 df); None when the variance is zero."""
    sa = se = sv = 0.0
    for a, n1, b, n0 in strata:
        n = n1 + n0
        if n < 2:
            continue
        m1 = a + b
        sa += a
        se += n1 * m1 / n
        sv += n1 * n0 * m1 * (n - m1) / (n * n * (n - 1))
    if sv == 0:
        return None
    return float(chi2.sf(max(abs(sa - se) - 0.5, 0) ** 2 / sv, 1))
