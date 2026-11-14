"""Which findings carry the "AI onaylı" badge, which wait for a person, and what to review first.

The tier is a rule chosen by the project owner (2026-11-14), not a probability:
a finding is `ai_confident` when neither reviewer dismissed it, or when the skeptic confirmed at
least one of the card's necessary conditions. On the 8.1 run no reviewer ever said "supported",
so the badge means "left standing", not "confirmed"; the audit sample is what checks it.
"""
from __future__ import annotations

import hashlib
from typing import Any

REJECTED = "sorgulayan inceleme reddetti ve hiçbir koşulu doğrulamadı"
DEMOTED = "insan incelemeleri bu kavramda yetersiz buldu"
AUDIT_RATE = 0.05
_FINDING_KEYS = ("supported", "uncertain", "effects")


def tier(advocate: dict[str, Any], skeptic: dict[str, Any], card_status: str | None
         ) -> tuple[str, list[str], str | None]:
    """Return (tier, reasons, basis) for one finding from its two normalised assessments."""
    not_dismissed = "not_supported" not in (advocate["verdict"], skeptic["verdict"])
    confirmed = any(c["status"] == "satisfied" for c in skeptic.get("necessary_conditions", []))
    basis = ("both" if not_dismissed and confirmed else "not_dismissed" if not_dismissed
             else "skeptic_partly_confirmed" if confirmed else None)
    reasons = ([] if basis else [REJECTED]) + ([DEMOTED] if card_status == "demoted" else [])
    return ("needs_human" if reasons else "ai_confident"), reasons, basis


def in_audit_sample(event: str, card_id: str, pack_version: str, rate: float = AUDIT_RATE) -> bool:
    """Deterministic sample, so the same findings are audited on every rebuild of a pack."""
    digest = hashlib.sha256(f"{pack_version}|{event}|{card_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 2**32 < rate


def review_queue(events: list[dict[str, Any]], reviewed_counts: dict[str, int]) -> list[dict[str, Any]]:
    """Findings a person should look at: least-reviewed cards first, then the biggest events."""
    rows = []
    for e in events:
        for key in _FINDING_KEYS:
            for f in e.get(key) or []:
                why = "needs_human" if f["tier"] == "needs_human" else "audit" if f.get("audit") else None
                if why:
                    rows.append((reviewed_counts.get(f["id"], 0), -e["outlets"], e["event"], f["id"], why))
    return [{"event": ev, "card_id": card, "why": why, "priority": n}
            for n, (_, _, ev, card, why) in enumerate(sorted(rows), 1)]
