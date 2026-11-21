"""Single-source lens: who is compared (comparison group), which stories count (notices excluded)."""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, timedelta

from .config import PARAMS
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
