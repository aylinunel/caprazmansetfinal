"""9 "what is new": the 8.2 build against the 9 build, from the two core.bin files.

    python -m capraz_pipeline.whatsnew9 --old <8.2 core.bin> --new <9 core.bin>   -> data/reference/whatsnew-9.json

Same card shape as whatsnew.py (8.1), but every sentence follows the numbers: the verb comes from the sign of the
change, never from the previous release. narratives.merge ships it as core key W9.
"""
from __future__ import annotations

import argparse
import gzip
import json
from datetime import date, timedelta
from pathlib import Path

from .config import REPO

OUT = REPO / "data" / "reference" / "whatsnew-9.json"
COLS = ["8.2", "9"]


def _load(p: Path) -> dict:
    return json.loads(gzip.decompress(p.read_bytes()))


def _n(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def _d(v: float, k: int = 2) -> str:
    return f"{v:.{k}f}".replace(".", ",")


def _move(a: float, b: float, eps: float) -> tuple[str, str]:
    """(verb, tag) for a change from a to b; within eps counts as unchanged."""
    if abs(b - a) <= eps:
        return "neredeyse aynı kaldı", "sürüyor"
    return ("arttı" if b > a else "azaldı"), "değişti"


def _sig(p: float) -> str:
    return "anlamlı" if p < 0.05 else "anlamlı değil"


def build(old: dict, new: dict, bg_new: int = 0, bg_changed: int = 0) -> dict:
    om, nm = old["meta"], new["meta"]
    oc, nc = om["counts"], nm["counts"]
    new_from = (date.fromisoformat(om["v2"]["target"]["end"]) + timedelta(days=1)).isoformat()
    new_ev = [e for e in new["E"] if e["f"][:10] >= new_from]
    names = {r["s"]: r["n"] for r in new["S"]}
    names.update(new.get("SN", {}))
    nm_ = lambda s: names.get(s, s)
    added = sorted(set(nm["sources"]) - set(om["sources"]))
    out = []

    out.append({"id": "veri", "tag": "yeni", "title": "Bir hafta daha veri",
        "claim": f"Pencere {om['v2']['target']['end']} yerine {nm['v2']['target']['end']} tarihinde bitiyor. Başlık {_n(oc['articles'])} → {_n(nc['articles'])}, "
                 f"olay {_n(oc['events'])} → {_n(nc['events'])}, kurum {len(om['sources'])} → {len(nm['sources'])}.",
        "rows": [["Başlık", _n(oc["articles"]), _n(nc["articles"])], ["Olay", _n(oc["events"]), _n(nc["events"])],
                 ["Kurum (veri alınan)", str(len(om["sources"])), str(len(nm["sources"]))],
                 ["Dönem", f"{om['v2']['target']['start']} – {om['v2']['target']['end']}", f"{nm['v2']['target']['start']} – {nm['v2']['target']['end']}"]],
        "note": f"{_n(len(new_ev))} olay {new_from} ve sonrasında başladı." + (f" İlk kez dahil olan kurumlar: {', '.join(nm_(s) for s in added)}." if added else "")})

    for key, cid, title, note in (
            (("V5", "similarity"), "benzerlik", "Başlık dili benzerliği ve yerleşim", "Benzer yerleşimdeki kurumların benzer sözcükler seçtiğini ölçer; niyet göstermez."),
            (("ADV", "agenda"), "gundem", "Gündem seçimi ve yerleşim", "Hangi olayların haberleştirildiğinin yerleşimle ilişkisini ölçer.")):
        a, b = old[key[0]][key[1]], new[key[0]][key[1]]
        verb, tag = _move(a["mantel_r"], b["mantel_r"], 0.02)
        out.append({"id": cid, "tag": tag, "title": title,
            "claim": f"Mantel r {_d(a['mantel_r'])} → {_d(b['mantel_r'])}: ilişki {verb}. 9’daki sonuç {_sig(b['mantel_p'])} (p {_d(b['mantel_p'], 3)}).",
            "rows": [["Mantel r", _d(a["mantel_r"], 3), _d(b["mantel_r"], 3)], ["p", _d(a["mantel_p"], 3), _d(b["mantel_p"], 3)]], "note": note})

    oa, na = old["ADV"]["pca"], new["ADV"]["pca"]
    verb, tag = _move(oa["rho1"], na["rho1"], 0.02)
    out.append({"id": "uslup", "tag": tag, "title": "Yazım üslubu ve yerleşim",
        "claim": f"Üslup eksenindeki Spearman ρ {_d(oa['rho1'])} → {_d(na['rho1'])}: bağ {verb}. 9’daki sonuç {_sig(na['p1'])} (p {_d(na['p1'], 3)}).",
        "rows": [["ρ (1. eksen)", _d(oa["rho1"], 3), _d(na["rho1"], 3)], ["p (1. eksen)", _d(oa["p1"], 3), _d(na["p1"], 3)]], "note": ""})

    bo, bn = sum(1 for e in old["E"] if e.get("bs")), sum(1 for e in new["E"] if e.get("bs"))
    po, pn = 100 * bo / len(old["E"]), 100 * bn / len(new["E"])
    verb, tag = _move(po, pn, 0.1)
    out.append({"id": "kornokta", "tag": tag, "title": "Kör nokta olayları",
        "claim": f"Bir tarafın belirgin biçimde az haberleştirdiği olay {bo} → {bn}; bütün olayların içindeki payı %{_d(po, 1)} → %{_d(pn, 1)} ({verb}).",
        "rows": [["Kör nokta olayı", str(bo), str(bn)], ["Pay", f"%{_d(po, 1)}", f"%{_d(pn, 1)}"],
                 [f"{new_from} sonrası kör nokta", "—", str(sum(1 for e in new_ev if e.get("bs")))]], "note": ""})

    comp = sorted(s for s in old["OM"] if s in new["OM"])
    mv = sorted(comp, key=lambda s: new["OM"][s]["load"] - old["OM"][s]["load"])
    diff = sum(abs(new["OM"][s]["load"] - old["OM"][s]["load"]) for s in comp) / len(comp)
    out.append({"id": "yuk", "tag": "sürüyor" if diff < 1 else "değişti", "title": "Yüklü dil",
        "claim": f"İki sürümde de bulunan {len(comp)} kurumun yük ortalaması kurum başına ortalama {_d(diff)} puan değişti.",
        "rows": [[nm_(s), _d(old["OM"][s]["load"], 1), _d(new["OM"][s]["load"], 1)] for s in (mv[:2] + mv[-3:])],
        "note": "Tabloda en çok düşen iki ve en çok yükselen üç kurum."})

    bg, bgm = new.get("BG", {}).get("summary", {}), new.get("BGM", {}).get("summary", {})
    obg = old.get("BG", {}).get("summary", {})
    out.append({"id": "yz", "tag": "değişti", "title": "AI incelemesi yeni olaylarla güncellendi",
        "claim": f"En çok kurumun haberleştirdiği {bg.get('planned', 0)} olay yeniden seçildi: {bg_new} olay listeye yeni girdi, {bg_changed} olayın başlıkları ya da bağlamı değiştiği için yeniden "
                 f"incelendi, geri kalanların 8.2 incelemesi aynen korundu. Davranışsal bulgu {obg.get('uncertain', 0) + obg.get('supported', 0)} → {bg.get('uncertain', 0) + bg.get('supported', 0)}.",
        "rows": [["Davranışsal bulgu", str(obg.get("uncertain", 0) + obg.get("supported", 0)), str(bg.get("uncertain", 0) + bg.get("supported", 0))],
                 ["Doğrulanmış alıntı", _n(obg.get("quotesVerified", 0)), _n(bg.get("quotesVerified", 0))],
                 ["Medya tekniği bulgusu (canlı)", str(old.get("BGM", {}).get("summary", {}).get("uncertain", 0) + old.get("BGM", {}).get("summary", {}).get("supported", 0)),
                  str(bgm.get("uncertain", 0) + bgm.get("supported", 0))]],
        "note": "Her olay ayrı seçici, savunucu ve kuşkucu ajanlarca incelendi; bulgular aynı biçimde, AI imzalı gösterilir."})

    nw = [w for w in new.get("NW", []) if w["k"] not in {w["k"] for w in old.get("NW", [])}]
    if nw:
        out.append({"id": "anlati", "tag": "yeni", "title": "Anlatı haritasına yeni hafta",
            "claim": "Anlatı haritası " + ", ".join(w["l"] for w in nw) + " haftasıyla genişledi; " + str(sum(len(w["keys"]) for w in nw)) + " olay yapay zekâyla kodlandı (YZ).",
            "rows": [], "note": "Kodlama kuralları önceki haftalarla aynıdır; insan kodlayıcı denetiminden geçmedi."})

    top_ev = sorted(new_ev, key=lambda e: (-len(e["s"]), -e["n"]))[:8]
    if top_ev:
        out.append({"id": "olaylar", "tag": "yeni", "title": "Yeni haftanın en çok kurumca haberleştirilen olayları",
            "claim": f"Uzayan pencerede {_n(len(new_ev))} olay başladı; en geniş yankı bulan: {top_ev[0]['t']} ({len(top_ev[0]['s'])} kurum).",
            "rows": [[e["t"], str(len(e["s"])), e["i"]] for e in top_ev], "events": True, "note": "Her satır olay sayfasına bağlanır."})

    out.append({"id": "sinir", "tag": "uyarı", "title": "Sınırlar", "claim": "9’un yeni bulguları şu sınırlarla okunmalı.",
        "rows": [["Son gün", f"{nm['v2']['target']['end']} sonrası henüz eksik toplandığı için dışarıda", ""],
                 ["Anlatı haritası", "yeni hafta yapay zekâyla kodlandı (YZ)", ""],
                 ["AI incelemesi", "yalnızca en çok kurumun haberleştirdiği olaylar incelenir", ""]], "note": ""})
    for f in out:
        f["cols"] = COLS
    return {"version": "9", "from": new_from, "findings": out}


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.whatsnew9")
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--bg-new", type=int, default=0)
    p.add_argument("--bg-changed", type=int, default=0)
    p.add_argument("--out", type=Path, default=OUT)
    a = p.parse_args()
    r = build(_load(a.old), _load(a.new), a.bg_new, a.bg_changed)
    a.out.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(r["findings"]), "findings ->", a.out)
