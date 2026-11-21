"""Single-source lens: who is compared (comparison group), which stories count (notices excluded),
and how each comparison outlet differs from the others on the same stories.

    python -m capraz_pipeline.lens --data <folder with core.bin and a-*.bin>   # writes data/reference/lens-82.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from .cluster import minutes, vectors
from .config import PARAMS, REPO
from .stats import bh_q, cmh_p, mh_rr
from .store import tr_lower

# Must equal PARAMS.noticeRules.keywords in site/js/turkish-layer.js (tests check it).
NOTICE_KEYWORDS = ["MAHKEMESİ", "HAKİMLİĞİ", "SATIŞ MEMURLUĞU", "İCRA DAİRESİ", "İCRA MÜDÜRLÜĞÜ", "BELEDİYE BAŞKANLIĞI",
                   "BELEDİYE BŞK", "BAŞKANLIĞI", "MÜDÜRLÜĞÜ", "İDARESİ", "ALIM İŞİ", "İHALE"]
NOTICE_EVENT_SHARE = 0.5          # PARAMS.ilanEventShare in turkish-layer.js
LENS_TYPES = {"print", "tv", "web", "online"}
MIN_MEDIAN = 20                   # complete feed: headlines per active day
MAX_DAY_SHARE = 0.10              # complete feed: active days at the outlet's own maximum
REASON_PART = "Yalnızca sezonun bir kısmında derlendi."
REASON_TYPE = "Kayıt defterinde genel haber kurumu olarak geçmiyor."

MEASURES = ("skip", "loaded", "harsher", "first")
FEED_MEASURES = {"skip", "first"}  # computed only for complete-feed lens outlets, against complete-feed lens outlets
LOADED_V = 25                     # loaded: headline score v >= 25 (political headlines only)
HARSHER_GAP = 15                  # harsher: v - lv >= 15 (political headlines with a lede)
FIRST_MINUTES = 60                # first to report: within 60 minutes of the earliest timed comparison headline
BARE_DATE = "00:00"               # a time of exactly 00:00 is a date without a time
MIN_STORIES = 20                  # a measure is counted only on >= 20 stories
CLIP = (0.25, 4.0)                # distance: RR clipped to this range
MIN_MEASURES = 3                  # distance needs >= 3 measures
STRONG_RR = 2.0                   # "systematically": RR >= 2 or <= 1/2 ...
STRONG_Q = 0.01                   # ... BH q < 0.01 over every outlet x measure on the whole season ...
MONTH_MIN_STORIES = 5             # ... and in every month with >= 5 stories ...
MONTH_RR = 1.5                    # ... the same direction with RR >= 1.5 or <= 1/1.5 ...
MIN_MONTHS = 2                    # ... in at least 2 such months
TOPIC_SLICES = 6                  # the most frequent tp codes among big stories
MAX_MISSED = 8
MONTH_NAMES = {"01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan", "05": "Mayıs", "06": "Haziran",
               "07": "Temmuz", "08": "Ağustos", "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık"}
OUT = REPO / "data" / "reference" / "lens-82.json"
GROUPS = REPO / "data" / "reference" / "lens-groups.json"
COLUMNS = ("i", "s", "d", "v", "p", "lv", "t", "nu")


def tr_upper(text: str) -> str:
    return text.replace("i", "İ").replace("ı", "I").upper()


def is_all_caps(t: str) -> bool:
    return t == tr_upper(t) and t != tr_lower(t)


def is_notice_article(a: dict) -> bool:
    t = a.get("t") or ""
    return bool(a.get("nu", 0) & 1) or (is_all_caps(t) and any(k in t for k in NOTICE_KEYWORDS))


def notice_events(core: dict, arts: dict) -> set[str]:
    out = set()
    for e in core["E"]:
        ids = e["a"]
        n = sum(1 for i in ids if i in arts and is_notice_article(arts[i]))
        if ids and n / len(ids) >= NOTICE_EVENT_SHARE:
            out.add(e["i"])
    return out


def days_active(arts: dict) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a in arts.values():
        out[a["s"]][a["d"][:10]] += 1
    return {s: dict(d) for s, d in out.items()}


def season_days(core: dict) -> list[str]:
    w = core["meta"]["window"]
    d, end = date.fromisoformat(w["start"][:10]), date.fromisoformat(w["end"][:10])
    return [(d + timedelta(n)).isoformat() for n in range((end - d).days + 1)]


def group(core: dict, arts: dict, groups: dict) -> dict[str, dict]:
    days = days_active(arts)
    n_days = len(season_days(core))
    excluded = groups.get("exclude", {})
    out = {}
    for s in core["S"]:
        slug = s["s"]
        share = len(days.get(slug, {})) / n_days if n_days else 0.0
        if slug in excluded:
            reason = excluded[slug]
        elif s.get("t") not in LENS_TYPES:
            reason = REASON_TYPE
        elif share < PARAMS.active_day_share:
            reason = REASON_PART
        else:
            reason = ""
        out[slug] = {"lens": not reason, "reason": reason, "active_share": share}
    return out


def feed_complete(counts: dict[str, int], n_days: int) -> tuple[bool, dict]:
    vals = list(counts.values())
    if not vals or not n_days:
        return False, {"active_share": 0.0, "median": 0.0, "at_max_share": 0.0}
    top = max(vals)
    st = {"active_share": len(vals) / n_days, "median": statistics.median(vals),
          "at_max_share": sum(1 for v in vals if v == top) / len(vals)}
    ok = st["active_share"] >= PARAMS.active_day_share and st["median"] >= MIN_MEDIAN and st["at_max_share"] < MAX_DAY_SHARE
    return ok, st


def big_stories(core: dict, arts: dict, group_out: dict, notices: set[str]) -> list[dict]:
    """Non-notice events covered by >= half of the comparison outlets that were active on the event's first day."""
    lens = {s for s, g in group_out.items() if g["lens"]}
    days = days_active(arts)
    out = []
    for e in core["E"]:
        if e["i"] in notices:
            continue
        day = e["f"][:10]
        active = sorted(s for s in lens if days.get(s, {}).get(day))
        have = {arts[i]["s"] for i in e["a"] if i in arts}
        covered = [s for s in active if s in have]
        if active and len(covered) / len(active) >= 0.5:
            out.append({"event": e["i"], "day": day, "active": active, "covered": covered})
    return out


