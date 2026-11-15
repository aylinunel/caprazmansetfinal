"""python -m validation.learning snapshot|errors|replay-build|replay-inputs|replay-score|promote-check|insights"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validation.feedback.labels import read as read_labels

from . import errors, snapshot

REPO = Path(__file__).resolve().parents[2]
REFERENCE = REPO / "validation" / "reference"
REPORTS = REPO / "docs" / "validation" / "reports"


def _results(core: dict, catalog: str) -> dict:
    key = "BGM" if catalog == "media" else "BG"
    if key not in core:
        raise SystemExit(f"this data pack has no {catalog} review ({key})")
    return core[key]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m validation.learning")
    p.add_argument("cmd", choices=["snapshot", "errors", "replay-build", "replay-inputs", "replay-score",
                                   "promote-check", "insights"])
    p.add_argument("--core", type=Path, default=REPO / "public" / "data" / "core.bin")
    p.add_argument("--run", type=Path, default=REPO / "runs" / "bg")
    p.add_argument("--catalog", choices=["behavioural", "media"], default="behavioural")
    p.add_argument("--labels", type=Path, default=REFERENCE / "labels.jsonl")
    p.add_argument("--out", type=Path)
    p.add_argument("--metrics", type=Path, help="promote-check: JSON file of gate metrics")
    p.add_argument("--version", help="promote-check: candidate detector version id")
    a = p.parse_args(argv)
    if a.cmd in ("snapshot", "errors"):
        core = snapshot.load_core(a.core)
        results = _results(core, a.catalog)
        path = snapshot.write(results, core, a.catalog, REFERENCE / "snapshots")
        if a.cmd == "snapshot":
            print(path)
            return 0
        rows = snapshot.read(path)
        text = errors.report(path.name.removesuffix(".jsonl.gz"), errors.joined(rows, read_labels(a.labels)),
                             errors.stuck_conditions(a.run))
        out = a.out or REPORTS / f"errors-{path.name.removesuffix('.jsonl.gz')}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(out)
        return 0
    from . import cli_more
    return cli_more.run(a)


if __name__ == "__main__":
    sys.exit(main())
