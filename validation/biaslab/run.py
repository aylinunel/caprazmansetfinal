"""Lab commands: build cases, write reviewer tasks, score the results.

Reviewing itself is done by the existing file-based reviewer workflow (biasguard/AGENT_REVIEW.md);
nothing here calls a model provider.
"""
from __future__ import annotations

import dataclasses
import json
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

from biasguard import news
from biasguard.engine import BiasGuard

from . import configs, crosswalk
from .adapter import Assessment, Span, normalize, verify_spans
from .cases import PERTURBATIONS, DetectorInput, case_id, expected, family_id, split_of
from .ledger import Ledger
from .metrics import Row, paired_bootstrap, summarize
from .renderer import _RENDERERS, assert_no_leak, kinds, render, variants
from .sim import realize, scenario

PILOT = ("selective_statistics", "illusory_truth_effect")   # the first two concepts the lab was built on


def lab_concepts() -> tuple[str, ...]:
    """Every concept that has both a renderer and a card under the candidate configuration."""
    return tuple(c for c in sorted(_RENDERERS) if configs.target(c, "candidate"))
SCOPE = "synthetic, implementation-authored cases; not detector accuracy"
_PRIMARY = ("end_to_end_recall", "strict_precision")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sources(concept: str, seed: int) -> dict[str, object]:
    """Which realised agent each kind is rendered from. The label follows what the agent did."""
    positive = realize(concept, scenario(concept, "positive"), seed=seed)
    boundary = realize(concept, scenario(concept, "boundary"), seed=seed)
    active = next((r for r in positive if r.active), None)
    inactive = next((r for r in positive if not r.active), None)
    return {"positive": active, "missing_context": active, "quoted_control": active,
            "inactive_control": inactive, "boundary_control": boundary[0]}


