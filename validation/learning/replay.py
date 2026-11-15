"""The replay set: every human review, kept for good as a case a new detector version must not break.

A case stores the event text it was reviewed on, so it survives later data packs.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from biasguard.engine import BiasGuard
from biasguard.news import MAX_CANDIDATES, FileReviewer
from validation.feedback.labels import Label

_SHOWN = {"pattern_supported", "contextual_effect_consensus", "reviewer_disagreement", "needs_context"}
_CONFIRMED = {"pattern_supported", "contextual_effect_consensus"}


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    event: str
    card_id: str
    text: str
    context: str
    text_sha256: str
    expect: str            # "present" (verified or corrected) | "absent" (rejected)
    note: str
    added_from_pack: str
    reviewed_at: str
    retired: str | None


def _id(event: str, card: str, text_hash: str, reviewed_at: str) -> str:
    return "r-" + hashlib.sha256(f"{event}|{card}|{text_hash}|{reviewed_at}".encode("utf-8")).hexdigest()[:12]


def build(labels: Sequence[Label], inputs: list[dict], existing: Sequence[ReplayCase]) -> list[ReplayCase]:
    """Existing cases unchanged, plus one new case per new review. Older reviews of a key are retired."""
    by_hash = {hashlib.sha256(i["text"].encode("utf-8")).hexdigest(): i for i in inputs}
    cases = {c.case_id: c for c in existing}
    for l in sorted(labels, key=lambda l: l.reviewed_at):
        cid = _id(l.event, l.card_id, l.text_sha256, l.reviewed_at)
        item = by_hash.get(l.text_sha256)
        if cid in cases or item is None:
            continue   # already stored, or the reviewed text is not available to copy
        cases[cid] = ReplayCase(cid, l.event, l.card_id, item["text"], item["context"], l.text_sha256,
                                "absent" if l.outcome == "rejected" else "present", l.note, l.pack_version,
                                l.reviewed_at, None)
    newest: dict[tuple, ReplayCase] = {}
    for c in cases.values():
        key = (c.event, c.card_id, c.text_sha256)
        if key not in newest or c.reviewed_at > newest[key].reviewed_at:
            newest[key] = c
    out = []
    for c in cases.values():
        stale = newest[(c.event, c.card_id, c.text_sha256)].case_id != c.case_id
        out.append(dataclasses.replace(c, retired="superseded") if stale and c.retired is None else c)
    return sorted(out, key=lambda c: (c.reviewed_at, c.case_id))


def read(path: Path) -> list[ReplayCase]:
    path = Path(path)
    if not path.exists():
        return []
    return [ReplayCase(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(path: Path, cases: Sequence[ReplayCase]) -> None:
    """Rewrite the file from `cases`, refusing to drop or alter a stored case (only `retired` may change)."""
    strip = lambda c: dataclasses.replace(c, retired=None)
    now = {c.case_id: c for c in cases}
    for old in read(path):
        if old.case_id not in now or strip(now[old.case_id]) != strip(old):
            raise ValueError(f"replay case {old.case_id} would be removed or changed; cases are permanent")
    Path(path).write_text("".join(json.dumps(dataclasses.asdict(c), ensure_ascii=False) + "\n" for c in cases),
                          encoding="utf-8")


def write_inputs(cases: Sequence[ReplayCase], run: Path) -> None:
    """inputs.jsonl for `python -m biasguard.news tasks --run <run>`; one row per live case."""
    Path(run).mkdir(parents=True, exist_ok=True)
    rows = [{"event": c.case_id, "title": "", "outlets": len(c.text.splitlines()), "text": c.text, "context": c.context}
            for c in cases if c.retired is None]
    (Path(run) / "inputs.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                            encoding="utf-8")


def score(cases: Sequence[ReplayCase], run: Path, cards: list[dict]) -> dict:
    """Does a detector version still agree with what people decided?"""
    # reintroduced_absent: both reviewers now confirm a finding a person rejected (never acceptable).
    # still_shown_absent: a rejected finding is still raised as uncertain (compare with the baseline version).
    keys = ("kept_present", "lost_present", "kept_absent", "still_shown_absent", "reintroduced_absent", "errors")
    total = dict.fromkeys(keys, 0)
    by_card: dict[str, dict] = {}
    live = [c for c in cases if c.retired is None]
    for c in live:
        r = BiasGuard(cards=cards, reviewer=FileReviewer(Path(run), c.case_id)).analyze(
            c.text, c.context, stakes="medium", mode="ai", max_candidates=MAX_CANDIDATES)
        status = {a["card_id"]: a["status"] for a in r.get("adjudication", [])}.get(c.card_id)
        if r["status"] != "review_complete":
            outcome = "errors"
        elif c.expect == "present":
            outcome = "kept_present" if status in _SHOWN else "lost_present"
        else:
            outcome = ("reintroduced_absent" if status in _CONFIRMED else
                       "still_shown_absent" if status in _SHOWN else "kept_absent")
        total[outcome] += 1
        by_card.setdefault(c.card_id, dict.fromkeys(keys, 0))[outcome] += 1
    return {**total, "scored": len(live), "by_card": by_card}
