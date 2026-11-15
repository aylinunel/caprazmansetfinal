"""What changed, and what the catalogue may be missing.

Everything here is a prompt for a person. Nothing in this module edits a catalogue: a proposal's next
step is always to write it as a lab candidate and pass the promotion gate.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from itertools import combinations
from typing import Sequence

from validation.feedback.labels import Label

NEXT = "write it as a lab candidate and pass the promotion gate"
_FOLD = str.maketrans("ıİşŞğĞüÜöÖçÇâîû", "iisSgGuUoOcCaiu")


def _rate_by_card(rows: list[dict]) -> tuple[dict[str, int], int]:
    events = len({r["event"] for r in rows})
    return Counter(r["card_id"] for r in rows if r.get("tier")), events


def drift(snapshots: Sequence[list[dict]]) -> list[dict]:
    """Per card: is the latest pack's finding rate outside what earlier packs showed?"""
    if not snapshots:
        return []
    per_pack = [_rate_by_card(s) for s in snapshots]
    latest_counts, latest_events = per_pack[-1]
    version = lambda s: s[0]["detector_version"] if s else None
    changed = len(snapshots) > 1 and version(snapshots[-1]) != version(snapshots[-2])
    out = []
    for card in sorted(latest_counts):
        rate = latest_counts[card] / latest_events
        earlier = [c.get(card, 0) / n for c, n in per_pack[:-1] if n]
        row = {"card_id": card, "latest": f"{latest_counts[card]}/{latest_events}", "detector_version_changed": changed}
        if len(earlier) < 4:
            row["flag"] = "too little history"
        else:
            mean, sd = statistics.mean(earlier), statistics.pstdev(earlier)
            row["usual"] = f"{mean:.3f} ± {sd:.3f}"
            row["flag"] = "outside usual range" if abs(rate - mean) > 3 * max(sd, 1e-9) else "within usual range"
        out.append(row)
    return out


def tier_shift(snapshots: Sequence[list[dict]]) -> list[dict]:
    out = []
    for s in snapshots:
        tiers = Counter(r["tier"] for r in s if r.get("tier"))
        out.append({"pack": s[0]["pack_version"] if s else "", "ai_confident": tiers["ai_confident"],
                    "needs_human": tiers["needs_human"]})
    return out


def co_occurrence(rows: list[dict], min_events: int = 10) -> list[dict]:
    """Card pairs raised on the same event far more often than chance: candidates to merge or split."""
    by_event: dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("tier") and r.get("card_id"):
            by_event[r["event"]].add(r["card_id"])
    n = len(by_event)
    single = Counter(c for cards in by_event.values() for c in cards)
    pairs = Counter(p for cards in by_event.values() for p in combinations(sorted(cards), 2))
    out = [{"pair": list(p), "together": k, "events": n, "lift": (k / n) / ((single[p[0]] / n) * (single[p[1]] / n))}
           for p, k in pairs.items() if k >= min_events]
    return sorted(out, key=lambda x: (-x["lift"], -x["together"]))


def new_pattern_notes(labels: Sequence[Label]) -> list[dict]:
    """Reviewer notes flagged "a pattern no card covers", grouped by their text ignoring case and Turkish diacritics."""
    groups: dict[str, list[Label]] = defaultdict(list)
    for l in labels:
        if l.new_pattern and l.note.strip():
            groups[" ".join(l.note.translate(_FOLD).casefold().split())].append(l)
    out = [{"text": ls[0].note, "count": len(ls), "examples": sorted({l.event for l in ls})[:5]} for ls in groups.values()]
    return sorted(out, key=lambda g: -g["count"])


def proposals(co: list[dict], notes: list[dict], rejected_clusters: list[dict]) -> dict:
    """Proposals need at least 5 supporting notes or 10 events; weaker signals are listed as "watching"."""
    found, watching = [], []
    for g in notes:
        item = {"kind": "new_card", "evidence": g, "next": NEXT}
        (found if g["count"] >= 5 else watching).append(item)
    for p in co:
        if p["lift"] >= 2.0:
            found.append({"kind": "merge_or_split_cards", "evidence": p, "next": NEXT})
    for c in rejected_clusters:
        if "card_id" in c["slice"] and c["reviewed"] >= 10 and c["reject_rate"] >= 0.5:
            found.append({"kind": "reword_card", "evidence": c, "next": NEXT})
    return {"proposals": found, "watching": watching}


def report(pack: str, drift_rows: list[dict], tiers: list[dict], co: list[dict], found: dict) -> str:
    lines = [f"# Insights — {pack}", "",
             "Nothing in this report changes a catalogue. Each proposal's next step is to write it as a lab",
             "candidate and pass the promotion gate.", "", "## Review status by pack", ""]
    lines += [f"- {t['pack']}: {t['ai_confident']} AI onaylı, {t['needs_human']} waiting for a person" for t in tiers] or ["- no snapshots"]
    lines += ["", "## Finding rates", ""]
    flagged = [d for d in drift_rows if d["flag"] == "outside usual range"]
    if drift_rows and all(d["flag"] == "too little history" for d in drift_rows):
        lines.append("Fewer than five packs exist, so there is no usual range to compare with yet.")
    elif not flagged:
        lines.append("No card's finding rate is outside its usual range.")
    for d in flagged:
        cause = "the detector version changed" if d["detector_version_changed"] else "the detector did not change, so look at the news"
        lines.append(f"- {d['card_id']}: {d['latest']} events, usual {d['usual']}; {cause}.")
    lines += ["", "## Cards raised together", ""]
    lines += [f"- {a} + {b}: together on {p['together']}/{p['events']} events (lift {p['lift']:.1f})"
              for p in co[:10] for a, b in [p["pair"]]] or ["No pair meets the minimum number of events."]
    lines += ["", "## Proposals", ""]
    if not found["proposals"]:
        lines.append("No proposals yet.")
    for p in found["proposals"]:
        lines.append(f"- **{p['kind']}** — {p['evidence']}. Next: {p['next']}.")
    if found["watching"]:
        lines += ["", "Watching (too little support so far):"] + [f"- {w['kind']}: “{w['evidence']['text']}” ({w['evidence']['count']} notes)" for w in found["watching"]]
    return "\n".join(lines) + "\n"