def build(run: Path, seed: int = 42, salt: str | None = None) -> dict:
    run = Path(run)
    if (run / "inputs.jsonl").exists():
        raise FileExistsError(f"{run} already holds a lab run; choose a new folder")
    (run / "private").mkdir(parents=True)
    salt = salt or secrets.token_hex(16)
    inputs, private, seen = [], [], set()
    for concept in lab_concepts():
        sources = _sources(concept, seed)
        detector_id = configs.target(concept, "candidate")
        for variant in range(variants(concept)):
            family = family_id(concept, {"variant": variant})
            for kind in kinds(concept):
                realized = sources[kind]
                if realized is None:
                    continue
                base_id = None
                for perturbation in PERTURBATIONS:
                    visible = render(realized, kind, variant, perturbation)
                    cid = case_id(visible, salt)
                    if perturbation == "none":
                        base_id = cid
                    if cid in seen:
                        continue   # identical visible input: one case, first label kept
                    seen.add(cid)
                    row = {"event": cid, "title": "", "outlets": len(visible.text.splitlines()),
                           "text": visible.text, "context": visible.context}
                    assert_no_leak(row, concept, detector_id, family)
                    inputs.append(row)
                    private.append({"case_id": cid, "concept": concept, "kind": kind, "variant": variant,
                                    "perturbation": perturbation,
                                    "base_case_id": None if perturbation == "none" else base_id,
                                    "family_id": family, "split": split_of(family), "seed": seed,
                                    "strength": realized.strength, "active": realized.active,
                                    "agent": realized.agent})
    dump = lambda rows: "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    (run / "inputs.jsonl").write_text(dump(inputs), encoding="utf-8")
    (run / "private" / "cases.jsonl").write_text(dump(private), encoding="utf-8")
    (run / "private" / "salt.txt").write_text(salt + "\n", encoding="utf-8")
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": seed,
                "cases": len(inputs), "concepts": list(lab_concepts()), "scope": SCOPE,
                "configs": {c: configs.manifest(c) for c in configs.CONFIGS}}
    (run / "private" / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def tasks(run: Path, config: str, stage: str, batch: int = 10) -> list[Path]:
    """Write reviewer task batches for one configuration, then check them for leaks."""
    run = Path(run)
    cfg = run / config
    cfg.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(run / "inputs.jsonl", cfg / "inputs.jsonl")
    paths = news.write_tasks(cfg, stage, batch, bg=BiasGuard(cards=configs.catalog(config)))
    families = {p["concept"]: p["family_id"] for p in _jsonl(run / "private" / "cases.jsonl")}
    for path in paths:
        events = json.loads(path.read_text(encoding="utf-8"))["events"]
        visible = [{k: e[k] for k in ("event", "text", "context")} for e in events]
        for concept, family in families.items():
            assert_no_leak({"events": visible, "file": path.name}, concept, None, family)
    return paths


def _assess(run: Path, config: str, item: dict, target: str | None, mode: str) -> tuple[Assessment, dict]:
    if target is None:
        return normalize({}, None), {}
    cards = configs.catalog(config)
    if mode == "offline":
        result = BiasGuard(cards=cards).analyze(item["text"], item["context"], mode="offline")
    else:
        reviewer = news.FileReviewer(run / config, item["event"])
        result = BiasGuard(cards=cards, reviewer=reviewer).analyze(
            item["text"], item["context"], stakes="medium", mode="ai", max_candidates=news.MAX_CANDIDATES)
    return normalize(result, target), result.get("audit", {})


def score(run: Path, mode: str = "ai") -> tuple[dict, int]:
    """Assess every case under both configurations, record the attempts, and report."""
    run = Path(run)
    items = {r["event"]: r for r in _jsonl(run / "inputs.jsonl")}
    private = {r["case_id"]: r for r in _jsonl(run / "private" / "cases.jsonl")}
    ledger = Ledger(run / "ledger.jsonl")
    for config in configs.CONFIGS:
        for cid, item in items.items():
            assessment, audit = _assess(run, config, item, configs.target(private[cid]["concept"], config), mode)
            ledger.record(cid, config, assessment, audit)
    report: dict = {"scope": SCOPE, "mode": mode, "crosswalk": crosswalk.coverage(),
                    "manifests": {c: configs.manifest(c) for c in configs.CONFIGS}}
    rows: dict[str, list[Row]] = {}
    for config in configs.CONFIGS:
        first = ledger.first_attempts(config)
        rows[config] = []
        for cid, attempt in first.items():
            p, item = private[cid], items[cid]
            e = expected(p["kind"], attempt.target is not None)
            try:
                verify_spans(Assessment(attempt.target, attempt.status, "", tuple(Span(**s) for s in attempt.spans)),
                             DetectorInput(item["text"], item["context"]))
                span_ok = True
            except ValueError:
                span_ok = False
            base = first.get(p["base_case_id"]) if p["base_case_id"] else None
            rows[config].append(Row(cid, p["family_id"], p["kind"], attempt.status, e.acceptable, e.forbidden,
                                    span_ok, base.status if base else None))
        report[config] = summarize(rows[config])
    report["comparison"] = {m: paired_bootstrap(rows["baseline"], rows["candidate"], m) for m in _PRIMARY}
    (run / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    complete = all(report[c]["completion"]["value"] == 1.0 for c in configs.CONFIGS)
    return report, 0 if complete else 2


def text_summary(report: dict) -> str:
    show = lambda v: "not estimable" if v["value"] is None else f"{v['value']:.3f} ({v['n']}/{v['d']})"
    lines = [f"Scope: {report['scope']}"]
    for config in configs.CONFIGS:
        s = report[config]
        lines.append(f"{config}: " + "; ".join(f"{k} {show(s[k])}" for k in (
            "completion", "eligible", "decision_coverage", "end_to_end_recall", "strict_precision",
            "forbidden_rate", "unsupported_assertion_rate", "perturbation_consistency")))
        lines.append(f"  statuses: {s['counts_by_status']}; families: {s['families']}")
    for metric, c in report["comparison"].items():
        point = "not estimable" if c["point"] is None else f"{c['point']:+.3f}"
        interval = "no interval (too few families)" if c["lo"] is None else f"[{c['lo']:+.3f}, {c['hi']:+.3f}]"
        lines.append(f"candidate − baseline, {metric}: {point} {interval}")
    return "\n".join(lines)
