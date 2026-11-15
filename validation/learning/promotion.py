"""The gate a detector version (cards + prompts + settings) must pass before it replaces the current one.

Fail closed: a missing or not-estimable metric is a failure. One change per iteration; every decision
is appended to validation/reference/versions.jsonl, whether or not it promoted.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROMOTION_GATES = {
    "replay_reintroduced_absent":      ("max", 0),      # never confirm something a person rejected
    "replay_still_shown_absent_delta": ("max", 0),      # not more rejected findings raised than the current version
    "replay_lost_present_rate":        ("max", 0.05),   # keep what people verified or corrected
    "replay_error_rate":               ("max", 0.05),
    "lab_forbidden_rate":              ("max", 0.0),    # no forbidden answer on the lab's controls
    "run_completion":                  ("min", 0.95),
}


def assert_promotion_ready(metrics: dict[str, float | None]) -> None:
    missing = sorted(name for name in PROMOTION_GATES if metrics.get(name) is None)
    if missing:
        raise ValueError(f"promotion metrics missing or not estimable: {missing}")
    failures = {name: metrics[name] for name, (direction, threshold) in PROMOTION_GATES.items()
                if (direction == "min" and metrics[name] < threshold)
                or (direction == "max" and metrics[name] > threshold)}
    if failures:
        raise ValueError(f"promotion gates failed: {failures}")


def metrics_from(baseline_replay: dict, candidate_replay: dict, lab_candidate: dict, run_completion: float | None) -> dict:
    present = candidate_replay["kept_present"] + candidate_replay["lost_present"]
    scored = candidate_replay["scored"]
    return {
        "replay_reintroduced_absent": candidate_replay["reintroduced_absent"] if scored else None,
        "replay_still_shown_absent_delta": (candidate_replay["still_shown_absent"]
                                            - baseline_replay["still_shown_absent"]) if scored else None,
        "replay_lost_present_rate": candidate_replay["lost_present"] / present if present else None,
        "replay_error_rate": candidate_replay["errors"] / scored if scored else None,
        "lab_forbidden_rate": lab_candidate["forbidden_rate"]["value"],
        "run_completion": run_completion,
    }


def _kept_rate(card: dict) -> tuple[float | None, int]:
    n = card.get("kept_present", 0) + card.get("lost_present", 0)
    return (card.get("kept_present", 0) / n if n else None), n


def slice_regressions(baseline: dict, candidate: dict, min_n: int = 10) -> list[dict]:
    """Cards whose kept rate on the replay set fell, with at least `min_n` cases on both sides."""
    out = []
    for card, base in baseline["by_card"].items():
        b, bn = _kept_rate(base)
        c, cn = _kept_rate(candidate["by_card"].get(card, {}))
        if b is not None and c is not None and min(bn, cn) >= min_n and c < b:
            out.append({"slice": card, "baseline": f"{base.get('kept_present', 0)}/{bn}",
                        "candidate": f"{candidate['by_card'][card].get('kept_present', 0)}/{cn}"})
    return out


def decide(metrics: dict, regressions: list[dict]) -> dict:
    reasons = []
    try:
        assert_promotion_ready(metrics)
    except ValueError as exc:
        reasons.append(str(exc))
    reasons += [f"regressed on {r['slice']}: kept {r['baseline']} before, {r['candidate']} now" for r in regressions]
    return {"promote": not reasons, "reasons": reasons or ["all gates met; no slice regressed"]}


def record(path: Path, version: str, decision: dict, report: Path) -> None:
    row = {"version": version, "decided_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "promote": decision["promote"], "reasons": decision["reasons"], "report": str(report)}
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
