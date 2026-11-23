"""Per-card statistics from editor reviews, and the gate that acts on them.

Precision here is "verify-pass precision": the reviewer saw the AI's finding first, which tends
to raise agreement. It is not accuracy, and it says nothing about findings the AI missed.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .labels import Label, latest


def wilson_lower(successes: int, n: int, z: float = 1.6449) -> float | None:
    """One-sided 95% lower bound of a proportion; None when nothing was reviewed."""
    if n == 0:
        return None
    p = successes / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def card_stats(labels: Sequence[Label]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for l in latest(labels):
        s = out.setdefault(l.card_id, {"reviewed": 0, "kept": 0, "rejected": 0, "audit_reviewed": 0,
                                       "audit_kept": 0, "by_tier": {}})
        kept = l.outcome != "rejected"   # corrected = the pattern was there, the wording needed fixing
        s["reviewed"] += 1
        s["kept"] += kept
        s["rejected"] += not kept
        t = s["by_tier"].setdefault(l.tier_at_review, {"reviewed": 0, "kept": 0})
        t["reviewed"] += 1
        t["kept"] += kept
        if l.audit and l.tier_at_review == "ai_confident":
            s["audit_reviewed"] += 1
            s["audit_kept"] += kept
    for s in out.values():
        s["precision"] = s["kept"] / s["reviewed"]
        s["lower"] = wilson_lower(s["kept"], s["reviewed"])
        s["audit_precision"] = s["audit_kept"] / s["audit_reviewed"] if s["audit_reviewed"] else None
    return out


def card_status(stats: dict[str, dict], gates: dict) -> dict[str, dict]:
    out = {}
    for card, s in stats.items():
        n, shown = s["reviewed"], f"{s['kept']}/{s['reviewed']} kept"
        if n < gates["hide_min_reviews"]:
            status, why = "unjudged", f"{shown}; fewer than {gates['hide_min_reviews']} reviews"
        elif s["precision"] < gates["hide_below_precision"]:
            status, why = "hidden", f"{shown}; verify-pass precision below {gates['hide_below_precision']}"
        elif n < gates["min_reviews_to_judge"]:
            status, why = "unjudged", f"{shown}; fewer than {gates['min_reviews_to_judge']} reviews"
        elif s["lower"] < gates["min_precision_lower_bound"]:
            status, why = "demoted", f"{shown}; lower bound {s['lower']:.2f} below {gates['min_precision_lower_bound']}"
        else:
            status, why = "eligible", f"{shown}; lower bound {s['lower']:.2f}"
        out[card] = {"status": status, "applied": bool(gates["agreed"]), "reasons": [why]}
    return out


STRICT = ("unjudged", "eligible", "demoted", "hidden")


def write_status(path: Path, measure: str, cards: dict[str, dict], agreed: bool, pack: str = "") -> None:
    """Replace only this measure's results in card_status.json; each card takes its strictest status across measures."""
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    by = old.get("by_measure") or ({old["measure"]: old.get("cards", {})} if old.get("measure") else {})
    by[measure] = cards
    merged = {}
    for m in by.values():
        for c, v in m.items():
            if c not in merged or STRICT.index(v["status"]) > STRICT.index(merged[c]["status"]):
                merged[c] = v
    out = {"pack_version": pack, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "agreed": agreed, "cards": merged, "by_measure": by}
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
