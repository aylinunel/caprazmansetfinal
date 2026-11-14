"""python -m validation.biaslab build|tasks|score --run runs/lab/<name>"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import configs, run as lab


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m validation.biaslab")
    p.add_argument("cmd", choices=["build", "tasks", "score"])
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--config", choices=configs.CONFIGS)
    p.add_argument("--stage", choices=["select", "review"])
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--mode", choices=["ai", "offline"], default="ai")
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
    report, code = lab.score(a.run, a.mode)
    print(lab.text_summary(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
