"""python -m validation.feedback import <reviews.json> --results <biasguard.json>
   python -m validation.feedback status --pack <pack version>"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from biasguard.catalog import load_cards

from .labels import append, import_export, read
from .stats import card_stats, card_status

REFERENCE = Path(__file__).resolve().parents[1] / "reference"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m validation.feedback")
    p.add_argument("cmd", choices=["import", "status"])
    p.add_argument("export", nargs="?", type=Path)
    p.add_argument("--results", type=Path)
    p.add_argument("--pack", default="")
    p.add_argument("--labels", type=Path, default=REFERENCE / "labels.jsonl")
    a = p.parse_args(argv)
    if a.cmd == "import":
        if not (a.export and a.results):
            p.error("import needs the export file and --results")
        labels = import_export(json.loads(a.export.read_text(encoding="utf-8")),
                               json.loads(a.results.read_text(encoding="utf-8")), {c["id"] for c in load_cards()})
        print(f"{append(a.labels, labels)} new labels ({len(labels)} in the export)")
        return 0
    gates = json.loads((REFERENCE / "gates.json").read_text(encoding="utf-8"))
    stats = card_stats(read(a.labels))
    status = card_status(stats, gates)
    out = {"pack_version": a.pack, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "agreed": gates["agreed"], "measure": "verify-pass precision (not accuracy)", "cards": status}
    (REFERENCE / "card_status.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not status:
        print("No reviews yet: no card is judged.")
    for card, c in sorted(status.items()):
        print(f"{card}: {c['status']} ({c['reasons'][0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