def confirmed_skips(stories: list[dict], core: dict, arts: dict, outlets: list[str]) -> dict[str, set[str]]:
    """Outlet -> big events it skipped: no headline within 48 h of the event's first headline matches any event headline.

    The vectoriser is fit once on every headline in `arts`, so a result never depends on which outlets or stories are passed."""
    events = {e["i"]: e for e in core["E"]}
    window = 48 * 60
    by_outlet: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for aid, a in arts.items():
        if a["s"] in outlets:
            by_outlet[a["s"]].append((minutes(a["d"]), aid))
    for v in by_outlet.values():
        v.sort()
    stamps = {s: [m for m, _ in v] for s, v in by_outlet.items()}
    # (outlet, event, in-window headline ids): the outlet was active that day but has no article in the event.
    pairs = []
    for st in stories:
        e = events[st["event"]]
        t0 = minutes(e["f"])
        for s in outlets:
            if s in st["active"] and s not in st["covered"]:
                lo, hi = bisect_left(stamps.get(s, []), t0), bisect_right(stamps.get(s, []), t0 + window)
                pairs.append((s, e, [aid for _, aid in by_outlet.get(s, [])[lo:hi]]))
    out: dict[str, set[str]] = {s: set() for s in outlets}
    if not pairs:
        return out
    ids = list(arts)
    try:
        X = vectors([arts[i]["t"] for i in ids])
    except ValueError:  # empty vocabulary: nothing can be confirmed
        return out
    row = {aid: n for n, aid in enumerate(ids)}
    for s, e, near in pairs:
        own = [row[i] for i in e["a"] if i in row]
        if not own:
            continue
        if near and (X[[row[i] for i in near]] @ X[own].T).max() >= PARAMS.cluster_threshold:
            continue
        out[s].add(e["i"])
    return out


