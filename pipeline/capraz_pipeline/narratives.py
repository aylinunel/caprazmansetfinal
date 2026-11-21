"""Anlatı haritası weeks after the hand-coded period (Yöntem § 6, same rules).

    python -m capraz_pipeline.narratives candidates --build ../dist/capraz-8/build --out ../runs/narr
    (coding agents write ../runs/narr/coded/<event>.json; see runs/narr/PROMPT.md)
    python -m capraz_pipeline.narratives finalize --out ../runs/narr      -> data/reference/narratives-7.json

§ 6.2 sample per week (7.0 pool): the 10 events with most outlets, plus 25 from coverage ranks 11-80 ranked by
score range / 100 + (1 - mean pairwise headline Jaccard). § 6.3 selection: a dimension is a focus
dimension when at least half the outlets fill it with at least two distinct values; s_d = w_d * c_d * H_d,
S = sum of the top three, events need two focus dimensions, at most KEEP per week by S.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

from .config import REPO

WEEKS = [("w7", "11–17 Ekim", "2026-10-11", "2026-10-17"), ("w8", "18–24 Ekim", "2026-10-18", "2026-10-24"),
         ("w9", "25–31 Ekim", "2026-10-25", "2026-10-31"), ("w10", "1–7 Kasım", "2026-11-01", "2026-11-07"),
         ("w11", "8–13 Kasım", "2026-11-08", "2026-11-13")]
KEEP = 20  # most differentiated events shown per agent-coded week (S, § 6.3)
DIM_LABELS = {"frame": "Çerçeve", "hero": "Merkezdeki aktör", "blame": "Sorumlu tutulan", "cause": "Sunulan neden",
              "cons": "Öne çıkan sonuç", "aff": "Etkilenen kesim", "sol": "Meşrulaştırılan çözüm", "moral": "Ahlaki çerçeve",
              "start": "Hikâyenin başlangıcı"}
DIMS = list(DIM_LABELS)
WEIGHT = {"blame": 1.2, "sol": 1.2, "frame": 1.0, "cause": 1.0, "moral": 1.0, "start": 0.8, "aff": 0.8, "hero": 0.6, "cons": 0.5}
OUT = REPO / "data" / "reference" / "narratives-7.json"
METHOD = ("Başlıklardan otomatik kodlandı: her kurumun bu olaydaki ilk başlığını bir Claude ajanı okuyup dokuz boyut atadı "
          "(Yöntem § 6 şeması). Başlığın desteklemediği boyut boş bırakıldı. İnsan kodlayıcı denetiminden geçmedi.")


def _load(p: Path):
    return json.loads(gzip.decompress(p.read_bytes()))


def _words(t: str) -> set[str]:
    return {w for w in re.findall(r"\w+", t.lower()) if len(w) > 2}


def candidates(build: Path, out: Path) -> int:
    core = _load(build / "core.bin")
    packs = core["meta"]["packs"]
    arts = {}
    for m in packs["months"]:
        a = _load(build / f"a-{m}.bin")
        for k, i in enumerate(a["i"]):
            arts[i] = {"s": packs["sources"][a["s"][k]], "t": a["t"][k], "d": a["d"][k]}
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for wk, label, d0, d1 in WEEKS:
        evs = [e for e in core["E"] if d0 <= e["f"][:10] <= d1]
        evs.sort(key=lambda e: (-len(e["s"]), -e["n"], e["i"]))

        def first(e):
            f = {}
            for i in e["a"]:
                a = arts.get(i)
                if a and (a["s"] not in f or a["d"] < f[a["s"]]["d"]):
                    f[a["s"]] = a
            return f

        def diverge(e):
            ws = [_words(a["t"]) for a in first(e).values()]
            jac = [len(x & y) / len(x | y) for x, y in combinations(ws, 2) if x | y]
            return e["p"] / 100 + 1 - (sum(jac) / len(jac) if jac else 1)

        # 7.0: wider pool (35 per week) so the 20 most differentiated narratives can be kept.
        pick = evs[:10] + sorted(evs[10:80], key=lambda e: -diverge(e))[:25]
        for e in pick:
            f = first(e)
            rows.append({"event": e["i"], "week": wk, "title": e["t"],
                         "headlines": [{"s": s, "hl": a["t"]} for s, a in sorted(f.items(), key=lambda x: x[1]["d"])]})
    (out / "candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return len(rows)


def tasks(items: list[dict], examples: list[dict], out: Path, batch: int = 12, n_examples: int = 2) -> list[Path]:
    """Writes out/tasks/batch-K.json. Examples are the highest-score human-coded entries whose key is not an event of
    that batch, so the agent never sees the answer to a task it is given."""
    # an example must show how headlines map to codes, so every one of its rows needs headline text
    ranked = sorted((x for x in examples if x["rows"] and all(r.get("hl") for r in x["rows"])), key=lambda x: -x.get("score", 0))
    (out / "tasks").mkdir(parents=True, exist_ok=True)
    files = []
    for k, i in enumerate(range(0, len(items), batch), 1):
        evs = items[i:i + batch]
        taken = {e["event"] for e in evs}
        ex = [{"key": g["key"], "q": g["q"], "rows": g["rows"]} for g in ranked if g["key"] not in taken][:n_examples]
        f = out / "tasks" / f"batch-{k}.json"
        f.write_text(json.dumps({"dimensions": DIM_LABELS, "examples": ex, "events": evs}, ensure_ascii=False, indent=1))
        files.append(f)
    return files


def _gold(core: dict) -> list[dict]:
    return [{"key": k, "q": e["q"], "rows": e["rows"], "score": e.get("score", 0), "week": e.get("w", ""),
             "title": next((r["hl"] for r in e["rows"] if r.get("hl")), "")}  # first headline; never q.happened (human coding)
            for k, e in core["N"].items() if e.get("status") in ("hand_coded", "headline_coded") and e["rows"]]


def _focus(rows: list[dict]) -> tuple[list[str], float]:
    n = len(rows)
    scores = {}
    for d in DIMS:
        vals = [(r.get(d) or "").strip() for r in rows]
        vals = [v for v in vals if v]
        if n < 2 or len(vals) < n / 2 or len(set(vals)) < 2:
            continue
        counts = {v: vals.count(v) for v in set(vals)}
        h = -sum(c / len(vals) * math.log(c / len(vals)) for c in counts.values()) / math.log(n)
        scores[d] = WEIGHT[d] * (len(vals) / n) * h
    top = sorted(scores, key=lambda d: -scores[d])
    return top, round(sum(scores[d] for d in top[:3]), 4)


def finalize(out: Path) -> dict:
    cands = json.loads((out / "candidates.json").read_text())
    N, NW = {}, []
    for wk, label, *_ in WEEKS:
        coded, kept = 0, []
        for c in (x for x in cands if x["week"] == wk):
            p = out / "coded" / f"{c['event']}.json"
            if not p.exists():
                continue
            x = json.loads(p.read_text())
            known = {h["s"]: h["hl"] for h in c["headlines"]}
            rows = [{"s": r["s"], "hl": known[r["s"]], **{d: (r.get(d) or "").strip() for d in DIMS}}
                    for r in x["rows"] if r.get("s") in known]
            coded += 1
            focus, score = _focus(rows)
            if len(focus) >= 2:
                key = f"{wk}-{c['event']}"
                N[key] = {"label": "", "ev": c["event"], "w": wk, "kind": "event", "status": "agent_coded", "method": METHOD,
                          "q": {k: x["q"].get(k, "") for k in ("happened", "agree", "differ", "care")},
                          "rows": rows, "score": score, "focus": focus}
                kept.append(key)
        kept.sort(key=lambda k: -N[k]["score"])
        for k in kept[KEEP:]:
            del N[k]
        NW.append({"k": wk, "l": label, "keys": kept[:KEEP], "pool": coded, "coded": "agent"})
    OUT.write_text(json.dumps({"N": N, "NW": NW}, ensure_ascii=False, indent=1))
    return {w["k"]: (w["pool"], len(w["keys"])) for w in NW}


def _card_conditions(core: dict) -> dict:
    """{card id: {"n": name, "c": [necessary conditions]}} for every card with a finding in BG or BGM (pending included)."""
    used = {f["id"] for k in ("BG", "BGM") for ev in core.get(k, {}).get("events", []) + core.get(k, {}).get("pending", {}).get("events", [])
            for g in ("supported", "uncertain") for f in ev.get(g, [])}
    data = REPO / "biasguard" / "data"
    files = [data / "cards.json", data / "media_cards.json", *sorted((REPO / "validation" / "biaslab" / "proposed_cards").glob("*.json"))]
    out: dict = {}
    for f in files:
        x = json.loads(f.read_text(encoding="utf-8"))
        for c in x if isinstance(x, list) else [x]:
            if c["id"] in used and c["id"] not in out:
                out[c["id"]] = {"n": c["name"], "c": c["necessary_conditions"]}
    return out


def merge(core: dict) -> None:
    """7.0 analyses outside the main pipeline: agent-coded Anlatı haritası weeks and the checklist run
    on the current scorer (build.py and biasguard.news pack)."""
    cl = OUT.parent / "checklist-7.json"
    if cl.exists():
        core["CL"] = json.loads(cl.read_text())
    wn = OUT.parent / "whatsnew-81.json"  # 8.1: 8.0 vs 8.1 findings (python -m capraz_pipeline.whatsnew)
    if wn.exists():
        core["W81"] = json.loads(wn.read_text())
    w82 = OUT.parent / "whatsnew-82.json"  # 8.2: old AI review vs the rerun (python -m capraz_pipeline.whatsnew82)
    if w82.exists():
        core["W82"] = json.loads(w82.read_text())
    blind = OUT.parent / "blind-packets.json"  # blind coding packets for the desk (python -m validation.answerkey packet)
    if blind.exists():
        core["BLIND"] = json.loads(blind.read_text(encoding="utf-8"))
    # biasguard/data files the site shares with explain_rules.py: Turkish meanings of behavioural concepts (BMT),
    # card ids the concept registry stores under an older key (BRA)
    for key, name in (("BMT", "behavioural_means.json"), ("BRA", "concept_alias.json")):
        f = REPO / "biasguard" / "data" / name
        if f.exists():
            core[key] = json.loads(f.read_text(encoding="utf-8"))
    cards = _card_conditions(core)  # AI denetim masası: the conditions an expert checks, one copy per concept with findings
    if cards:
        core["BGC"] = cards
    aix = OUT.parent / "aix-82.json"  # 8.2: AI findings against the rule-based findings (python -m capraz_pipeline.aix)
    if aix.exists():
        core["AIX"] = json.loads(aix.read_text())
    lens = OUT.parent / "lens-82.json"  # 8.2: single-source lens, same-story measures (python -m capraz_pipeline.lens)
    if lens.exists():
        core["LENS"] = json.loads(lens.read_text())
    nq = OUT.parent / "narrative-quality.json"  # AI coding vs human coding on hand-coded events (Task 6)
    if nq.exists():
        core["NQ"] = json.loads(nq.read_text(encoding="utf-8"))
    if OUT.exists():
        x = json.loads(OUT.read_text())
        core["N"] = {**core.get("N", {}), **x["N"]}
        core["NW"] = [w for w in core.get("NW", []) if w["k"] not in {y["k"] for y in x["NW"]}] + x["NW"]


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.narratives")
    p.add_argument("cmd", choices=["candidates", "finalize", "tasks"])
    p.add_argument("--build", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source", choices=["gold", "candidates"], default="candidates")
    p.add_argument("--core", type=Path, default=REPO / "public" / "data" / "core.bin")
    a = p.parse_args()
    if a.cmd == "tasks":
        gold = _gold(_load(a.core))
        if a.source == "gold":
            items = [{"event": g["key"], "week": g["week"], "title": g["title"],
                      "headlines": [{"s": r["s"], "hl": r["hl"]} for r in g["rows"]]}
                     for g in gold if all(r.get("hl") for r in g["rows"])]  # hand_coded events carry no headline text
        else:
            items = json.loads((a.out / "candidates.json").read_text())
        files = tasks(items, gold, a.out)
        print(f"{len(files)} batch files, {len(items)} events")
    else:
        print(candidates(a.build, a.out) if a.cmd == "candidates" else finalize(a.out))
