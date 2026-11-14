"""Append-only record of every detector attempt. The first attempt per case is the one scored."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .adapter import Assessment


@dataclass(frozen=True)
class Attempt:
    case_id: str
    config: str
    attempt: int
    status: str
    target: str | None
    native_status: str
    spans: tuple[dict, ...]
    card_hash: str
    prompts_version: str
    recorded_at: str


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def attempts(self) -> list[Attempt]:
        if not self.path.exists():
            return []
        out = []
        for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                out.append(Attempt(**{**raw, "spans": tuple(raw["spans"])}))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"{self.path.name}: line {number} is not a valid attempt record") from exc
        return out

    def record(self, case_id: str, config: str, assessment: Assessment, audit: dict) -> Attempt:
        earlier = sum(1 for a in self.attempts() if a.case_id == case_id and a.config == config)
        attempt = Attempt(case_id, config, earlier + 1, assessment.status, assessment.target,
                          assessment.native_status, tuple(dataclasses.asdict(s) for s in assessment.spans),
                          audit.get("card_hash_sha256", ""), audit.get("prompts_version", ""),
                          datetime.now(timezone.utc).isoformat(timespec="seconds"))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dataclasses.asdict(attempt), ensure_ascii=False) + "\n")
        return attempt

    def first_attempts(self, config: str) -> dict[str, Attempt]:
        return {a.case_id: a for a in self.attempts() if a.config == config and a.attempt == 1}