def _timed(a: dict) -> bool:
    return a["d"][11:16] != BARE_DATE


def _eligible(measure: str, a: dict) -> bool:
    if measure == "loaded":
        return bool(a["p"])
    if measure == "harsher":
        return bool(a["p"]) and a["lv"] is not None
    return _timed(a)  # first


def _stratum(measure: str, outlet: str, st: dict, arts: dict, others: list[str]) -> tuple[int, int, int, int] | None:
    """(outlet yes, 1, others yes, others eligible) for one story, or None when the outlet or every other is ineligible."""
    if measure == "skip":
        active = st.get("active") or ()
        if outlet not in active:
            return None
        skipped = st.get("skipped") or set()
        peers = [s for s in others if s in active]
        if not peers:
            return None
        return (int(outlet in skipped), 1, sum(1 for s in peers if s in skipped), len(peers))
    # "first" judges each outlet by its earliest real-timed headline in the story ("timed"); the rest by its first headline.
    first = st.get("timed", st["first"]) if measure == "first" else st["first"]
    if outlet not in first or not _eligible(measure, arts[first[outlet]]):
        return None
    peers = [arts[first[s]] for s in others if s in first and _eligible(measure, arts[first[s]])]
    if not peers:
        return None
    own = arts[first[outlet]]
    if measure == "loaded":
        yes = lambda a: a["v"] >= LOADED_V
    elif measure == "harsher":
        yes = lambda a: a["v"] - a["lv"] >= HARSHER_GAP
    else:  # first: reference = earliest timed headline of the outlet and the others that covered the story
        ref = datetime.fromisoformat(min([own["d"]] + [a["d"] for a in peers]))
        yes = lambda a: (datetime.fromisoformat(a["d"]) - ref).total_seconds() <= FIRST_MINUTES * 60
    return (int(yes(own)), 1, sum(1 for a in peers if yes(a)), len(peers))


def strata(measure: str, outlet: str, stories: list[dict], arts: dict, others: list[str]) -> list[tuple[int, int, int, int]]:
    """One stratum per story where the outlet and at least one of `others` are eligible for the measure."""
    out = [_stratum(measure, outlet, st, arts, others) for st in stories]
    return [x for x in out if x is not None]


def _rate(ss: list[tuple[int, int, int, int]]) -> dict:
    """Raw MH ratio and CMH p. rr 0 = the outlet never does it while others do; None = only it does, or nobody does (then none=True)."""
    rr, lo, hi = mh_rr(ss)
    if not any(b for _, _, b, _ in ss):
        rr, lo, hi = None, None, None
    none = not any(a or b for a, _, b, _ in ss)   # nobody does it: rr is undefined, but it is not "only this outlet"
    return {"n": len(ss), "rr": rr, "lo": lo, "hi": hi, "p": cmh_p(ss), "none": none}


def verdict(m: dict, months: dict[str, dict]) -> bool:
    """'Systematically': n >= 20, RR >= 2 or <= 1/2, q < 0.01, and every month with >= 5 stories (at least 2 of them)
    in the same direction with RR >= 1.5 or <= 1/1.5."""
    rr, q = m.get("rr"), m.get("q")
    if m["n"] < MIN_STORIES or rr is None or q is None or q >= STRONG_Q:
        return False
    if rr >= STRONG_RR:
        same = lambda x: x is not None and x >= MONTH_RR
    elif rr <= 1 / STRONG_RR:
        same = lambda x: x is not None and x <= 1 / MONTH_RR
    else:
        return False
    counted = [x for x in months.values() if x["n"] >= MONTH_MIN_STORIES]
    return len(counted) >= MIN_MONTHS and all(same(x["rr"]) for x in counted)


