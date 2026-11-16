"""8.2 Örüntüler › AI imzalı: AI findings (core keys BG, BGM) set against the rule-based findings.

    python -m capraz_pipeline.aix --data ../public/data      # writes data/reference/aix-82.json

Four analyses, all on the events both AI passes reviewed (review_complete):
  wording   outlets: how often the AI cites an outlet's headline for a wording technique
            (loaded-language, word-choice, labeling) against the rule-based loaded-language score
            of the same headlines; headline level: AUC of the rule score for "AI cited it".
  heat      media technique x bloc: share of a bloc's outlet-events where the AI quoted the outlet for it.
  blame     Anlatı haritası 'sorumlu tutulan' (rule/agent-coded narrative rows) against the AI's
            responsibility-framing citations, per outlet-event: a 2x2 table and Cohen's kappa.
  where     findings per event by blind spot, loaded-language spread, topic and week.
  profile   every outlet measure (rule-based, registry, Anlatı haritası, AI) side by side; Spearman matrix with
            permutation p-values and Benjamini-Hochberg q.
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


def _ranks(v: list[float]) -> list[float]:
    """1-based ranks, ties get their average rank."""
    o = sorted(range(len(v)), key=lambda i: v[i])
    r, i = [0.0] * len(v), 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for t in range(i, j + 1):
            r[o[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def auc(pos: list[float], neg: list[float]) -> float:
    """P(score of a random positive > random negative), ties half (Mann-Whitney U / n1 n2)."""
    if not pos or not neg:
        return float("nan")
    r_pos = sum(_ranks(pos + neg)[:len(pos)])
    return (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def _pearson(rx: list[float], ry: list[float]) -> float:
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def spearman(x: list[float], y: list[float]) -> float:
    return _pearson(_ranks(x), _ranks(y))


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


def perm_p(x: list[float], y: list[float], rho: float, n: int = 2000, seed: int = 5) -> float:
    """Two-sided permutation p-value for Spearman rho (shuffling y)."""
    if rho != rho:
        return float("nan")
    # ranks move with their values under a shuffle, so rank once and shuffle the ranks (same p, same seed)
    rnd, rx, ry, hit = random.Random(seed), _ranks(x), _ranks(y), 0
    for _ in range(n):
        rnd.shuffle(ry)
        hit += abs(_pearson(rx, ry)) >= abs(rho) - 1e-12
    return (hit + 1) / (n + 1)


# Outlet profile: every measure the site computes for an outlet, side by side. kind: kural = rule-based scorer,
# kayıt = registry, anlatı = Anlatı haritası coding (partly AI-coded), ai = AI imzalı review.
MEASURES = [
    ("lean", "Yerleşim (sol → sağ)", "kayıt"),
    ("cover", "Verdiği olay payı", "kural"),
    ("loaded", "Yüklü dil puanı", "kural"),
    ("gap", "Başlık spottan ne kadar sert", "kural"),
    ("first", "İlk veren olduğu olay payı", "kural"),
    ("blame", "Başlıkta birini sorumlu tutma payı", "anlatı"),
    ("ai_media", "AI: medya tekniği alıntısı", "ai"),
    ("ai_wording", "AI: sözcük tekniği alıntısı", "ai"),
    ("ai_behav", "AI: davranışsal yanlılık alıntısı", "ai"),
]


def profile(core: dict, arts: dict[str, dict], im: dict, ib: dict, first: dict, min_events: int = MIN_EVENTS) -> dict:
    """Every measure the site computes for an outlet, side by side, and their pairwise Spearman correlations."""
    lean = {s["s"]: s.get("lean") for s in core.get("S", [])}
    E = core["E"]
    n_ev = len(E)
    cover = defaultdict(int)
    for e in E:
        for s in set(e["s"]):
            cover[s] += 1
    pol, gaps = defaultdict(list), defaultdict(list)
    for a in arts.values():
        if a.get("p"):
            pol[a["s"]].append(a["v"])
            if a.get("lv") is not None:
                gaps[a["s"]].append(a["v"] - a["lv"])
    ll = ((core.get("V5") or {}).get("leadLag") or {}).get("outlets") or {}
    rows_b, set_b = defaultdict(int), defaultdict(int)
    for n in core.get("N", {}).values():
        for r in n.get("rows") or []:
            rows_b[r["s"]] += 1
            v = str(r.get("blame") or "").strip()
            set_b[r["s"]] += bool(v) and not UNSET.search(v)

    def rate(idx: dict, ids=None) -> tuple[dict, dict]:
        k, nn = defaultdict(int), defaultdict(int)
        for ev, c in idx.items():
            hit = cited(c, ids)
            for s in first.get(ev, {}):
                nn[s] += 1
                k[s] += s in hit
        return k, nn
    am, an = rate(im)
    aw, _ = rate(im, WORDING)
    ab, bn = rate(ib)
    outlets = []
    for s in sorted(set(an) | set(bn)):
        if an[s] < min_events:
            continue
        m = {"lean": lean.get(s), "cover": cover[s] / n_ev if n_ev else None,
             "loaded": sum(pol[s]) / len(pol[s]) if len(pol[s]) >= 20 else None,
             "gap": sum(gaps[s]) / len(gaps[s]) if len(gaps[s]) >= 20 else None,
             "first": ll.get(s, {}).get("firstShare"),
             "blame": set_b[s] / rows_b[s] if rows_b[s] >= 10 else None,
             "ai_media": am[s] / an[s], "ai_wording": aw[s] / an[s],
             "ai_behav": ab[s] / bn[s] if bn[s] >= min_events else None}
        outlets.append({"s": s, "bloc": _bloc(lean.get(s)), "n": an[s], "m": m})
    keys = [k for k, _, _ in MEASURES]
    matrix = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            pts = [(o["m"][a], o["m"][b]) for o in outlets if o["m"][a] is not None and o["m"][b] is not None]
            if len(pts) < 8:
                matrix.append({"a": a, "b": b, "n": len(pts), "rho": None, "p": None})
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            rho = spearman(xs, ys)
            matrix.append({"a": a, "b": b, "n": len(pts), "rho": rho, "p": perm_p(xs, ys, rho)})
    # Benjamini-Hochberg over the tested pairs, so 'significant' survives the many comparisons
    tested = sorted((c for c in matrix if c["p"] is not None), key=lambda c: c["p"])
    m_ = len(tested)
    q_prev = 1.0
    for rank, c in reversed(list(enumerate(tested, 1))):
        q_prev = min(q_prev, c["p"] * m_ / rank)
        c["q"] = q_prev
    return {"measures": [{"k": k, "label": l, "kind": kd} for k, l, kd in MEASURES], "outlets": outlets, "matrix": matrix}


def _bloc(lean):
    return None if lean is None else "left" if lean < 45 else "right" if lean > 55 else "mid"


def _cited(f: dict) -> set[str]:
    return {o for q in f.get("evidence", []) for o in q.get("o", [])}


def _live(ev: dict) -> list[dict]:
    return ev.get("supported", []) + ev.get("uncertain", [])


def cite_index(passes: dict) -> dict[str, dict[str, set[str]]]:
    """event -> card id -> outlets whose headline a live finding of that card quotes. Built once per pass."""
    idx: dict[str, dict[str, set[str]]] = {}
    for ev, x in passes.items():
        c: dict[str, set[str]] = defaultdict(set)
        for f in _live(x):
            c[f["id"]] |= _cited(f)
        idx[ev] = c
    return idx


def cited(idx_ev: dict[str, set[str]], ids=None) -> set[str]:
    return set().union(*(v for k, v in idx_ev.items() if ids is None or k in ids))


def _bloc_rate(idx: dict, first: dict, bloc_of: dict, ids=None) -> dict:
    """Per bloc: outlet-events where the outlet was quoted for the given cards / all outlet-events of the bloc."""
    cnt = {b: [0, 0] for b in ("left", "mid", "right")}
    for ev, c in idx.items():
        hit = cited(c, ids)
        for s in first.get(ev, {}):
            b = bloc_of.get(s)
            if b:
                cnt[b][1] += 1
                cnt[b][0] += s in hit
    out = {}
    for b, (k, n) in cnt.items():
        lo, hi = wilson(k, n)
        out[b] = {"k": k, "n": n, "rate": k / n if n else 0, "lo": lo, "hi": hi}
    return out


def _nn(o):
    """NaN -> None and floats rounded to 4 places (the site shows at most 2), recursively."""
    if isinstance(o, float):
        return None if math.isnan(o) else round(o, 4)
    if isinstance(o, dict):
        return {k: _nn(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_nn(v) for v in o]
    return o


def compute(core: dict, arts: dict[str, dict]) -> dict:
    lean = {s["s"]: s.get("lean") for s in core.get("S", [])}
    bloc_of = {s: _bloc(v) for s, v in lean.items()}
    E = {e["i"]: e for e in core["E"]}
    bgm = {x["event"]: x for x in core.get("BGM", {}).get("events", []) if x["status"] == "review_complete" and x["event"] in E}
    bg = {x["event"]: x for x in core.get("BG", {}).get("events", []) if x["status"] == "review_complete" and x["event"] in E}
    im, ib = cite_index(bgm), cite_index(bg)

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
    for ev in bgm:
        cw = cited(im[ev], WORDING)
        for s, a in first[ev].items():
            cov[s] += 1
            vs[s].append(a["v"])
            if s in cw:
                hit[s] += 1
                pos.append(a["v"])
            else:
                neg.append(a["v"])
    outlets = []
    for s in cov:
        if cov[s] < MIN_EVENTS:
            continue
        lo, hi = wilson(hit[s], cov[s])
        outlets.append({"s": s, "bloc": bloc_of.get(s), "n": cov[s], "k": hit[s], "rate": hit[s] / cov[s],
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
            lo, hi = wilson(k, n)
            blocs[b] = {"k": k, "n": n, "rate": k / n, "lo": lo, "hi": hi, "outlets": len(rs)}
    wording = {"outlets": outlets, "rho": rho, "blocs": blocs, "events": len(bgm),
               "headlines": {"cited": len(pos), "notCited": len(neg),
                             "vCited": sum(pos) / len(pos) if pos else None, "vNot": sum(neg) / len(neg) if neg else None,
                             "auc": auc(pos, neg), "aucLo": boots[7] if boots else None, "aucHi": boots[292] if boots else None}}

    # ---- heat: technique x bloc, per outlet-event so a bloc with more outlets is not favoured by its size
    names = {f["id"]: f["name"] for x in bgm.values() for f in _live(x)}
    heat = [{"id": t, "name": names[t], "events": sum(t in im[ev] for ev in bgm), **_bloc_rate(im, first, bloc_of, {t})}
            for t in sorted(names)]
    heat.sort(key=lambda r: -r["events"])
    if bg:  # the behavioural pass as one row, so its bloc reading stays on the site
        heat.append({"id": "_behavioural", "name": "Davranışsal yanlılıklar (tümü)", "events": sum(1 for ev in bg if ib[ev]),
                     **_bloc_rate(ib, first, bloc_of)})

    # ---- blame: Anlatı haritası 'sorumlu tutulan' vs AI responsibility-framing, per outlet-event
    nby = {n["ev"]: n for n in core.get("N", {}).values() if n.get("ev")}
    tab = {"both": 0, "rule": 0, "ai": 0, "neither": 0}
    events_both = 0
    for ev in bgm:
        n = nby.get(ev)
        if not n or not n.get("rows"):
            continue
        events_both += 1
        ai = im[ev].get("responsibility-framing", set())
        for r in n["rows"]:
            rule = bool(str(r.get("blame") or "").strip()) and not UNSET.search(str(r.get("blame")))
            tab["both" if rule and r["s"] in ai else "rule" if rule else "ai" if r["s"] in ai else "neither"] += 1
    blame = {**tab, "events": events_both, "kappa": kappa(tab["both"], tab["rule"], tab["ai"], tab["neither"])}

    # ---- where: findings per event (both passes) by context
    nf = {ev: len(_live(bgm[ev])) + (len(_live(bg[ev])) if ev in bg else 0) for ev in bgm}

    def group(key) -> list[dict]:
        g = defaultdict(list)
        for ev in bgm:
            for k in key(E[ev], ev) or []:
                g[k].append(nf[ev])
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
    prof = profile(core, arts, im, ib, first)
    return _nn({"wording": wording, "heat": heat, "blame": blame, "where": where, "profile": prof,
                "minEvents": MIN_EVENTS})


def load_articles(data: Path, core: dict) -> dict[str, dict]:
    packs = core["meta"]["packs"]
    out = {}
    for m in packs["months"]:
        a = _load(data / f"a-{m}.bin")
        for k, i in enumerate(a["i"]):
            out[i] = {"s": packs["sources"][a["s"][k]], "d": a["d"][k], "v": a["v"][k], "p": a["p"][k], "lv": a["lv"][k]}
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
