"""Editor reviews, exported from the site, as an append-only label file.

A review applies only to the data-pack version and event text it was made on. The file stores
no reviewer identity.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

OUTCOMES = ("verified", "corrected", "rejected")
_FINDING_KEYS = ("supported", "uncertain", "effects")


@dataclass(frozen=True)
class Label:
    event: str
    card_id: str
    pack_version: str
    text_sha256: str
    outcome: str
    note: str
    tier_at_review: str
    audit: bool
    new_pattern: bool
    reviewed_at: str


def import_export(export: dict, results: dict, known_cards: set[str]) -> list[Label]:
    """Turn a site reviews export into labels. Any bad entry rejects the whole file."""
    if export.get("pack") != results.get("pack"):
        raise ValueError(f"export is for pack {export.get('pack')!r}, results are for {results.get('pack')!r}")
    findings = {(e["event"], f["id"]): (e, f) for e in results["events"]
                for key in _FINDING_KEYS for f in e.get(key) or []}
    labels, seen = [], set()
    for number, r in enumerate(export["reviews"], 1):
        key = r.get("key", "")
        if key.startswith("narr__"):
            continue   # narrative-coding reviews are a different record
        event, sep, card = key.partition("__")
        problem = (None if sep and event and card else "key is not <event>__<card>")
        problem = problem or ("unknown status" if r.get("status") not in OUTCOMES else None)
        problem = problem or ("unknown card" if card not in known_cards else None)
        problem = problem or ("no such finding in the results" if (event, card) not in findings else None)
        problem = problem or ("duplicate key" if key in seen else None)
        problem = problem or ("made on another pack" if r.get("pack") != results.get("pack") else None)
        if not problem and r.get("text") != findings[(event, card)][0].get("text"):
            problem = "made on different event text"
        if problem:
            raise ValueError(f"review {number} ({key!r}): {problem}; nothing was imported")
        seen.add(key)
        _, f = findings[(event, card)]
        labels.append(Label(event, card, results["pack"], r["text"], r["status"], r.get("note", ""),
                            f.get("tier", ""), bool(f.get("audit")), bool(r.get("new_pattern")), r.get("at", "")))
    return labels


def read(path: Path) -> list[Label]:
    path = Path(path)
    if not path.exists():
        return []
    return [Label(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append(path: Path, labels: Sequence[Label]) -> int:
    """Append labels not already present; returns how many were added."""
    existing = set(read(path))
    new = [l for l in labels if l not in existing]
    if new:
        with Path(path).open("a", encoding="utf-8") as f:
            f.write("".join(json.dumps(dataclasses.asdict(l), ensure_ascii=False) + "\n" for l in new))
    return len(new)


def latest(labels: Sequence[Label]) -> list[Label]:
    """One label per (event, card, pack): the most recently reviewed."""
    by_key: dict[tuple, Label] = {}
    for l in sorted(labels, key=lambda l: l.reviewed_at):
        by_key[(l.event, l.card_id, l.pack_version)] = l
    return list(by_key.values())