def distance(measures: dict[str, dict]) -> float | None:
    """2^(mean |log2 RR|) over the measures with >= 20 stories and a defined RR, RR clipped to [1/4, 4]; needs 3."""
    logs = [abs(math.log2(min(max(m["rr"], CLIP[0]), CLIP[1]))) for m in measures.values()
            if m["n"] >= MIN_STORIES and m["rr"] is not None]
    return 2 ** (sum(logs) / len(logs)) if len(logs) >= MIN_MEASURES else None


def outlet_lens(slug: str, measures: list[str], others: dict[str, list[str]], stories: list[dict], arts: dict,
                slices: dict[str, set[str]], months: list[str]) -> tuple[dict, dict]:
    """Per slice the measures with >= 20 stories, plus per measure the season's month rates for the verdict."""
    out = {k: {"measures": {}} for k in slices}
    month_rates = {}
    for m in measures:
        by_event = {st["event"]: x for st in stories if (x := _stratum(m, slug, st, arts, others[m])) is not None}
        month_rates[m] = {}
        for k, events in slices.items():
            ss = [x for e, x in by_event.items() if e in events]
            if k in months:
                month_rates[m][k] = {"n": len(ss), "rr": _rate(ss)["rr"] if ss else None}
            if len(ss) >= MIN_STORIES:
                out[k]["measures"][m] = _rate(ss)
    return out, month_rates


def compute(core: dict, arts: dict, groups: dict) -> dict:
    g = group(core, arts, groups)
    lens = sorted(s for s, x in g.items() if x["lens"])
    days = days_active(arts)
    n_days = len(season_days(core))
    feeds = {}
    for slug in g:
        ok, st = feed_complete(days.get(slug, {}), n_days)
        feeds[slug] = {"complete": ok, **st}
    complete = [s for s in lens if feeds[s]["complete"]]
    notices = notice_events(core, arts)
    big = big_stories(core, arts, g, notices)
    skips = confirmed_skips(big, core, arts, complete)
    big_by = {b["event"]: b for b in big}
    events = {e["i"]: e for e in core["E"]}

    stories = []
    for e in core["E"]:
        if e["i"] in notices:
            continue
        first: dict[str, str] = {}
        timed: dict[str, str] = {}
        for aid in sorted((i for i in e["a"] if i in arts), key=lambda i: (arts[i]["d"], i)):
            first.setdefault(arts[aid]["s"], aid)
            if _timed(arts[aid]):
                timed.setdefault(arts[aid]["s"], aid)
        b = big_by.get(e["i"])
        stories.append({"event": e["i"], "month": e["f"][:7], "tp": e.get("tp") or [], "first": first, "timed": timed,
                        "active": b["active"] if b else [],
                        "skipped": {s for s in complete if e["i"] in skips[s]} if b else set()})

    months = sorted({d[:7] for d in season_days(core)})
    tp_names = {t["k"]: t["n"] for t in core.get("TP", [])}
    top = Counter(c for st in stories if st["active"] for c in st["tp"])
    topics = [c for c, _ in sorted(top.items(), key=lambda x: (-x[1], x[0]))[:TOPIC_SLICES]]
    slices = [{"k": "all", "l": "Bütün sezon"}] + [{"k": m, "l": MONTH_NAMES[m[5:]]} for m in months] + \
             [{"k": f"tp:{c}", "l": tp_names.get(c, c)} for c in topics]
    members = {"all": {st["event"] for st in stories}}
    members |= {m: {st["event"] for st in stories if st["month"] == m} for m in months}
    members |= {f"tp:{c}": {st["event"] for st in stories if c in st["tp"]} for c in topics}

    outlets, month_rates = {}, {}
    for slug, x in g.items():
        o = {"lens": x["lens"], "reason": x["reason"], "feed": feeds[slug], "slices": {}, "missed": []}
        if x["lens"]:
            # skip and first only for complete feeds, against the other complete feeds: a partial or capped feed
            # distorts which stories we collected from it and when, not what the newsroom published.
            ms = [m for m in MEASURES if m not in FEED_MEASURES or slug in complete]
            others = {m: [s for s in (complete if m in FEED_MEASURES else lens) if s != slug] for m in ms}
            o["slices"], month_rates[slug] = outlet_lens(slug, ms, others, stories, arts, members, months)
            if slug in complete:
                o["missed"] = sorted(skips[slug], key=lambda i: (-len(events[i]["s"]), events[i]["f"], i))[:MAX_MISSED]
        outlets[slug] = o

    # BH over every outlet x measure on the whole season; an untestable p (zero variance) enters as 1 and gets no q.
    tested = [(s, m) for s in lens for m in outlets[s]["slices"]["all"]["measures"]]
    ps = [outlets[s]["slices"]["all"]["measures"][m]["p"] for s, m in tested]
    qs = bh_q([1.0 if p is None else p for p in ps])
    for (s, m), q in zip(tested, qs):
        x = outlets[s]["slices"]["all"]["measures"][m]
        x["q"] = None if x["p"] is None else q
        x["strong"] = verdict(x, month_rates[s][m])
    for s in lens:
        for v in outlets[s]["slices"].values():
            v["distance"] = distance(v["measures"])

    params = {"measures": list(MEASURES), "loaded_v": LOADED_V, "harsher_gap": HARSHER_GAP, "first_minutes": FIRST_MINUTES,
              "min_stories": MIN_STORIES, "clip": list(CLIP), "min_measures": MIN_MEASURES, "strong_rr": STRONG_RR,
              "strong_q": STRONG_Q, "month_min_stories": MONTH_MIN_STORIES, "month_rr": MONTH_RR, "min_months": MIN_MONTHS,
              "active_day_share": PARAMS.active_day_share, "big_share": 0.5, "feed_median": MIN_MEDIAN,
              "feed_max_share": MAX_DAY_SHARE, "skip_cosine": PARAMS.cluster_threshold, "skip_hours": 48,
              "season_days": n_days, "stories": len(stories), "big_stories": len(big), "notice_stories": len(notices)}
    return {"params": params, "slices": slices, "outlets": outlets}


