"""Normalise a BiasGuard result for one target card without collapsing outcomes.

`not_supported` means both reviewers assessed the card and rejected it. A card that was not
assessed, a run that failed and a concept with no card are three different things and stay so.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .cases import DetectorInput

_ADJUDICATION = {"pattern_supported": "supported", "contextual_effect_consensus": "contextual_effect",
                 "reviewer_disagreement": "uncertain", "needs_context": "uncertain", "suppressed": "not_supported"}
_FINDING_LISTS = ("supported_findings", "uncertain_findings", "contextual_effects")


@dataclass(frozen=True)
class Span:
    source: Literal["text", "context"]
    quote: str
    start: int   # Python code-point offset, inclusive
    end: int     # exclusive


@dataclass(frozen=True)
class Assessment:
    target: str | None
    status: str
    reason: str
    spans: tuple[Span, ...] = ()
    native_status: str = ""
    native_adjudication: str | None = None
    missing_context: tuple[str, ...] = ()
    extra_supported: tuple[str, ...] = ()


def normalize(result: dict, target: str | None) -> Assessment:
    if target is None:
        return Assessment(None, "ineligible", "No reviewed detector card for this concept; not a negative.")
    native = result.get("status", "")
    if native == "input_rejected":
        return Assessment(target, "error", "Input rejected by the detector.", native_status=native)
    if native == "offline_candidates_only":
        return Assessment(target, "unassessed", "Offline retrieval only; no card was assessed.", native_status=native)
    if native != "review_complete":
        return Assessment(target, "error", "Review did not complete; not a negative.", native_status=native)
    verdicts = {a["card_id"]: a["status"] for a in result["adjudication"]}
    extra = tuple(sorted(c for c, s in verdicts.items() if s == "pattern_supported" and c != target))
    if target not in verdicts:
        return Assessment(target, "unassessed", "Card was not selected for review; not a negative.",
                          native_status=native, extra_supported=extra)
    adjudication = verdicts[target]
    finding = next((f for key in _FINDING_LISTS for f in result[key] if f["id"] == target), None)
    spans = tuple(Span(e["source"], e["quote"], start, end)
                  for e in (finding["evidence"] if finding else [])
                  for start, end in zip(e["start_offsets"], e["end_offsets"]))
    return Assessment(target, _ADJUDICATION[adjudication], f"Detector adjudication: {adjudication}.", spans,
                      native, adjudication, tuple(finding["missing_context"]) if finding else (), extra)


def verify_spans(assessment: Assessment, input: DetectorInput) -> None:
    for span in assessment.spans:
        field = input.text if span.source == "text" else input.context
        if field[span.start:span.end] != span.quote:
            raise ValueError(f"evidence span does not match the original {span.source} field")
