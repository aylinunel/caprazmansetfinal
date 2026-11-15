"""Move a media card from lab candidate to the production media catalogue.

Two conditions, both required: the owner approved the card, and the candidate detector got every lab
case for it right (all cases completed, no forbidden answer on a control, at least one positive found).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from . import crosswalk
from .cases import expected
from .configs import PROPOSED_DIR
from .ledger import Ledger

MEDIA_CATALOG = Path(__file__).resolve().parents[2] / "biasguard" / "data" / "media_cards.json"
_POSITIVE = {"supported", "contextual_effect"}
_INCOMPLETE = {"error", "unassessed", "ineligible"}


def card_outcomes(run: Path) -> dict[str, dict[str, list[str]]]:
    """Per card, per case kind: the candidate detector's first-attempt statuses in a lab run."""
    private = [json.loads(l) for l in (Path(run) / "private" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l]
    first = Ledger(Path(run) / "ledger.jsonl").first_attempts("candidate")
    out: dict[str, dict[str, list[str]]] = {}
    for p in private:
        card = crosswalk.load()[p["concept"]].detector_id
        if card and p["case_id"] in first:
            out.setdefault(card, {}).setdefault(p["kind"], []).append(first[p["case_id"]].status)
    return out


def promotable(outcomes: dict[str, list[str]], approved: bool) -> tuple[bool, list[str]]:
    reasons = [] if approved else ["not approved by the owner"]
    statuses = [s for ss in outcomes.values() for s in ss]
    if not statuses:
        return False, reasons + ["no lab cases were scored for this card"]
    incomplete = sum(s in _INCOMPLETE for s in statuses)
    if incomplete:
        reasons.append(f"{incomplete} of {len(statuses)} lab cases did not complete")
    for kind, ss in outcomes.items():
        if kind == "positive":
            continue
        bad = sum(s in expected(kind, True).forbidden for s in ss)
        if bad:
            reasons.append(f"{bad} of {len(ss)} {kind} cases got a forbidden answer")
    if not any(s in _POSITIVE for s in outcomes.get("positive", [])):
        reasons.append("no positive case was supported")
    return not reasons, reasons


def promote(outcomes: dict[str, dict[str, list[str]]], approved: Sequence[str], lab_run: str,
            dest: Path = MEDIA_CATALOG) -> dict[str, list[str]]:
    """Add promotable cards to the media catalogue; return {card: reasons} for those refused."""
    current = {c["id"]: c for c in json.loads(Path(dest).read_text(encoding="utf-8"))}
    refused = {}
    for card_id in sorted(set(outcomes) | set(approved)):
        ok, reasons = promotable(outcomes.get(card_id, {}), card_id in approved)
        if not ok:
            refused[card_id] = reasons
            continue
        card = json.loads((PROPOSED_DIR / f"{card_id}.json").read_text(encoding="utf-8"))
        card["provenance"] = (card["provenance"].replace("LAB-ONLY PROPOSAL, not reviewed, not in production. ", "")
                              + f" Owner-approved; passed lab run {lab_run}. Not validated against human-reviewed news.")
        current[card_id] = card
    Path(dest).write_text(json.dumps([current[k] for k in sorted(current)], indent=1, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return refused
