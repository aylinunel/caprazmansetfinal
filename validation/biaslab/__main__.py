"""python -m validation.biaslab build|tasks|score|promote --run runs/lab/<name>"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import configs, run as lab


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m validation.biaslab")
    p.add_argument("cmd", choices=["build", "tasks", "score", "promote"])
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--config", choices=configs.CONFIGS)
    p.add_argument("--stage", choices=["select", "review"])
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--mode", choices=["ai", "offline"], default="ai")
    p.add_argument("--approved", nargs="*", default=[], help="promote: card ids the owner approved")
    a = p.parse_args(argv)
    if a.cmd == "build":
        print(lab.build(a.run, a.seed)["cases"], "cases written to", a.run)
        return 0
    if a.cmd == "tasks":
        if not (a.config and a.stage):
            p.error("tasks needs --config and --stage")
        for path in lab.tasks(a.run, a.config, a.stage, a.batch):
            print(path)
        return 0
    if a.cmd == "promote":
        from . import promote as pr
        outcomes = pr.card_outcomes(a.run)
        media = {c: o for c, o in outcomes.items() if (pr.PROPOSED_DIR / f"{c}.json").exists()}
        refused = pr.promote(media, a.approved, a.run.name)
        for card in sorted(media):
            print(f"{card}: " + ("refused — " + "; ".join(refused[card]) if card in refused else "promoted"))
        return 0
    report, code = lab.score(a.run, a.mode)
    print(lab.text_summary(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
