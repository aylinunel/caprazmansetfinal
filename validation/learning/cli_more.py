"""Replay, promotion and insights commands for python -m validation.learning."""
from __future__ import annotations

import json
from pathlib import Path

from biasguard.catalog import load_cards
from biasguard.news import _inputs
from validation.feedback.labels import read as read_labels

from . import errors, insights, promotion, replay, snapshot

REPO = Path(__file__).resolve().parents[2]
REFERENCE = REPO / "validation" / "reference"
REPORTS = REPO / "docs" / "validation" / "reports"


def run(a) -> int:
    replay_path = REFERENCE / "replay.jsonl"
    if a.cmd == "replay-build":
        cases = replay.build(read_labels(a.labels), _inputs(a.run), replay.read(replay_path))
        replay.write(replay_path, cases)
        print(f"{sum(c.retired is None for c in cases)} live replay cases ({len(cases)} stored)")
        return 0
    if a.cmd == "replay-inputs":
        if not a.out:
            raise SystemExit("replay-inputs needs --out <new run folder>")
        replay.write_inputs(replay.read(replay_path), a.out)
        print(f"wrote {a.out / 'inputs.jsonl'}; write reviewer tasks with python -m biasguard.news tasks --run {a.out}")
        return 0
    if a.cmd == "replay-score":
        print(json.dumps(replay.score(replay.read(replay_path), a.run, load_cards()), indent=1, ensure_ascii=False))
        return 0
    if a.cmd == "promote-check":
        if not (a.metrics and a.version):
            raise SystemExit("promote-check needs --metrics <json> and --version <id>")
        m = json.loads(a.metrics.read_text(encoding="utf-8"))
        regressions = promotion.slice_regressions(m["baseline_replay"], m["candidate_replay"])
        decision = promotion.decide(promotion.metrics_from(m["baseline_replay"], m["candidate_replay"],
                                                           m["lab_candidate"], m.get("run_completion")), regressions)
        promotion.record(REFERENCE / "versions.jsonl", a.version, decision, a.metrics)
        print(("PROMOTE" if decision["promote"] else "DO NOT PROMOTE") + ": " + "; ".join(decision["reasons"]))
        return 0 if decision["promote"] else 1
    # insights
    snaps = [snapshot.read(p) for p in sorted((REFERENCE / "snapshots").glob(f"*_{a.catalog}_*.jsonl.gz"))]
    if not snaps:
        raise SystemExit("no snapshots yet; run: python -m validation.learning snapshot")
    labels = read_labels(a.labels)
    latest = snaps[-1]
    co = insights.co_occurrence(latest)
    rejected = errors.clusters(errors.joined(latest, labels), ["card_id"])["clusters"]
    found = insights.proposals(co, insights.new_pattern_notes(labels), rejected)
    pack = latest[0]["pack_version"] if latest else ""
    out = a.out or REPORTS / f"insights-{pack}_{a.catalog}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(insights.report(pack, insights.drift(snaps), insights.tier_shift(snaps), co, found), encoding="utf-8")
    print(out)
    return 0