def _load_checked(data: Path) -> tuple[dict, dict]:
    from .aix import _load, load_articles
    path = data / "core.bin"
    if not path.exists():
        raise SystemExit(f"lens: missing {path}")
    core = _load(path)
    for m in core["meta"]["packs"]["months"]:
        f = data / f"a-{m}.bin"
        if not f.exists():
            raise SystemExit(f"lens: missing {f}")
        missing = [c for c in COLUMNS if c not in _load(f)]
        if missing:
            raise SystemExit(f"lens: {f} has no column {', '.join(missing)}")
    return core, load_articles(data, core)


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.lens")
    p.add_argument("--data", type=Path, required=True, help="folder with core.bin and a-*.bin")
    a = p.parse_args()
    t0 = time.monotonic()
    core, arts = _load_checked(a.data)
    if not GROUPS.exists():
        raise SystemExit(f"lens: missing {GROUPS}")
    res = compute(core, arts, json.loads(GROUPS.read_text(encoding="utf-8")))
    text = json.dumps(res, ensure_ascii=False, allow_nan=False)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, OUT)
    for slug, o in sorted(res["outlets"].items()):
        if o["lens"]:
            al, f = o["slices"]["all"], o["feed"]
            d = "-" if al["distance"] is None else f"{al['distance']:.3f}"
            print(f"{slug:16} distance {d:>6}  measures {len(al['measures'])}  feed {'complete' if f['complete'] else 'partial ':8}"
                  f" active {f['active_share']:.2f} median {f['median']:g} at-max {f['at_max_share']:.2f}")
    for sl in res["slices"]:
        n = sum(1 for o in res["outlets"].values() if o["lens"] and o["slices"][sl["k"]]["distance"] is not None)
        print(f"slice {sl['k']:16} {sl['l']:24} outlets with a distance: {n}")
    print(f"wrote {OUT} ({len(text)} bytes) in {time.monotonic() - t0:.1f}s")


if __name__ == "__main__":
    main()
