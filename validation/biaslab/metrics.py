"""Lab metrics with honest denominators.

A ratio with a zero denominator is None ("not estimable"), never 0 or 1. Intervals resample
families, because cases built from the same facts are not independent.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

_DECISIONS = {"supported", "contextual_effect", "not_supported"}
_POSITIVE = {"supported", "contextual_effect"}


@dataclass(frozen=True)
class Row:
    case: str
    family: str
    kind: str
    status: str
    acceptable: frozenset[str]
    forbidden: frozenset[str]
    span_ok: bool
    base_status: str | None = None   # status of the unperturbed case, for perturbed rows only


def ratio(n: int, d: int) -> float | None:
    return n / d if d else None


def _r(n: int, d: int) -> dict:
    return {"n": n, "d": d, "value": ratio(n, d)}


def summarize(rows: Sequence[Row]) -> dict:
    eligible = [r for r in rows if r.status != "ineligible"]
    positives = [r for r in eligible if r.kind == "positive"]
    controls = [r for r in eligible if r.kind != "positive"]
    hits = [r for r in positives if r.status in r.acceptable]
    predicted = [r for r in eligible if r.status in _POSITIVE]
    missing = [r for r in eligible if r.kind == "missing_context"]
    paired = [r for r in rows if r.base_status is not None and "error" not in (r.status, r.base_status)]
    return {
        "completion": _r(sum(r.status != "error" for r in rows), len(rows)),
        "eligible": _r(len(eligible), len(rows)),
        "decision_coverage": _r(sum(r.status in _DECISIONS for r in eligible), len(eligible)),
        "end_to_end_recall": _r(len(hits), len(positives)),
        "conditional_recall": _r(len(hits), sum(r.status in _DECISIONS for r in positives)),
        "strict_precision": _r(sum(r.kind == "positive" and r.span_ok for r in predicted), len(predicted)),
        "forbidden_rate": _r(sum(r.status in r.forbidden for r in controls),
                             sum(r.status in _DECISIONS for r in controls)),
        "unsupported_assertion_rate": _r(sum(r.status in r.forbidden for r in missing), len(missing)),
        "perturbation_consistency": _r(sum(r.status == r.base_status for r in paired), len(paired)),
        "counts_by_status": dict(Counter(r.status for r in rows)),
        "families": len({r.family for r in rows}),
    }


def paired_bootstrap(baseline: Sequence[Row], candidate: Sequence[Row], metric: str, *,
                     n_boot: int = 2000, seed: int = 0) -> dict:
    """Candidate minus baseline for one metric, with a family-level percentile interval."""
    if sorted(r.case for r in baseline) != sorted(r.case for r in candidate):
        raise ValueError("baseline and candidate must cover the same cases")

    def diff(b: Sequence[Row], c: Sequence[Row]) -> float | None:
        vb, vc = summarize(b)[metric]["value"], summarize(c)[metric]["value"]
        return None if vb is None or vc is None else vc - vb

    families = sorted({r.family for r in baseline})
    by_family = {f: ([r for r in baseline if r.family == f], [r for r in candidate if r.family == f])
                 for f in families}
    rng = random.Random(seed)
    draws, undefined = [], 0
    for _ in range(n_boot):
        picked = [by_family[rng.choice(families)] for _ in families]
        d = diff([r for b, _ in picked for r in b], [r for _, c in picked for r in c])
        if d is None:
            undefined += 1
        else:
            draws.append(d)
    usable = len(families) >= 10 and undefined / n_boot <= 0.05 and draws
    draws.sort()
    return {"metric": metric, "point": diff(baseline, candidate),
            "lo": draws[int(0.025 * (len(draws) - 1))] if usable else None,
            "hi": draws[int(0.975 * (len(draws) - 1))] if usable else None,
            "families": len(families), "n_boot": n_boot, "undefined_draws": undefined}
