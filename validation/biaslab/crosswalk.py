"""Reviewed-status crosswalk between Mesa simulation ids and BiasGuard card ids.

A shared id is a proposal, not a semantic match: only entries a person has marked
``pilot`` or ``approved`` resolve to a detector card.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

TIERS = ("headline_lede", "full_article", "decision_history", "internal_state")
RELATIONSHIPS = ("candidate_same_id", "equivalent_within_task", "narrower", "overlapping",
                 "context_only_effect", "unsupported_in_current_taxonomy")
REVIEW_STATUSES = ("needs_domain_review", "pilot", "approved", "rejected")
PATH = Path(__file__).with_name("crosswalk.json")


@dataclass(frozen=True)
class Entry:
    simulation_id: str
    detector_id: str | None
    relationship: str
    evidence_tier: str
    policy: str
    review_status: str
    required_evidence: tuple[str, ...]


def parse(records: list[dict]) -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    for r in records:
        e = Entry(r["simulation_id"], r["detector_id"], r["relationship"], r["evidence_tier"], r["policy"],
                  r["review_status"], tuple(r["required_evidence"]))
        if e.relationship not in RELATIONSHIPS or e.evidence_tier not in TIERS or e.review_status not in REVIEW_STATUSES:
            raise ValueError(f"crosswalk entry {e.simulation_id}: unknown relationship, tier or review status")
        if e.simulation_id in out:
            raise ValueError(f"crosswalk entry {e.simulation_id}: duplicate")
        out[e.simulation_id] = e
    return out


@lru_cache(maxsize=1)
def load() -> dict[str, Entry]:
    return parse(json.loads(PATH.read_text(encoding="utf-8")))


def _resolves(e: Entry, available_tier: str) -> bool:
    return (e.detector_id is not None and e.review_status in ("pilot", "approved")
            and TIERS.index(e.evidence_tier) <= TIERS.index(available_tier))


def resolve(simulation_id: str, available_tier: str = "headline_lede") -> str | None:
    e = load()[simulation_id]
    return e.detector_id if _resolves(e, available_tier) else None


def coverage() -> dict:
    entries = load().values()
    return {"relationship": dict(Counter(e.relationship for e in entries)),
            "review_status": dict(Counter(e.review_status for e in entries)),
            "evidence_tier": dict(Counter(e.evidence_tier for e in entries)),
            "resolvable": sum(_resolves(e, "headline_lede") for e in entries),
            "total": len(load())}
