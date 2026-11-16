"""8.2 Örüntüler › AI imzalı: AI findings (core keys BG, BGM) set against the rule-based findings.

    python -m capraz_pipeline.aix --data ../public/data      # writes data/reference/aix-82.json

Four analyses, all on the events both AI passes reviewed (review_complete):
  wording   outlets: how often the AI cites an outlet's headline for a wording technique
            (loaded-language, word-choice, labeling) against the rule-based loaded-language score
            of the same headlines; headline level: AUC of the rule score for "AI cited it".
  heat      media technique x bloc: share of events with the bloc present where the AI cited it.
  blame     Anlatı haritası 'sorumlu tutulan' (rule/agent-coded narrative rows) against the AI's
            responsibility-framing citations, per outlet-event: a 2x2 table and Cohen's kappa.
  where     findings per event by blind spot, loaded-language spread, topic and week.
Narratives merge it into core.bin as key AIX (narratives.merge).
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from .config import REPO

OUT = REPO / "data" / "reference" / "aix-82.json"
WORDING = ("loaded-language", "word-choice", "labeling")
MIN_EVENTS = 20
UNSET = re.compile(r"belirtilmiyor|yok|—", re.I)


def _load(p: Path):
    return json.loads(gzip.decompress(p.read_bytes()))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def auc(pos: list[float], neg: list[float]) -> float:
    """P(score of a random positive > random negative), ties half (Mann-Whitney U / n1 n2)."""
    if not pos or not neg:
        return float("nan")
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    ranks, i = [0.0] * len(allv), 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        for t in range(i, j + 1):
            ranks[t] = (i + j) / 2 + 1
        i = j + 1
    r_pos = sum(r for r, (_, lab) in zip(ranks, allv) if lab)
    return (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def spearman(x: list[float], y: list[float]) -> float:
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def kappa(a: int, b: int, c: int, d: int) -> float:
    """Cohen's kappa for [[a (both), b (rule only)], [c (AI only), d (neither)]]."""
    n = a + b + c + d
    if not n:
        return float("nan")
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def boot_mean_ci(xs: list[float], seed: int = 7, n: int = 1000) -> tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    rnd = random.Random(seed)
    ms = sorted(sum(rnd.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def _bloc(lean):
    return None if lean is None else "left" if lean < 45 else "right" if lean > 55 else "mid"


def _cited(f: dict) -> set[str]:
    return {o for q in f.get("evidence", []) for o in q.get("o", [])}


def _live(ev: dict) -> list[dict]:
    return ev.get("supported", []) + ev.get("uncertain", [])


def compute(core: dict, arts: dict[str, dict]) -> dict:
    lean = {s["s"]: s.get("lean") for s in core.get("S", [])}
    E = {e["i"]: e for e in core["E"]}
    bgm = {x["event"]: x for x in core.get("BGM", {}).get("events", []) if x["status"] == "review_complete" and x["event"] in E}
    bg = {x["event"]: x for x in core.get("BG", {}).get("events", []) if x["status"] == "review_complete" and x["event"] in E}

    # first headline per outlet per reviewed event, with its rule-based loaded-language score v
    first: dict[str, dict[str, dict]] = {}
    for ev in set(bgm) | set(bg):
        fx: dict[str, dict] = {}
        for i in E[ev]["a"]:
            a = arts.get(i)
            if a and (a["s"] not in fx or a["d"] < fx[a["s"]]["d"]):
                fx[a["s"]] = a
        first[ev] = fx

    # ---- wording: outlets and headlines
    cov, hit, vs = defaultdict(int), defaultdict(int), defaultdict(list)
    pos, neg = [], []
    for ev, x in bgm.items():
        cited = set().union(*[_cited(f) for f in _live(x) if f["id"] in WORDING] or [set()])
        for s, a in first[ev].items():
            cov[s] += 1
            vs[s].append(a["v"])
            if s in cited:
                hit[s] += 1
                pos.append(a["v"])
            else:
                neg.append(a["v"])
    outlets = []
    for s in cov:
        if cov[s] < MIN_EVENTS:
            continue
        lo, hi = wilson(hit[s], cov[s])
        outlets.append({"s": s, "bloc": _bloc(lean.get(s)), "n": cov[s], "k": hit[s], "rate": hit[s] / cov[s],
                        "lo": lo, "hi": hi, "v": sum(vs[s]) / len(vs[s])})
    outlets.sort(key=lambda r: -r["rate"])
    rho = spearman([r["v"] for r in outlets], [r["rate"] for r in outlets]) if len(outlets) > 2 else float("nan")
    rnd = random.Random(11)
    boots = sorted(auc([rnd.choice(pos) for _ in pos], [rnd.choice(neg) for _ in neg]) for _ in range(300)) if pos and neg else []
    blocs = {}
    for b in ("left", "mid", "right"):
        rs = [r for r in outlets if r["bloc"] == b]
        k, n = sum(r["k"] for r in rs), sum(r["n"] for r in rs)
        if n:
            blocs[b] = {"k": k, "n": n, "rate": k / n, "lo": wilson(k, n)[0], "hi": wilson(k, n)[1], "outlets": len(rs)}
    wording = {"outlets": outlets, "rho": rho, "blocs": blocs, "events": len(bgm),
               "headlines": {"cited": len(pos), "notCited": len(neg),
                             "vCited": sum(pos) / len(pos) if pos else None, "vNot": sum(neg) / len(neg) if neg else None,
                             "auc": auc(pos, neg), "aucLo": boots[7] if boots else None, "aucHi": boots[292] if boots else None}}

    # ---- heat: technique x bloc
    tech = sorted({f["id"] for x in bgm.values() for f in _live(x)})
    names = {f["id"]: f["name"] for x in bgm.values() for f in _live(x)}
    heat = []
    for t in tech:
        row = {"id": t, "name": names[t], "events": 0}
        for b in ("left", "mid", "right"):
            # per outlet-event, so a bloc with more outlets is not favoured by its size
            present = cited = 0
            for ev, x in bgm.items():
                hit_t = set().union(*[_cited(f) for f in _live(x) if f["id"] == t] or [set()])
                for s in first[ev]:
                    if _bloc(lean.get(s)) == b:
                        present += 1
                        cited += s in hit_t
            lo, hi = wilson(cited, present)
            row[b] = {"k": cited, "n": present, "rate": cited / present if present else 0, "lo": lo, "hi": hi}
        row["events"] = sum(1 for x in bgm.values() if any(f["id"] == t for f in _live(x)))
        heat.append(row)
    heat.sort(key=lambda r: -r["events"])

    # ---- blame: narrative 'sorumlu tutulan' vs AI responsibility-framing, per outlet-event
    nby = {n["ev"]: n for n in core.get("N", {}).values() if n.get("ev")}
    tab = {"both": 0, "rule": 0, "ai": 0, "neither": 0}
    events_both = 0
    for ev, x in bgm.items():
        n = nby.get(ev)
        if not n or not n.get("rows"):
            continue
        events_both += 1
        ai = set().union(*[_cited(f) for f in _live(x) if f["id"] == "responsibility-framing"] or [set()])
        for r in n["rows"]:
            rule = bool(str(r.get("blame") or "").strip()) and not UNSET.search(str(r.get("blame")))
            tab["both" if rule and r["s"] in ai else "rule" if rule else "ai" if r["s"] in ai else "neither"] += 1
    blame = {**tab, "events": events_both, "kappa": kappa(tab["both"], tab["rule"], tab["ai"], tab["neither"])}

    # ---- where: findings per event by context
    def group(key) -> list[dict]:
        g = defaultdict(list)
        for ev in bgm:
            for k in key(E[ev], ev) or []:
                g[k].append(len(_live(bgm[ev])) + (len(_live(bg[ev])) if ev in bg else 0))
        out = []
        for k, xs in g.items():
            lo, hi = boot_mean_ci(xs)
            out.append({"k": k, "n": len(xs), "mean": sum(xs) / len(xs), "lo": lo, "hi": hi})
        return sorted(out, key=lambda r: -r["n"])

    sp = {ev: max(a["v"] for a in first[ev].values()) - min(a["v"] for a in first[ev].values())
          for ev in bgm if len(first[ev]) >= 3}
    cuts = sorted(sp.values())
    t1, t2 = (cuts[len(cuts) // 3], cuts[2 * len(cuts) // 3]) if cuts else (0, 0)

    def spread(e, ev):
        if ev not in sp:
            return None
        v = sp[ev]
        return [f"dar (≤ {t1} puan)" if v <= t1 else f"orta ({t1 + 1}–{t2})" if v <= t2 else f"geniş (> {t2})"]

    where = {"blind": group(lambda e, ev: ["kör nokta: " + ("sol" if e["bs"] == "left" else "sağ") if e.get("bs") else "kör nokta yok"]),
             "spread": group(spread),
             "topic": [r for r in group(lambda e, ev: e.get("tp", [])[:1]) if r["n"] >= 5],
             "week": sorted([r for r in group(lambda e, ev: ["%d-H%02d" % date.fromisoformat(e["f"][:10]).isocalendar()[:2]])
                             if r["n"] >= 5], key=lambda r: r["k"])}
    clean = lambda o: None if isinstance(o, float) and math.isnan(o) else o
    return json.loads(json.dumps({"wording": wording, "heat": heat, "blame": blame, "where": where,
                                  "minEvents": MIN_EVENTS, "wordingIds": list(WORDING)},
                                 default=clean).replace("NaN", "null"))


def load_articles(data: Path, core: dict) -> dict[str, dict]:
    packs = core["meta"]["packs"]
    out = {}
    for m in packs["months"]:
        a = _load(data / f"a-{m}.bin")
        for k, i in enumerate(a["i"]):
            out[i] = {"s": packs["sources"][a["s"][k]], "d": a["d"][k], "v": a["v"][k]}
    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.aix")
    p.add_argument("--data", type=Path, required=True, help="folder with core.bin (with BG/BGM) and a-*.bin")
    a = p.parse_args()
    core = _load(a.data / "core.bin")
    res = compute(core, load_articles(a.data, core))
    OUT.write_text(json.dumps(res, ensure_ascii=False))
    w = res["wording"]
    print(json.dumps({"outlets": len(w["outlets"]), "rho": w["rho"], "auc": w["headlines"]["auc"], "blame": res["blame"],
                      "heat": len(res["heat"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
