"""Error analysis: where reviewers disagree with the detector, and why findings stay uncertain.

Reviews are verify-pass labels (anchored and partial; see docs/validation/DATA_CONTRACT.md).
Every rate is reported with its counts.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from biasguard.engine import BiasGuard
from biasguard.news import MAX_CANDIDATES, FileReviewer, _inputs
from validation.feedback.labels import Label, latest

MOVES = ("better card wording", "better evidence (context the input lacks)",
         "better threshold/config", "better product fallback")


def joined(rows: list[dict], labels: Sequence[Label]) -> list[dict]:
    """Each snapshot row with its review outcome, or None. A label binds to pack and event text."""
    by_key = {(l.event, l.card_id, l.pack_version, l.text_sha256): l for l in latest(labels)}
    out = []
    for r in rows:
        l = by_key.get((r["event"], r["card_id"], r["pack_version"], r["text_sha256"]))
        out.append({**r, "outcome": l.outcome if l else None, "note": l.note if l else ""})
    return out


def confusion(joined_rows: list[dict]) -> dict:
    out: dict = {"system_failures": sum(r["card_id"] is None for r in joined_rows)}
    for r in joined_rows:
        if r["tier"] is None:
            continue
        c = out.setdefault(r["tier"], {"kept": 0, "rejected": 0, "unreviewed": 0})
        c["unreviewed" if r["outcome"] is None else "rejected" if r["outcome"] == "rejected" else "kept"] += 1
    return out


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p, d = k / n, 1 + z * z / n
    centre, half = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / d, (centre + half) / d


def clusters(joined_rows: list[dict], by: Sequence[str], min_n: int = 5) -> dict:
    """Slices of reviewed findings, worst (highest lower bound of the reject rate) first."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in joined_rows:
        if r["outcome"] is not None:
            groups[tuple(r[f] for f in by)].append(r)
    found, too_few = [], []
    for key, rs in groups.items():
        n, k = len(rs), sum(r["outcome"] == "rejected" for r in rs)
        base = {"slice": dict(zip(by, key)), "reviewed": n, "rejected": k}
        if n < min_n:
            too_few.append(base)
        else:
            lo, hi = _wilson(k, n)
            found.append({**base, "reject_rate": k / n, "lower": lo, "upper": hi})
    found.sort(key=lambda c: (-c["lower"], -c["reviewed"]))
    too_few.sort(key=lambda c: -c["reviewed"])
    return {"clusters": found, "too_few": too_few}


def stuck_conditions(run: Path) -> list[dict]:
    """Per card: how often each necessary condition was satisfied, unknown or contradicted.

    This explains findings that never reach "supported": a condition that is unknown in most
    assessments is asking for evidence the input does not contain.
    """
    per: dict[str, dict[int, Counter]] = defaultdict(lambda: defaultdict(Counter))
    seen: Counter = Counter()
    for it in _inputs(Path(run)):
        r = BiasGuard(reviewer=FileReviewer(Path(run), it["event"])).analyze(
            it["text"], it["context"], stakes="medium", mode="ai", max_candidates=MAX_CANDIDATES)
        for o in r.get("reviewer_outcomes", []):
            for a in o["assessments"]:
                if not a.get("necessary_conditions"):
                    continue   # rejected outright, no condition detail
                seen[a["card_id"]] += 1
                for c in a["necessary_conditions"]:
                    per[a["card_id"]][c["condition_index"]][c["status"]] += 1
    out = []
    for card, conds in per.items():
        detail = [{"index": i, "satisfied": c["satisfied"], "unknown": c["unknown"], "contradicted": c["contradicted"]}
                  for i, c in sorted(conds.items())]
        worst = max(d["unknown"] + d["contradicted"] for d in detail)
        out.append({"card_id": card, "assessments": seen[card], "conditions": detail,
                    "stuck_share": worst / seen[card]})
    return sorted(out, key=lambda s: -s["assessments"])


def next_move(cluster: dict, stuck: list[dict], system_failure_rate: float) -> str:
    """One of the four moves, by rule; a person decides whether to take it."""
    if system_failure_rate > 0.05:
        return MOVES[3]
    card = cluster["slice"].get("card_id")
    if card is None:
        return MOVES[2]
    s = next((s for s in stuck if s["card_id"] == card), None)
    return MOVES[1] if s and s["stuck_share"] > 0.5 else MOVES[0]


def report(snapshot: str, joined_rows: list[dict], stuck: list[dict]) -> str:
    c = confusion(joined_rows)
    events = len({r["event"] for r in joined_rows})
    reviewed = sum(r["outcome"] is not None for r in joined_rows)
    failure_rate = c["system_failures"] / events if events else 0.0
    lines = [f"# Error analysis — {snapshot}", "",
             "Reviews are verify-pass labels: the reviewer saw the AI's finding first, and only shown findings can be",
             "reviewed. These numbers say nothing about findings the detector missed.", "",
             "## Reviewed and unreviewed findings", "", "| Tier | Kept | Rejected | Unreviewed |", "|---|---|---|---|"]
    for tier in ("ai_confident", "needs_human"):
        t = c.get(tier, {"kept": 0, "rejected": 0, "unreviewed": 0})
        lines.append(f"| {tier} | {t['kept']} | {t['rejected']} | {t['unreviewed']} |")
    lines += ["", f"Events whose review failed: {c['system_failures']} of {events}.", ""]
    if not reviewed:
        lines += ["No finding has been reviewed yet, so there are no error clusters.", ""]
    else:
        lines += ["## Where reviewers rejected findings", ""]
        for by in (["card_id"], ["bloc_mix"], ["tier"], ["month"], ["event_size"]):
            out = clusters(joined_rows, by)
            for cl in out["clusters"]:
                name = ", ".join(f"{k} = {v}" for k, v in cl["slice"].items())
                lines.append(f"- {name}: rejected {cl['rejected']}/{cl['reviewed']} "
                             f"(95% interval {cl['lower']:.2f}–{cl['upper']:.2f}). "
                             f"Proposed move: {next_move(cl, stuck, failure_rate)}.")
            if out["too_few"]:
                few = "; ".join(", ".join(f"{k} = {v}" for k, v in t["slice"].items())
                                + f" ({t['rejected']}/{t['reviewed']})" for t in out["too_few"])
                lines.append(f"- Too few reviews to judge (rejected/reviewed): {few}.")
        lines.append("")
    if stuck:
        lines += ["## Why findings stay uncertain", "",
                  "For each card: of the reviewer assessments that examined its conditions, how many left each",
                  "condition satisfied / unknown / contradicted. A condition that is mostly unknown asks for evidence a",
                  "headline and lede do not contain.", "",
                  "| Card | Assessments | Conditions (satisfied/unknown/contradicted) | Most-stuck condition |", "|---|---|---|---|"]
        for s in stuck[:15]:
            conds = "; ".join(f"#{d['index'] + 1}: {d['satisfied']}/{d['unknown']}/{d['contradicted']}" for d in s["conditions"])
            worst = max(s["conditions"], key=lambda d: d["unknown"] + d["contradicted"])
            n = worst["unknown"] + worst["contradicted"]
            lines.append(f"| {s['card_id']} | {s['assessments']} | {conds} | #{worst['index'] + 1}: {n}/{s['assessments']} not satisfied |")
        lines.append("")
    return "\n".join(lines)
