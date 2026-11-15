"""What the detector said for one data pack, one row per event × card, written once.

A snapshot holds only what was known at prediction time. Nothing from human review goes in it;
reviews are joined later (errors.py).
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

_FINDING_KEYS = ("supported", "uncertain", "effects")


def load_core(path: Path) -> dict:
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def detector_version(results: dict) -> str:
    d = results["summary"]["detector"]
    key = f"{d['card_hash']}|{d['prompts_version']}|{d['max_candidates']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def snapshot_id(pack_version: str, catalog: str, version: str) -> str:
    return f"{pack_version or 'nopack'}_{catalog}_{version}"


def _size(outlets: int) -> str:
    return "20+" if outlets >= 20 else "10–19" if outlets >= 10 else "5–9" if outlets >= 5 else "<5"


def _bloc_mix(finding: dict, lean: dict[str, float]) -> str:
    blocs = set()
    for e in finding.get("evidence") or []:
        for outlet in e.get("o") or []:
            v = lean.get(outlet)
            if v is not None:
                blocs.add("sol" if v < 45 else "sağ" if v > 55 else "orta")
    return "yok" if not blocs else blocs.pop() if len(blocs) == 1 else "karışık"


def rows(results: dict, core: dict, catalog: str) -> list[dict]:
    lean = {s["s"]: s.get("lean") for s in core.get("S", [])}
    first = {e["i"]: e.get("f", "") for e in core.get("E", [])}
    version, pack = detector_version(results), results.get("pack", "")
    out = []
    for e in results["events"]:
        base = {"event": e["event"], "catalog": catalog, "month": first.get(e["event"], "")[:7],
                "event_size": _size(e.get("outlets", 0)), "outlets": e.get("outlets", 0),
                "text_sha256": e.get("text"), "pack_version": pack, "detector_version": version}
        if e.get("status") != "review_complete":
            out.append({**base, "card_id": None, "status": e.get("status"), "tier": None, "tier_reasons": [],
                        "audit": False, "bloc_mix": "yok"})
            continue
        flagged = set()
        for key in _FINDING_KEYS:
            for f in e.get(key) or []:
                flagged.add(f["id"])
                out.append({**base, "card_id": f["id"], "status": f.get("status"), "tier": f.get("tier"),
                            "tier_reasons": f.get("tier_reasons", []), "audit": bool(f.get("audit")),
                            "bloc_mix": _bloc_mix(f, lean)})
        for card in e.get("selected") or []:
            if card not in flagged:   # assessed and rejected by both reviewers, or hidden by the gate
                out.append({**base, "card_id": card, "status": "suppressed", "tier": None, "tier_reasons": [],
                            "audit": False, "bloc_mix": "yok"})
    return out


def write(results: dict, core: dict, catalog: str, out_dir: Path) -> Path:
    """Write the snapshot once. Re-running with the same inputs changes nothing."""
    body = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows(results, core, catalog))
    path = Path(out_dir) / (snapshot_id(results.get("pack", ""), catalog, detector_version(results)) + ".jsonl.gz")
    if path.exists():
        if gzip.decompress(path.read_bytes()).decode("utf-8") != body:
            raise ValueError(f"{path.name} already exists with different content; a snapshot is never rewritten")
        return path
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(body.encode("utf-8"), mtime=0))
    return path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in gzip.decompress(Path(path).read_bytes()).decode("utf-8").splitlines()]
