"""Daily release: collector data -> every rule-based analysis -> site and artifact files, in one command.

    python -m capraz_pipeline.daily [--until YYYY-MM-DD] [--work DIR]

Steps: fetch the collector's backfill-data branch; ingest into a fresh day store; seed event ids from the current
public/data/core.bin (so every known event keeps its id); build; refresh the BiasGuard run folders runs/bg9 and
runs/bgm9 for the new top 150 (an event whose text and context are unchanged keeps its selection, reviews and
explanations; any other event loses its old files and shows as not attempted until the weekly AI run); apply both
passes, compose explanations, pack; recompute AIX and the lens; repack; write public/ and the artifact fragment
(dist/artifact). Prints one JSON summary. Nothing is committed or published here.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import REPO

COLLECTOR = "https://github.com/aylinunel/turkish-news-scraper"
RUNS = (("bg9", "behavioural"), ("bgm9", "media"))
TRT = timezone(timedelta(hours=3))


def sh(*cmd: str, cwd: Path = REPO) -> str:
    print("+", " ".join(cmd), file=sys.stderr, flush=True)
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def _load(p: Path) -> dict:
    return json.loads(gzip.decompress(p.read_bytes()))


def fetch_collector(work: Path) -> Path:
    repo, data = work / "collector.git", work / "collector"
    if not repo.exists():
        sh("git", "init", "-q", "--bare", str(repo))
    sh("git", "-C", str(repo), "fetch", "-q", "--depth", "1", COLLECTOR, "backfill-data")
    shutil.rmtree(data, ignore_errors=True)
    data.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(repo), "archive", "FETCH_HEAD", "data"], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as t:
        t.extractall(data, filter="data")
    return data


def refresh_runs(build: Path) -> dict:
    """Write the new top 150 into each run; keep agent outputs only where the event's text and context are unchanged."""
    sys.path.insert(0, str(REPO))
    from biasguard.news import _inputs, event_inputs
    new = event_inputs(build, 150)
    out = {}
    for run, _ in RUNS:
        d = REPO / "runs" / run
        old = {x["event"]: x for x in _inputs(d)} if (d / "inputs.jsonl").exists() else {}
        keep = {x["event"] for x in new if x["event"] in old and (old[x["event"]]["text"], old[x["event"]]["context"]) == (x["text"], x["context"])}
        removed = 0
        for sub in ("selections", "reviews/advocate", "reviews/skeptic", "explain"):
            for f in (d / sub).glob("*.json") if (d / sub).exists() else []:
                if f.name.split("__")[0].removesuffix(".json") not in keep:
                    f.unlink()
                    removed += 1
        (d / "inputs.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in new), encoding="utf-8")
        out[run] = {"kept": len(keep), "to_review": len(new) - len(keep), "files_removed": removed}
    return out


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.daily")
    p.add_argument("--until", default=(datetime.now(TRT).date() - timedelta(days=1)).isoformat(), help="last complete Türkiye day")
    p.add_argument("--since", default="2026-09-01")
    p.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()) / "capraz-daily")
    a = p.parse_args(argv)
    work, build = a.work, a.work / "build"
    shutil.rmtree(work / "store", ignore_errors=True)
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)
    data = fetch_collector(work)
    py = sys.executable
    pipe = REPO / "pipeline"
    print(sh(py, "-m", "capraz_pipeline", "ingest", "--root", str(work / "store"), "--from", str(data), "--since", a.since, "--until", a.until, cwd=pipe), file=sys.stderr)
    core = _load(REPO / "public" / "data" / "core.bin")
    (build / "events-members.json").write_text(json.dumps({e["i"]: e["a"] for e in core["E"]}))
    sh(py, "-m", "capraz_pipeline", "build", "--root", str(work / "store"), "--out", str(build), "--since", a.since, "--until", a.until, cwd=pipe)
    runs = refresh_runs(build)
    pack = datetime.now(TRT).date().isoformat()
    for run, cat in RUNS:
        sh(py, "-m", "biasguard.news", "apply", "--run", f"runs/{run}", "--catalog", cat,
           "--card-status", "validation/reference/card_status.json", "--pack", pack)
        sh(py, "-m", "biasguard.explain_rules", "--run", f"runs/{run}", "--core", str(build / "core.bin"), "--catalog", cat)
    shutil.copy(REPO / "runs/bg9/biasguard.json", build / "biasguard.json")
    shutil.copy(REPO / "runs/bgm9/biasguard.json", build / "biasguard-media.json")

    def pack_core() -> None:
        sh(py, "-m", "biasguard.news", "pack", "--build", str(build), "--run", "runs/bg9", "--media-run", "runs/bgm9")
        c = _load(build / "core.bin")
        c["meta"]["version"], c["meta"]["built"] = "9", pack
        (build / "core.bin").write_bytes(gzip.compress(json.dumps(c, ensure_ascii=False, separators=(",", ":")).encode()))

    pack_core()
    sh(py, "-m", "capraz_pipeline.aix", "--data", str(build), cwd=pipe)
    sh(py, "-m", "capraz_pipeline.lens", "--data", str(build), cwd=pipe)
    pack_core()
    # 9'da yeni: the 8.2 release (data/reference/core-82.bin) against today's build, then pack it in
    old = {x["event"]: x for x in map(json.loads, (REPO / "runs/bg82/inputs.jsonl").read_text(encoding="utf-8").splitlines())}
    top = [json.loads(l) for l in (REPO / "runs/bg9/inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    n_new = sum(x["event"] not in old for x in top)
    n_chg = sum(x["event"] in old and (old[x["event"]]["text"], old[x["event"]]["context"]) != (x["text"], x["context"]) for x in top)
    sh(py, "-m", "capraz_pipeline.whatsnew9", "--old", str(REPO / "data/reference/core-82.bin"), "--new", str(build / "core.bin"),
       "--bg-new", str(n_new), "--bg-changed", str(n_chg), cwd=pipe)
    pack_core()
    sh(py, "-m", "capraz_pipeline", "site", "--out", str(build), "--site", "../public", cwd=pipe)
    art = REPO / "dist" / "artifact"
    shutil.rmtree(art, ignore_errors=True)
    sh(py, "-m", "capraz_pipeline", "site", "--out", str(build), "--site", str(art), "--fragment", cwd=pipe)
    # record the new packs for tests_repo (the pack guard compares against this file)
    rec = json.loads((REPO / "docs/provenance/packs.json").read_text(encoding="utf-8"))
    rec.update(built=pack, window=[a.since, a.until],
               packs={str(f.relative_to(REPO)): hashlib.sha256(gzip.decompress(f.read_bytes())).hexdigest()
                      for f in sorted((REPO / "public/data").glob("[alu]-*.bin"))})
    (REPO / "docs/provenance/packs.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shutil.copy(build / "report.json", REPO / "docs" / "build-report.json")
    new = _load(build / "core.bin")
    print(json.dumps({"until": a.until, "articles": new["meta"]["counts"]["articles"], "events": len(new["E"]),
                      "outlets": len(new["meta"]["sources"]), "runs": runs, "artifact_dir": str(art),
                      "bg": {k: v for k, v in new["BG"]["summary"].items() if k in ("completed", "notAttempted", "uncertain", "supported")}}, indent=1))


if __name__ == "__main__":
    main()
